"""Render each OfficeBench task's trace in Bangla (trace_bn.txt).

Per task: system prompt, user input (task), model thinking, and output are translated to
Bangla using the local gemma4:31b (Ollama). Tool schema and JSON commands stay in English
(they are API identifiers the model must emit verbatim) with a one-line Bangla gloss.

English->Bangla translations are cached on disk (analysis/bn_cache.json) so the job is
resumable and repeated strings (system prompt, instructions, stock messages) are translated
only once.

    python analysis/translate_bn.py [--tag gemma4_31b_think] [--limit N] [task_id/sub_id ...]
"""
import glob, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from utils.llm import load_env_file
from history_to_trace import split_thought
from openai import OpenAI

ENV = load_env_file()
CLIENT = OpenAI(base_url=ENV.get('base_url', 'https://ollama.com/v1'), api_key=ENV.get('api_key', ''))
MODEL = ENV.get('model', 'gemma4:31b')
CACHE_PATH = os.path.join(ROOT, 'analysis', 'bn_cache.json')
CACHE = json.load(open(CACHE_PATH, encoding='utf-8')) if os.path.exists(CACHE_PATH) else {}
_dirty = [0]

TR_SYS = ("You are a professional English-to-Bangla translator. Translate the user's English "
          "text into natural, fluent Bangla (Bengali). Keep JSON, code, file names, numbers, "
          "email addresses and technical identifiers EXACTLY as they are. Do not add notes or "
          "explanations. Output ONLY the Bangla translation.")


def save_cache():
    json.dump(CACHE, open(CACHE_PATH, 'w', encoding='utf-8'), ensure_ascii=False)
    _dirty[0] = 0


def translate(text):
    text = (text or '').strip()
    if not text:
        return ''
    if text in CACHE:
        return CACHE[text]
    for attempt in range(4):
        try:
            r = CLIENT.chat.completions.create(
                model=MODEL, temperature=0,
                messages=[{'role': 'system', 'content': TR_SYS},
                          {'role': 'user', 'content': text}])
            bn = (r.choices[0].message.content or '').strip()
            if bn:
                CACHE[text] = bn
                _dirty[0] += 1
                if _dirty[0] >= 20:
                    save_cache()
                return bn
        except Exception as e:
            msg = str(e)
            if '429' in msg:
                print('  [429] usage limit hit; saving cache and stopping.', flush=True)
                save_cache()
                sys.exit(2)
            time.sleep(4 * (attempt + 1))
    return '[অনুবাদ ব্যর্থ] ' + text


# --- Bangla gloss for each action (structure stays English, this explains what it does) ---
def gloss(a):
    if not isinstance(a, dict):
        return 'অজানা/ত্রুটিপূর্ণ action'
    act = a.get('action'); g = a.get
    tmpl = {
        'switch_app': lambda: f"{g('target_app')} অ্যাপে স্যুইচ করা হচ্ছে",
        'finish_task': lambda: f"টাস্ক শেষ করা হচ্ছে (উত্তর: {g('answer')})",
        'got_stuck': lambda: "এজেন্ট আটকে গেছে — একই action বারবার করায় থেমে গেছে",
        'command': lambda: f"শেল কমান্ড চালানো হচ্ছে: {g('command')}",
        'create_event': lambda: f"ক্যালেন্ডারে ইভেন্ট যোগ: '{g('summary')}' ({g('time_start')} – {g('time_end')})",
        'delete_event': lambda: f"ক্যালেন্ডার থেকে ইভেন্ট মুছে ফেলা: '{g('summary')}'",
        'list_events': lambda: "ক্যালেন্ডারের ইভেন্ট তালিকা দেখা হচ্ছে",
        'read_file': lambda: f"ফাইল পড়া হচ্ছে: {g('file_path') or g('filename')}",
        'set_cell': lambda: f"সেল (সারি {g('row_idx')}, কলাম {g('column_idx')}) = '{g('value')}' বসানো হচ্ছে ({g('file_path')})",
        'delete_cell': lambda: f"সেল (সারি {g('row_idx')}, কলাম {g('column_idx')}) মুছে ফেলা হচ্ছে ({g('file_path')})",
        'create_new_file': lambda: f"নতুন ফাইল তৈরি: {g('file_path')}",
        'write_to_file': lambda: f"ফাইলে লেখা হচ্ছে: {g('file_path')}",
        'convert_to_pdf': lambda: f"PDF-এ রূপান্তর: {g('file_path')}",
        'convert_to_image': lambda: f"PDF থেকে ছবিতে রূপান্তর: {g('file_path')}",
        'convert_to_word': lambda: f"PDF থেকে Word-এ রূপান্তর: {g('file_path')}",
        'recognize_file': lambda: f"ছবি থেকে টেক্সট শনাক্ত (OCR): {g('file_path')}",
        'send_email': lambda: f"ইমেইল পাঠানো হচ্ছে — প্রাপক: {g('recipient')}, বিষয়: {g('subject')}",
        'list_emails': lambda: "ইমেইল তালিকা দেখা হচ্ছে",
        'read_email': lambda: "ইমেইল পড়া হচ্ছে",
        'complete_text': lambda: "LLM-কে প্রশ্ন/prompt পাঠানো হচ্ছে",
    }
    try:
        return tmpl[act]() if act in tmpl else f"'{act}' action চালানো হচ্ছে"
    except Exception:
        return f"'{act}' action চালানো হচ্ছে"


