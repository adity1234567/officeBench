"""For each gpt-oss EN-pass/BN-fail case: which of the benchmark's checks fail in the Bangla run (evidence for labelling)."""
import contextlib, io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fa_rescore as RS  # noqa: E402  (changes cwd to the repo root and installs the corrected checks)

rows = json.load(open(os.path.join(HERE, 'fa_rows_gptoss.json'), encoding='utf-8'))
ev = RS.ev
for r in rows:
    if not (r['en'] and not r['bn']):
        continue
    t, s = r['id'].split('/')
    cfg = json.load(open(os.path.join('tasks', t, 'subtasks', s + '.json'), encoding='utf-8'))
    bad = []
    for e in cfg['evaluation']:
        d = os.path.join('tasks', t, 'outputs', s, 'gpt-oss_20b_bn', 'testbed')
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ok = getattr(ev, e['function'])(d, e['args'])
        except Exception as ex:
            ok = 'ERR %s' % ex
        if ok is not True:
            bad.append('%s %s -> %s' % (e['function'].replace('evaluate_', ''), json.dumps(e['args'], ensure_ascii=False)[:150], ok))
    print(r['id'], '| failing in BN:', ' ;; '.join(bad))
