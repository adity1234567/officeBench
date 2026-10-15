"""Pipeline steps 1-2: align EN and BN runs per subtask and compute the paired outcome table.

Pass/fail is the corrected score from analysis/failure_codes_all_runs.json (pass: EN = gemma4_31b_think,
BN = gemma4_31b_bn). Run:  python analysis/fa_step2_paired.py
"""
import json, os, math, collections, sys
sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(os.path.join(ROOT, 'analysis', 'failure_codes_all_runs.json'), encoding='utf-8'))
EN, BN = C['pass']['EN'], C['pass']['BN']
ids = sorted(set(EN) & set(BN), key=lambda s: (int(s.split('-')[0]), int(s.split('-')[1].split('/')[0]), int(s.split('/')[1])))
print('aligned subtasks:', len(ids), '| EN only:', len(set(EN) - set(BN)), '| BN only:', len(set(BN) - set(EN)))

def apps(i):
    return int(i.split('-')[0])

rows = []
for i in ids:
    rows.append({'id': i, 'apps': apps(i), 'en': bool(EN[i]), 'bn': bool(BN[i]),
                 'cat_en': C['cat']['EN'].get(i), 'cat_bn': C['cat']['BN'].get(i)})
json.dump(rows, open(os.path.join(ROOT, 'analysis', 'fa_rows.json'), 'w', encoding='utf-8'), indent=1)

def summarize(name, rs):
    n = len(rs)
    pp = sum(r['en'] and r['bn'] for r in rs); pf = sum(r['en'] and not r['bn'] for r in rs)
    fp = sum(not r['en'] and r['bn'] for r in rs); ff = sum(not r['en'] and not r['bn'] for r in rs)
    se, sb = (pp + pf) / n, (pp + fp) / n
    gap = se - sb
    melr = gap / se if se else float('nan')
    # McNemar exact (two-sided) on discordant pairs
    b, c = pf, fp
    m = b + c
    k = min(b, c)
    p = min(1.0, 2 * sum(math.comb(m, j) for j in range(k + 1)) / 2 ** m) if m else 1.0
    # paired bootstrap CIs
    import random
    random.seed(7)
    gaps, melrs = [], []
    for _ in range(4000):
        s = [rs[random.randrange(n)] for _ in range(n)]
        e = sum(r['en'] for r in s) / n; bb = sum(r['bn'] for r in s) / n
        gaps.append(e - bb); melrs.append((e - bb) / e if e else 0)
    gaps.sort(); melrs.sort()
    lo = lambda a: a[int(.025 * len(a))]; hi = lambda a: a[int(.975 * len(a)) - 1]
    # Wilson CI for a proportion
    def wil(x):
        z = 1.96; ph = x / n
        d = 1 + z * z / n
        c0 = (ph + z * z / (2 * n)) / d
        h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
        return c0 - h, c0 + h
    # effect size: odds ratio of discordant pairs, and Cohen's g
    g = (b / m - .5) if m else 0
    return dict(name=name, n=n, pp=pp, pf=pf, fp=fp, ff=ff, en=se, bn=sb, gap=gap, melr=melr, p=p,
                gap_ci=(lo(gaps), hi(gaps)), melr_ci=(lo(melrs), hi(melrs)),
                en_ci=wil(pp + pf), bn_ci=wil(pp + fp), g=g, odds=(b / c if c else float('inf')))

groups = [('Overall', rows)] + [('%d-app' % a, [r for r in rows if r['apps'] == a]) for a in (1, 2, 3)]
out = [summarize(n, r) for n, r in groups]
for s in out:
    print('%-8s n=%3d  EN %.1f%%  BN %.1f%%  gap %.1f pp  MELR %.1f%%  | PP %d  PF %d  FP %d  FF %d | McNemar p=%.4f'
          % (s['name'], s['n'], 100 * s['en'], 100 * s['bn'], 100 * s['gap'], 100 * s['melr'], s['pp'], s['pf'], s['fp'], s['ff'], s['p']))
    print('         gap 95%% CI [%.1f, %.1f] pp   MELR 95%% CI [%.1f, %.1f]%%   Cohen g=%.2f  discordant odds %.2f'
          % (100 * s['gap_ci'][0], 100 * s['gap_ci'][1], 100 * s['melr_ci'][0], 100 * s['melr_ci'][1], s['g'], s['odds']))
json.dump(out, open(os.path.join(ROOT, 'analysis', 'fa_step2.json'), 'w', encoding='utf-8'), indent=1, default=str)
print('\nEN-pass/BN-fail ids:', [r['id'] for r in rows if r['en'] and not r['bn']])
print('EN-fail/BN-pass ids:', [r['id'] for r in rows if not r['en'] and r['bn']])
