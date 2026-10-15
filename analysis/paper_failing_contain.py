"""For gemma4:31b Bangla failures that end with a Bangla-script answer: how many have a failing
evaluate_contain check under the corrected scorer (paper Section 4.4)."""
import contextlib, glob, io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fa_rescore as RS  # noqa: E402  (changes cwd to the repo root and installs the corrected checks)

BN = re.compile('[ঀ-৿]')
corr = json.load(open(os.path.join(HERE, 'failure_codes_all_runs.json'), encoding='utf-8'))['pass']['BN']
n = fail_contain = 0
for f in sorted(glob.glob('tasks/*/subtasks/*.json')):
    p = os.path.normpath(f).split(os.sep)
    t, s = p[1], p[3][:-5]
    if corr.get(f'{t}/{s}'):
        continue
    h = f'tasks/{t}/outputs/{s}/gemma4_31b_bn/env_history.json'
    if not os.path.exists(h):
        continue
    last = json.load(open(h, encoding='utf-8'))[-1][0]
    if not (isinstance(last, dict) and last.get('action') == 'finish_task' and BN.search(str(last.get('answer', '')))):
        continue
    n += 1
    cfg = json.load(open(f, encoding='utf-8'))
    d = f'tasks/{t}/outputs/{s}/gemma4_31b_bn/testbed'
    for e in cfg['evaluation']:
        if e['function'] != 'evaluate_contain':
            continue
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                ok = getattr(RS.ev, e['function'])(d, e['args'])
        except Exception:
            ok = False
        if ok is not True:
            fail_contain += 1
            break
print('Bangla-script answers among corrected failures:', n, '| with a failing evaluate_contain check:', fail_contain)
