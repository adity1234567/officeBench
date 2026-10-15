"""gpt-oss:20b paired outcomes on all 300 subtasks (English = gpt-oss_20b_en, Bangla = gpt-oss_20b_bn, corrected scores).

Writes analysis/fa_rows_gptoss.json and prints the groups. Needs analysis/rescored_gpt-oss_20b_bn.json (python analysis/fa_rescore.py gpt-oss_20b_bn).
"""
import json, os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'failure_codes_all_runs.json'), encoding='utf-8'))
GB = json.load(open(os.path.join(HERE, 'rescored_gpt-oss_20b_bn.json'), encoding='utf-8'))
GO = C['pass']['GO']
SIG = json.load(open(os.path.join(HERE, 'fa_signals.json'), encoding='utf-8'))
key = lambda s: (int(s.split('-')[0]), int(s.split('-')[1].split('/')[0]), int(s.split('/')[1]))
ids = sorted(GO, key=key)
assert set(ids) == set(GB)
rows = []
for i in ids:
    rows.append(dict(id=i, apps=int(i.split('-')[0]), en=bool(GO[i]), bn=bool(GB[i]), cat_en=C['cat']['GO'].get(i),
                     sig_en=SIG['GO'].get(i), sig_bn=SIG['GB'].get(i),
                     gem_en=bool(C['pass']['EN'][i]), gem_bn=bool(C['pass']['BN'][i])))
json.dump(rows, open(os.path.join(HERE, 'fa_rows_gptoss.json'), 'w', encoding='utf-8'), indent=1)
pf = [r for r in rows if r['en'] and not r['bn']]
fp = [r for r in rows if not r['en'] and r['bn']]
print('PP', sum(r['en'] and r['bn'] for r in rows), 'PF', len(pf), 'FP', len(fp), 'FF', sum(not r['en'] and not r['bn'] for r in rows))
print('PF ids:', [r['id'] for r in pf])
print('PF by apps:', dict(collections.Counter(r['apps'] for r in pf)), ' FP by apps:', dict(collections.Counter(r['apps'] for r in fp)))
print('FP: English cause code of the 45 subtasks Bangla passes:', dict(collections.Counter(r['cat_en'] for r in fp).most_common()))
print('FP: English run signals: runs with malformed>=1:', sum(1 for r in fp if r['sig_en'] and r['sig_en']['malformed']),
      '| builtin-tool steps total', sum(r['sig_en']['builtin'] for r in fp if r['sig_en']),
      '| ended stuck', sum(1 for r in fp if r['sig_en'] and r['sig_en']['end'] == 'stuck'),
      '| Bangla builtin-tool steps', sum(r['sig_bn']['builtin'] for r in fp if r['sig_bn']))
print('FP also passed by gemma EN:', sum(r['gem_en'] for r in fp), 'of', len(fp), '| gemma BN:', sum(r['gem_bn'] for r in fp))