# generic (parameter-free) Bangla description of each tool for the schema section
SCHEMA_GLOSS = {
    ('calendar', 'create_event'): "ব্যবহারকারীর ক্যালেন্ডারে নতুন ইভেন্ট যোগ করে",
    ('calendar', 'delete_event'): "summary দিয়ে ক্যালেন্ডার থেকে ইভেন্ট মুছে ফেলে",
    ('calendar', 'list_events'): "ব্যবহারকারীর ক্যালেন্ডারের সব ইভেন্ট দেখায়",
    ('excel', 'read_file'): "এক্সেল ফাইলের বিষয়বস্তু পড়ে",
    ('excel', 'set_cell'): "এক্সেল ফাইলের একটি সেলে টেক্সট লেখে (index ১ থেকে শুরু)",
    ('excel', 'delete_cell'): "এক্সেল ফাইলের একটি সেল খালি করে",
    ('excel', 'create_new_file'): "নতুন এক্সেল ফাইল তৈরি করে",
    ('excel', 'convert_to_pdf'): "এক্সেল ফাইলকে PDF-এ রূপান্তর করে",
    ('ocr', 'recognize_file'): "ছবি থেকে টেক্সট শনাক্ত করে (OCR)",
    ('pdf', 'convert_to_image'): "PDF ফাইলকে ছবিতে রূপান্তর করে",
    ('pdf', 'convert_to_word'): "PDF ফাইলকে Word-এ রূপান্তর করে",
    ('pdf', 'read_file'): "PDF ফাইল পড়ে",
    ('shell', 'command'): "সিস্টেমে শেল কমান্ড চালায়",
    ('word', 'convert_to_pdf'): "Word ফাইলকে PDF-এ রূপান্তর করে",
    ('word', 'create_new_file'): "নতুন Word ফাইল তৈরি করে",
    ('word', 'read_file'): "Word ফাইলের বিষয়বস্তু পড়ে",
    ('word', 'write_to_file'): "Word ফাইলে টেক্সট লেখে",
    ('email', 'send_email'): "একজন প্রাপককে ইমেইল পাঠায়",
    ('email', 'list_emails'): "ব্যবহারকারীর ইমেইল তালিকা দেখায়",
    ('email', 'read_email'): "Email ID দিয়ে একটি ইমেইল পড়ে",
    ('llm', 'complete_text'): "একটি prompt-এর উত্তর পেতে LLM-কে জিজ্ঞাসা করে",
}


def tools_schema_block(available_apps):
    import apps
    lines = []
    for app in available_apps:
        for act in apps.AVAILABLE_ACTIONS.get(app, {}):
            demo = getattr(apps.AVAILABLE_ACTIONS[app][act], 'DEMO', f'{app}:{act}')
            bn = SCHEMA_GLOSS.get((app, act), f"'{act}' অ্যাকশন")
            lines.append(f"  • {demo}\n      ↳ বাংলা: {bn}")
    return '\n'.join(lines)


DATA_HINT = ('(1,', 'table from', '\t', 'VEVENT', 'BEGIN:', '.xlsx', '.docx', '.pdf')


