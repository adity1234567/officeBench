"""Build the Bangla-run dashboard (the Bangla experiment): the agent actually ran with a
Bangla system prompt + Bangla task, so its thinking is natively Bangla. Shows, per task, the
Bangla system prompt, task, tool schema (English + Bangla gloss), and step-by-step
thinking -> command -> result, plus an English-vs-Bangla pass-rate comparison.

Reuses the translation cache only for the Bangla task text; no new API calls for the run
itself (the model already produced Bangla). Writes analysis/dashboard_bn/dashboard_bn.html

    python analysis/build_dashboard_bn.py [progress.txt]
"""
import glob, json, os, sys, contextlib, io, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from history_to_trace import evaluate, split_thought
import translate_bn as T  # cache-backed translate() for the task text; gloss(); schema

BN = 'gemma4_31b_bn'
EN = 'gemma4_31b_think'
OUT = os.path.join(ROOT, 'analysis', 'dashboard_bn')
PROGRESS = sys.argv[1] if len(sys.argv) > 1 else None


def clip(s, n):
    s = '' if s is None else str(s)
    return s if len(s) <= n else s[:n] + ' … [+%d]' % (len(s) - n)


def result(tag, tid, sid):
    d = f'tasks/{tid}/outputs/{sid}/{tag}'
    if not os.path.exists(f'{d}/env_history.json'):
        return None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            p, _ = evaluate(tid, sid, f'./{d}/testbed')
        return bool(p)
    except Exception:
        return None


systems, schemas = {}, {}
def intern(store, text):
    if text not in store:
        store[text] = len(store)
    return store[text]


rows = []
cmp = {'en': {1: [0, 0], 2: [0, 0], 3: [0, 0]}, 'bn': {1: [0, 0], 2: [0, 0], 3: [0, 0]}}
configs = sorted(glob.glob('tasks/*/subtasks/*.json'),
                 key=lambda p: (tuple(int(n) for n in p.replace(os.sep, '/').split('/')[1].split('-')),
                                int(os.path.basename(p)[:-5])))
for cfg_path in configs:
    p = cfg_path.replace(os.sep, '/')
    task_id, sub_id = p.split('/')[1], p.split('/')[3][:-5]
    cid = f'{task_id}/{sub_id}'
    apps = int(task_id[0])
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    row = {'id': cid, 'apps': apps, 'goal_bn': T.translate(cfg.get('task', ''))}

    en = result(EN, task_id, sub_id)
    if en is not None:
        row['en'] = 'pass' if en else 'fail'

    d = f'tasks/{task_id}/outputs/{sub_id}/{BN}'
    if not os.path.exists(f'{d}/llm_history.json'):
        row['status'] = 'pending'
        rows.append(row)
        continue
    bn = result(BN, task_id, sub_id)
    row['status'] = 'pass' if bn else 'fail'
    # compare only over tasks BOTH runs have completed (apples-to-apples)
    if en is not None:
        cmp['en'][apps][0 if en else 1] += 1
        cmp['bn'][apps][0 if bn else 1] += 1

    llm = json.load(open(f'{d}/llm_history.json', encoding='utf-8'))
    env = json.load(open(f'{d}/env_history.json', encoding='utf-8'))
    sys_msg = llm[0][0] if llm else ''          # already Bangla (the run used a Bangla prompt)
    apps_in_sys = [a for a in ['calendar', 'excel', 'ocr', 'pdf', 'shell', 'word', 'email', 'llm']
                   if f'{a}:' in sys_msg]
    row['sys'] = intern(systems, sys_msg)
    row['sch'] = intern(schemas, T.tools_schema_block(apps_in_sys))

    steps = []
    for i in range(max(len(llm), len(env))):
        s = {}
        if i < len(llm):
            s['t'] = split_thought(llm[i][2])    # native Bangla thinking, no translation
        if i < len(env):
            a, o = env[i]
            s['c'] = json.dumps(a, ensure_ascii=False) if isinstance(a, dict) else str(a)
            s['g'] = T.gloss(a)
            s['r'] = clip(str(o), 1000)          # tool output (English), shown as-is
        steps.append(s)
    row['steps'] = steps
    rows.append(row)

T.save_cache()

state = 'চলছে'
if PROGRESS and os.path.exists(PROGRESS):
    txt = open(PROGRESS, encoding='utf-8', errors='replace').read()
    if 'Evaluation run finished' in txt:
        state = 'সম্পূর্ণ'
    elif '429' in txt:
        state = 'থেমে গেছে (quota)'

data = {
    'generated': time.strftime('%Y-%m-%d %H:%M'),
    'state': state,
    'compare': cmp,
    'systems': [k for k, _ in sorted(systems.items(), key=lambda x: x[1])],
    'schemas': [k for k, _ in sorted(schemas.items(), key=lambda x: x[1])],
    'rows': rows,
}

os.makedirs(OUT, exist_ok=True)
tmpl = open(os.path.join(OUT, 'template_bn.html'), encoding='utf-8').read()
page = tmpl.replace('/*DATA*/null', json.dumps(data, ensure_ascii=False).replace('</', '<\\/').replace('�', ''))
open(os.path.join(OUT, 'dashboard_bn.html'), 'w', encoding='utf-8').write(page)

bnp = sum(r['status'] == 'pass' for r in rows)
bnd = sum(r['status'] != 'pending' for r in rows)
print(f'bn done={bnd}/300 pass={bnp}; {len(systems)} uniq system; '
      f'{os.path.getsize(os.path.join(OUT, "dashboard_bn.html"))//1024} KB')
