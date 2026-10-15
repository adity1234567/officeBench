"""Re-translate the OfficeBench task instructions into Bangla following
bangla_translation_guidelines.txt (names in Latin script, literals copied verbatim, ASCII digits).

Each translation is checked automatically; on a rule violation the model gets the list of
problems and retries (up to 3 attempts). Progress is kept in analysis/bn_tasks_v2.json so the
job is resumable. At the end the task entries in analysis/bn_cache.json are overwritten
(the previous cache is backed up once to analysis/bn_cache.before_v2.json) and a report is
written to analysis/bn_tasks_v2_report.txt.

    python analysis/retranslate_tasks_bn.py [--workers 4] [--limit N]
"""
import argparse, glob, json, os, re, shutil, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from utils.llm import load_env_file
from openai import OpenAI

ENV = load_env_file()
CLIENT = OpenAI(base_url=ENV.get('base_url', 'https://ollama.com/v1'), api_key=ENV.get('api_key', ''))
MODEL = ENV.get('model', 'gemma4:31b')
CACHE_PATH = 'analysis/bn_cache.json'
BACKUP_PATH = 'analysis/bn_cache.before_v2.json'
PROGRESS_PATH = 'analysis/bn_tasks_v2.json'
REPORT_PATH = 'analysis/bn_tasks_v2_report.txt'

# person names that occur in the task instructions (must stay in Latin script)
NAMES = ['Bob', 'Tom', 'Alice', 'Bill', 'Jane', 'Doe', 'Carol', 'Dan', 'Rena', 'Anna',
         'Xihozun', 'Cixarim', 'Dean']
# Bengali-script spellings of those names that must not appear (no short forms such as ডিন,
# জেন, আনা: they are prefixes of ordinary words like ডিনার, জেনারেট, আনা)
NAME_BN = ['বব', 'টম', 'অ্যালিস', 'এলিস', 'ক্যারল', 'ক্যারোল', 'ড্যান', 'রেনা', 'অ্যানা']

SYS = """You translate task instructions for an office-automation AI agent from English into Bangla (Bengali). The agent must be able to do exactly the same task, and an automatic grader will check its work, so follow these rules strictly:

1. Person names stay in Latin script exactly as written (Bob, Alice, Tom, Jane Doe, Carol, Anna, Rena). Never write them in Bangla script (not বব, অ্যালিস, টম). Attach Bangla case endings with a hyphen: Bob-এর, Alice-কে, Tom-এর.
2. Copy these EXACTLY, character for character, in Latin script: file names and paths (score.xlsx, Bill_course_list.xlsx), email addresses, URLs, app and format names (Excel, Word, PDF, OCR, DOCX), course codes and IDs (CS161, Math 151), and anything inside quotes ("..." or '...'). Never translate text inside quotes. Never fix typos in file names.
3. Numbers, dates and times: write every number with ASCII digits 0-9 exactly as in the English (5/18/2024, 7:00, 3.9, 100). Never use Bengali digits (০১২৩৪৫৬৭৮৯). Keep the same date format. a.m./p.m. may become সকাল/দুপুর/বিকেল/সন্ধ্যা/রাত, but the digits stay ASCII.
4. Answer options the user asks for (for example "Yes or no?") stay in English.
5. Do not add, remove or clarify information; keep any ambiguity of the English. Do not imply that a file already exists when the task asks to create it.
6. Write natural Bangla as a polite request (করুন form), using common office loanwords (ইমেইল, ফাইল, ক্যালেন্ডার, মিটিং, ইভেন্ট).

Output ONLY the Bangla translation, nothing else."""

SHOTS = [
    ("remind Bob that he has a dinner at 5/18/2024 7:00 p.m",
     "Bob-কে মনে করিয়ে দিন যে 5/18/2024 সন্ধ্যা 7:00 টায় তার একটি ডিনার আছে।"),
    ("Extract Bill's previous courses from Bill_course_list.xlsx, and put the course in classes_taken.docx.",
     "Bill_course_list.xlsx থেকে Bill-এর আগের কোর্সগুলো বের করুন, এবং কোর্সগুলো classes_taken.docx-এ লিখুন।"),
    ("Check the emails, and let me know if my rent is due. Yes or no?",
     "ইমেইলগুলো দেখুন, এবং আমাকে জানান আমার ভাড়া বাকি আছে কি না। Yes or no?"),
]

FILE_RE = re.compile(r'[\w\-./]*\w\.(?:xlsx|xls|docx|doc|pdf|csv|txt|eml|jpg|jpeg|png|ics|json)\b', re.I)
EMAIL_RE = re.compile(r'[\w.+\-]+@[\w\-]+\.[\w.\-]*\w')
URL_RE = re.compile(r'https?://\S+')
QUOTE_RE = re.compile(r'"([^"]+)"|(?<!\w)\'([^\']+)\'(?!\w)')
BN_DIGIT = re.compile('[০-৯]')
BN_TO_ASCII = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')


