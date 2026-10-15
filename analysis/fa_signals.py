"""Behaviour signals per run, from env_history.json: how a run ended, and how often it produced invalid actions.

Signals (per subtask run):
  steps        number of (action, observation) pairs
  malformed    steps whose observation contains "Malformed action"
  empty        steps with no action at all (action is None)
  builtin      steps whose action text calls a model built-in tool instead of the benchmark JSON (container.exec, repo_browser...)
  end          'finish' (finish_task), 'stuck' (got_stuck), 'budget' (20 steps used, no finish), 'other'

    python analysis/fa_signals.py
"""
import glob, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TAGS = {'EN': 'gemma4_31b_think', 'BN': 'gemma4_31b_bn', 'GO': 'gpt-oss_20b_en', 'GB': 'gpt-oss_20b_bn'}
BUILTIN = re.compile(r'container\.exec|repo_browser|functions\.|commentary to=|assistant<\|channel')


def signals(tag):
    out = {}
    for p in glob.glob(os.path.join(ROOT, 'tasks', '*', 'outputs', '*', tag, 'env_history.json')):
        parts = p.replace(os.sep, '/').split('/')
        key = '%s/%s' % (parts[-5], parts[-3])
        try:
            h = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        mal = sum(1 for a, o in h if 'Malformed action' in str(o))
        emp = sum(1 for a, o in h if a is None or str(a).strip() in ('None', ''))
        bi = sum(1 for a, o in h if BUILTIN.search(str(a)) and not isinstance(a, dict))
        last = h[-1][0] if h else None
        if isinstance(last, dict) and last.get('action') == 'finish_task':
            end = 'finish'
        elif isinstance(last, dict) and last.get('action') == 'got_stuck':
            end = 'stuck'
        elif len(h) >= 20:
            end = 'budget'
        else:
            end = 'other'
        out[key] = dict(steps=len(h), malformed=mal, empty=emp, builtin=bi, end=end)
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    res = {k: signals(t) for k, t in TAGS.items()}
    json.dump(res, open(os.path.join(HERE, 'fa_signals.json'), 'w', encoding='utf-8'), indent=0)
    for k, d in res.items():
        n = len(d)
        print('%s n=%d  runs with malformed>=1: %d  total malformed: %d  empty steps: %d  builtin-tool steps: %d  | end: %s'
              % (k, n, sum(1 for v in d.values() if v['malformed']), sum(v['malformed'] for v in d.values()),
                 sum(v['empty'] for v in d.values()), sum(v['builtin'] for v in d.values()),
                 dict(collections.Counter(v['end'] for v in d.values()))))