def translate_observation(o):
    o = (o or '')
    s = str(o)
    if not s.strip():
        return ''
    # file/table dumps: keep raw (translating would corrupt data), add a Bangla label
    if len(s) > 300 or any(h in s for h in DATA_HINT):
        return "[মূল ফলাফল / raw output — ডেটা হুবহু রাখা হলো]\n" + s
    return translate(s)


def current_app(prompt):
    for line in prompt.split('\n'):
        if line.startswith('##Current apps:'):
            return line.split(':', 1)[1].strip()
    return 'system (কোনো অ্যাপ এখনো নির্বাচিত হয়নি)'


def render(output_dir):
    parts = os.path.normpath(output_dir).replace(os.sep, '/').split('/')
    cid = f'{parts[-4]}/{parts[-2]}'
    settings = json.load(open(f'{output_dir}/settings.json', encoding='utf-8'))
    llm = json.load(open(f'{output_dir}/llm_history.json', encoding='utf-8'))
    env = json.load(open(f'{output_dir}/env_history.json', encoding='utf-8'))
    available_apps = list(settings.get('evaluation') and [] or [])  # placeholder
    # recover available apps from the system message line
    sys_msg = llm[0][0] if llm else ''
    apps_in_sys = [a for a in ['calendar', 'excel', 'ocr', 'pdf', 'shell', 'word', 'email', 'llm']
                   if f' - {a}:' in sys_msg or f'{a}:' in sys_msg]

    L = []
    L.append('=' * 78)
    L.append(f'টাস্ক: {cid}   মডেল: {settings.get("model_name", "?")}')
    L.append('=' * 78)
    L.append('')
    L.append('### ১. সিস্টেম প্রম্পট (বাংলা)')
    L.append(translate(sys_msg))
    L.append('')
    L.append('### ২. ব্যবহারকারীর টাস্ক (বাংলা)')
    L.append(translate(settings.get('task', '')))
    L.append('')
    L.append('### ৫. টুলস স্কিমা (ইংরেজি structure + বাংলা ব্যাখ্যা)')
    L.append(tools_schema_block(apps_in_sys))
    L.append('')
    L.append('### ৩+৪. ধাপে ধাপে: চিন্তা → কমান্ড → ফলাফল')
    L.append('')

    for i in range(max(len(llm), len(env))):
        L.append(f'—————— ধাপ {i} ' + '—' * 40)
        if i < len(llm):
            L.append('  [চিন্তা / THINKING]')
            L.append('    ' + translate(split_thought(llm[i][2])).replace('\n', '\n    '))
        if i < len(env):
            a, o = env[i]
            cmd = json.dumps(a, ensure_ascii=False) if isinstance(a, dict) else str(a)
            L.append('  [কমান্ড / OUTPUT]')
            L.append('    ' + cmd)
            L.append('    ↳ বাংলা: ' + gloss(a))
            L.append('  [ফলাফল / RESULT]')
            L.append('    ' + translate_observation(o).replace('\n', '\n    '))
        L.append('')

    out = os.path.join(output_dir, 'trace_bn.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(L))
    return out


def main():
    args = sys.argv[1:]
    tag = 'gemma4_31b_think'
    limit = None
    ids = []
    i = 0
    while i < len(args):
        if args[i] == '--tag':
            tag = args[i + 1]; i += 2
        elif args[i] == '--limit':
            limit = int(args[i + 1]); i += 2
        else:
            ids.append(args[i]); i += 1

    if ids:
        dirs = [f'tasks/{c.split("/")[0]}/outputs/{c.split("/")[1]}/{tag}' for c in ids]
    else:
        dirs = sorted(glob.glob(f'tasks/*/outputs/*/{tag}'),
                      key=lambda p: (tuple(int(n) for n in p.replace(os.sep, '/').split('/')[1].split('-')),
                                     int(p.replace(os.sep, '/').split('/')[3])))
    dirs = [d for d in dirs if os.path.exists(f'{d}/llm_history.json')]
    if limit:
        dirs = dirs[:limit]

    print(f'{len(dirs)} task(s) to translate; cache has {len(CACHE)} entries', flush=True)
    for n, d in enumerate(dirs, 1):
        start = time.time()
        out = render(d)
        save_cache()
        print(f'[{n}/{len(dirs)}] {out}  ({time.time()-start:.0f}s, cache={len(CACHE)})', flush=True)
    save_cache()
    print('done', flush=True)


if __name__ == '__main__':
    main()