def check(en, bn):
    """Return the list of guideline violations of a Bangla translation."""
    probs = []
    if not re.search('[ঀ-৿]', bn):
        probs.append('the output is not in Bangla')
    if BN_DIGIT.search(bn):
        probs.append('uses Bengali digits; write all numbers with ASCII digits 0-9')
    missing_nums = [n for n in set(re.findall(r'\d+', en)) if n not in re.findall(r'\d+', bn)]
    if missing_nums:
        probs.append('numbers missing or changed: ' + ', '.join(sorted(missing_nums)))
    for n in NAMES:
        if re.search(r'\b' + n + r'\b', en) and not re.search(n + r'(?![a-z])', bn):
            probs.append(f'person name "{n}" must stay in Latin script')
    for w in NAME_BN:
        if re.search('(?<![ঀ-৿])' + w, bn) and any(re.search(r'\b' + n + r'\b', en) for n in NAMES):
            probs.append(f'name written in Bangla script ("{w}"); keep it in Latin script')
            break
    toks = FILE_RE.findall(en) + EMAIL_RE.findall(en) + URL_RE.findall(en)
    toks += [a or b for a, b in QUOTE_RE.findall(en)]
    for t in toks:
        t = t.rstrip('.,')
        if t and t not in bn:
            probs.append(f'must be copied exactly: {t}')
    return probs


def call(messages):
    for attempt in range(5):
        try:
            r = CLIENT.chat.completions.create(model=MODEL, temperature=0, messages=messages)
            return (r.choices[0].message.content or '').strip()
        except Exception as e:
            if '429' in str(e):
                raise
            time.sleep(4 * (attempt + 1))
    return ''


def translate(en):
    msgs = [{'role': 'system', 'content': SYS}]
    for e, b in SHOTS:
        msgs += [{'role': 'user', 'content': e}, {'role': 'assistant', 'content': b}]
    msgs.append({'role': 'user', 'content': en})
    best = None
    for attempt in range(3):
        bn = call(msgs)
        probs = check(en, bn)
        if best is None or len(probs) < len(best[1]):
            best = (bn, probs, attempt + 1)
        if not probs:
            break
        msgs += [{'role': 'assistant', 'content': bn},
                 {'role': 'user', 'content': 'Your translation breaks these rules:\n- ' + '\n- '.join(probs)
                  + '\nFix them and output ONLY the corrected Bangla translation.'}]
    bn, probs, tries = best
    fixed = False
    if BN_DIGIT.search(bn):  # mechanical, meaning-preserving fallback
        bn = bn.translate(BN_TO_ASCII); fixed = True
        probs = check(en, bn)
    return {'bn': bn, 'problems': probs, 'attempts': tries, 'digits_autofixed': fixed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    tasks = sorted({json.load(open(f, encoding='utf-8')).get('task', '').strip()
                    for f in glob.glob('tasks/*/subtasks/*.json')} - {''})
    done = json.load(open(PROGRESS_PATH, encoding='utf-8')) if os.path.exists(PROGRESS_PATH) else {}
    todo = [t for t in tasks if t not in done]
    if args.limit:
        todo = todo[:args.limit]
    print(f'{len(tasks)} tasks, {len(done)} done, {len(todo)} to translate', flush=True)

    lock = threading.Lock()
    stop = [False]

    def work(en):
        if stop[0]:
            return
        try:
            res = translate(en)
        except Exception as e:
            print(f'  [429] usage limit hit: {e}'.splitlines()[0], flush=True)
            stop[0] = True
            return
        with lock:
            done[en] = res
            json.dump(done, open(PROGRESS_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            flag = 'OK ' if not res['problems'] else 'ISSUE'
            print(f'[{len(done)}/{len(tasks)}] {flag} ({res["attempts"]} try) {en[:60]}', flush=True)

    with ThreadPoolExecutor(args.workers) as ex:
        for _ in as_completed([ex.submit(work, t) for t in todo]):
            pass

    if len(done) < len(tasks):
        print(f'stopped with {len(done)}/{len(tasks)} done; rerun to resume. bn_cache.json not touched.')
        sys.exit(2)

    # merge into the cache used by agent_interact.py (--lang bn) and translate_bn.py
    if not os.path.exists(BACKUP_PATH):
        shutil.copyfile(CACHE_PATH, BACKUP_PATH)
    cache = json.load(open(CACHE_PATH, encoding='utf-8'))
    old = json.load(open(BACKUP_PATH, encoding='utf-8'))
    for en in tasks:
        cache[en] = done[en]['bn']
    json.dump(cache, open(CACHE_PATH, 'w', encoding='utf-8'), ensure_ascii=False)

    issues = {en: r for en, r in done.items() if r['problems']}
    changed = sum(1 for en in tasks if old.get(en) != done[en]['bn'])
    L = [f'Re-translated {len(tasks)} task instructions with {MODEL} (guidelines v2).',
         f'Changed vs previous cache: {changed}',
         f'Passed all automatic checks: {len(tasks) - len(issues)}',
         f'Still with issues: {len(issues)}',
         f'Bengali digits auto-converted to ASCII: {sum(r["digits_autofixed"] for r in done.values())}',
         f'Needed a retry: {sum(r["attempts"] > 1 for r in done.values())}', '']
    for en, r in issues.items():
        L += ['EN: ' + en, 'BN: ' + r['bn'], 'ISSUES: ' + '; '.join(r['problems']), '']
    open(REPORT_PATH, 'w', encoding='utf-8').write('\n'.join(L))
    print('\n'.join(L[:7]))
    print(f'report: {REPORT_PATH}; old cache backed up at {BACKUP_PATH}')


if __name__ == '__main__':
    main()
