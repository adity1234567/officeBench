"""Pipeline step 4 helper: condensed side-by-side EN / BN trajectories for every EN-pass/BN-fail case.

    python analysis/fa_step4_extract_go.py > analysis/fa_pairs_gptoss.txt
"""
import json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, 'analysis', 'fa_rows_gptoss.json'), encoding='utf-8'))
cases = [r for r in rows if r['en'] and not r['bn']]


def load(path):
    try:
        return json.load(open(path, encoding='utf-8'))
    except Exception:
        return None


def short(a, n=150):
    if not isinstance(a, dict):
        n = min(n, 110)
    if isinstance(a, dict):
        a = {k: v for k, v in a.items() if k != 'app' or True}
    s = json.dumps(a, ensure_ascii=False) if isinstance(a, dict) else str(a)
    s = re.sub(r'\s+', ' ', s)
    return s if len(s) <= n else s[:n] + '…'


def key(a):
    if isinstance(a, dict):
        return (a.get('app'), a.get('action'))
    return str(a)[:40]


for r in cases:
    t, s = r['id'].split('/')
    cfg = load(os.path.join(ROOT, 'tasks', t, 'subtasks', s + '.json')) or {}
    en = load(os.path.join(ROOT, 'tasks', t, 'outputs', s, 'gpt-oss_20b_en', 'env_history.json')) or []
    bn = load(os.path.join(ROOT, 'tasks', t, 'outputs', s, 'gpt-oss_20b_bn', 'env_history.json')) or []
    print('=' * 100)
    print('%s  apps=%s  EN-code=%s' % (r['id'], r['apps'], r.get('cat_en')))
    print('TASK:', cfg.get('task'))
    print('CHECKS:', '; '.join('%s %s' % (e['function'], short(e['args'], 110)) for e in cfg.get('evaluation', [])))
    div = None
    for i in range(max(len(en), len(bn))):
        a = en[i][0] if i < len(en) else None
        b = bn[i][0] if i < len(bn) else None
        if a != b:
            div = i
            break
    print('STEPS: EN=%d BN=%d  first-differing-step=%s' % (len(en), len(bn), div))
    for tag, h in (('EN', en), ('BN', bn)):
        for i, (a, o) in enumerate(h):
            mark = '*' if div is not None and i == div else ' '
            print(' %s %s%02d ACT %s' % (mark, tag, i, short(a, 190)))
            if i >= div - 0 if div is not None else False:
                pass
            if (div is not None and i >= max(div - 1, 0)) and tag == 'BN' or i == len(h) - 1:
                print('        OBS %s' % short(o, 140))
