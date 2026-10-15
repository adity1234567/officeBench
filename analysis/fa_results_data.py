"""Numbers behind the results charts. Importable (module-level dict R) and runnable for a printout.

Runs: EN = gemma4:31b English, BN = gemma4:31b Bangla, GO = gpt-oss:20b English, GB = gpt-oss:20b Bangla (all 300 subtasks).
Pass/fail is the corrected score. EN, BN and GO come from analysis/failure_codes_all_runs.json; GB comes from
analysis/rescored_gpt-oss_20b_bn.json (python analysis/fa_rescore.py gpt-oss_20b_bn), because the Bangla run finished after
failure_codes_all_runs.json was built (it holds only the first 51). fa_rescore.py reproduces the other three runs exactly.
"""
import json, os, collections, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'failure_codes_all_runs.json'), encoding='utf-8'))
P, CAT = C['pass'], C['cat']
_gb = json.load(open(os.path.join(HERE, 'rescored_gpt-oss_20b_bn.json'), encoding='utf-8'))
P['GB'] = {k: bool(v) for k, v in _gb.items()}   # full 300-subtask Bangla run for gpt-oss
APPS = lambda i: int(i.split('-')[0])
RUNS = [('EN', 'gemma4:31b', 'English'), ('BN', 'gemma4:31b', 'Bangla'),
        ('GO', 'gpt-oss:20b', 'English'), ('GB', 'gpt-oss:20b', 'Bangla')]

R = {}
R['n'] = {k: len(P[k]) for k, _, _ in RUNS}


def rate(run, apps=None, ids=None):
    xs = [i for i in P[run] if (apps is None or APPS(i) == apps) and (ids is None or i in ids)]
    return sum(bool(P[run][i]) for i in xs), len(xs)


R['rate'] = {k: {a: rate(k, a) for a in (None, 1, 2, 3)} for k, _, _ in RUNS}
# paired outcome by app size, for each model: (English run, Bangla run)
def _pair(en, bn):
    out = {}
    for a in (None, 1, 2, 3):
        ids = [i for i in P[en] if a is None or APPS(i) == a]
        out[a] = dict(PP=sum(P[en][i] and P[bn][i] for i in ids), PF=sum(P[en][i] and not P[bn][i] for i in ids),
                      FP=sum(not P[en][i] and P[bn][i] for i in ids), FF=sum(not P[en][i] and not P[bn][i] for i in ids))
    return out


R['pair'] = _pair('EN', 'BN')
R['pair_go'] = _pair('GO', 'GB')

# failure causes per run (primary codes)
R['cat'] = {k: collections.Counter(CAT[k].values()) for k in ('EN', 'BN', 'GO', 'GB')}   # GB: only the 21 failures among the first 51 subtasks are root-cause coded

# pass patterns over all four runs, and the three-run view used earlier
pat4 = collections.Counter()
pat = collections.Counter()
for i in P['EN']:
    pat4[(bool(P['EN'][i]), bool(P['BN'][i]), bool(P['GO'][i]), bool(P['GB'][i]))] += 1
    pat[(bool(P['EN'][i]), bool(P['BN'][i]), bool(P['GO'][i]))] += 1
R['pattern4'], R['pattern'] = pat4, pat
fail_all = [i for i in P['EN'] if not (P['EN'][i] or P['BN'][i] or P['GO'][i])]
pass_all = [i for i in P['EN'] if P['EN'][i] and P['BN'][i] and P['GO'][i]]
R['fail_all'], R['pass_all'] = len(fail_all), len(pass_all)
R['fail_all_same'] = sum(1 for i in fail_all if CAT['EN'].get(i) == CAT['BN'].get(i) == CAT['GO'].get(i))
R['bm_any'] = sum(1 for i in P['EN'] if any(CAT[k].get(i) == 'BM' for k in ('EN', 'BN', 'GO')))
R['fail_all4'] = sum(1 for i in P['EN'] if not any(P[k][i] for k in ('EN', 'BN', 'GO', 'GB')))
R['pass_all4'] = sum(1 for i in P['EN'] if all(P[k][i] for k in ('EN', 'BN', 'GO', 'GB')))

if __name__ == '__main__':
    for k, m, l in RUNS:
        print(k, m, l, 'n=%d' % R['n'][k], {('all' if a is None else a): '%d/%d' % R['rate'][k][a] for a in R['rate'][k]})
    print('pair gemma', R['pair']); print('pair gpt-oss', R['pair_go'])
    print('patterns (EN,BN,GO,GB):', dict(R['pattern4']))
    print('fail in all four', R['fail_all4'], '| pass in all four', R['pass_all4'], '| fail in first three', R['fail_all'], 'same cause', R['fail_all_same'], '| BM in any of first three', R['bm_any'])
