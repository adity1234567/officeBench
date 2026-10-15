"""Build the run dashboard data for the gemma4:31b OfficeBench run.

Writes, into analysis/dashboard/ (or the dir given as argv[1]):
  summary.json      one row per subtask (status, failing check, signals, codebook label)
  traces-<n>.json   step-by-step traces for <n>-app tasks
  dashboard.html    the page, with both inlined (publish this file)

Run from the repo root:  python analysis/build_dashboard.py [out_dir] [progress.txt]
"""
import contextlib, csv, glob, io, json, os, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from history_to_trace import evaluate, split_thought

MODEL = os.environ.get('DASH_MODEL', 'gemma4_31b')
RUN_TAGS = os.environ.get('DASH_TAGS', 'think').split(',')  # model-tag folder suffix(es) to read
MODEL_LABEL = os.environ.get('DASH_LABEL', 'gemma4:31b')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'analysis', 'dashboard')
PROGRESS = sys.argv[2] if len(sys.argv) > 2 else None


def clip(s, n):
    s = '' if s is None else str(s)
    return s if len(s) <= n else s[:n] + f' … [+{len(s) - n} chars]'


def current_app(prompt):
    for line in prompt.split('\n'):
        if line.startswith('##Current apps:'):
            return line.split(':', 1)[1].strip()
    return 'system'


labels = {}
with open(os.path.join(ROOT, 'analysis', 'labels_final.csv'), encoding='utf-8') as f:
    for r in csv.DictReader(f):
        labels[(r['id'], r['run_tag'])] = r

rows, traces = [], {'1': {}, '2': {}, '3': {}}
configs = sorted(glob.glob('tasks/*/subtasks/*.json'),
                 key=lambda p: (tuple(int(n) for n in p.replace(os.sep, '/').split('/')[1].split('-')),
                                int(os.path.basename(p)[:-5])))
for cfg_path in configs:
    p = cfg_path.replace(os.sep, '/')
    task_id, sub_id = p.split('/')[1], p.split('/')[3][:-5]
    cid = f'{task_id}/{sub_id}'
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    row = {'id': cid, 'apps': int(task_id[0]), 'goal': cfg['task'], 'status': 'pending'}

    run = next((t for t in RUN_TAGS
                if os.path.exists(f'tasks/{task_id}/outputs/{sub_id}/{MODEL}_{t}/settings.json')), None)
    if run:
        d = f'tasks/{task_id}/outputs/{sub_id}/{MODEL}_{run}'
        llm = json.load(open(f'{d}/llm_history.json', encoding='utf-8'))
        env = json.load(open(f'{d}/env_history.json', encoding='utf-8'))
        with contextlib.redirect_stdout(io.StringIO()):
            passed, reason = evaluate(task_id, sub_id, f'./{d}/testbed')

        last = env[-1][0] if env else None
        last_name = last.get('action') if isinstance(last, dict) else None
        end = {'finish_task': 'finished', 'got_stuck': 'stuck'}.get(last_name, 'max steps')
        signals = []
        malformed = sum('Malformed action' in str(o) for _, o in env)
        if malformed:
            signals.append(f'{malformed} malformed')
        if any(isinstance(a, dict) and a.get('app') == 'llm' and 'No API key' in str(o) for a, o in env):
            signals.append('llm app: no key')
        if reason.startswith('evaluator error'):
            signals.append('evaluator error')
        answer = last.get('answer') if isinstance(last, dict) and last_name == 'finish_task' else None

        row.update(status='pass' if passed else 'fail', run=run, steps=len(env), end=end,
                   check=None if passed else reason, signals=signals,
                   answer=None if answer in (None, 'None') else clip(answer, 300))
        lab = labels.get((cid, run))
        if lab:
            row['label'] = {'primary': lab['primary'], 'tags': [t for t in lab['tags'].split(';') if t],
                            'step': lab['decisive_step'], 'why': lab['rationale']}

        steps = []
        for i in range(max(len(llm), len(env))):
            s = {}
            if i < len(llm):
                s['app'] = current_app(llm[i][1])
                s['think'] = clip(split_thought(llm[i][2]), 1500)
            if i < len(env):
                a, o = env[i]
                s['act'] = clip(json.dumps(a) if isinstance(a, dict) else a, 800)
                s['result'] = clip(o, 1500)
            steps.append(s)
        traces[task_id[0]][cid] = steps
    elif os.path.isdir(f'tasks/{task_id}/outputs/{sub_id}'):
        # attempted but never saved a result (e.g. docker cp could not copy a file whose
        # name is illegal on Windows); evaluation.py counts this as a fail, so do we
        row.update(status='fail', end='not saved', check='result not saved (harness)',
                   signals=['harness: could not copy output on Windows'], steps=0)
    rows.append(row)

state = 'not running'
if PROGRESS and os.path.exists(PROGRESS):
    text = open(PROGRESS, encoding='utf-8', errors='replace').read()
    if 'Evaluation run finished' in text:
        state = 'finished'
    elif '429' in text:
        state = 'stopped: usage limit'
    else:
        state = 'running'

os.makedirs(OUT, exist_ok=True)
summary = {'model': MODEL_LABEL, 'generated': time.strftime('%Y-%m-%d %H:%M'), 'state': state, 'rows': rows}
json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w', encoding='utf-8'), ensure_ascii=False)
for n, t in traces.items():
    json.dump(t, open(os.path.join(OUT, f'traces-{n}.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# single self-contained page: data inlined into the template (escape `</` so it can't close the script)
def inline(obj):
    # strip U+FFFD (replacement chars from garbled model output) so the page stays clean
    return json.dumps(obj, ensure_ascii=False).replace('</', '<\\/').replace('�', '')

template = open(os.path.join(ROOT, 'analysis', 'dashboard', 'template.html'), encoding='utf-8').read()
page = template.replace('/*DATA*/null', inline(summary)).replace('/*TRACES*/null', inline(traces))
open(os.path.join(OUT, 'dashboard.html'), 'w', encoding='utf-8').write(page)

done = [r for r in rows if r['status'] != 'pending']
print(f"{len(done)}/{len(rows)} done, {sum(r['status'] == 'pass' for r in done)} pass, state={state}")
for n in traces:
    print(f'traces-{n}.json', os.path.getsize(os.path.join(OUT, f'traces-{n}.json')) // 1024, 'KB')
