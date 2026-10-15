"""Recompute every OfficeBench number used in paper/main.tex.

  --official   reproduce analysis/paper_stats.json from the official scorer output (validation)
  (default)    same statistics with the corrected pass/fail of analysis/failure_codes_all_runs.json
               (the three scorer repairs of fa_rescore.py) -> analysis/paper_stats_corrected.json

Signals are read from each episode's env_history.json:
  malformed      failed episode with at least one observation 'Malformed action!'
  stuck          failed episode whose last action is got_stuck
  maxsteps       failed episode with >= 20 actions that did not end in finish_task or got_stuck
  finished_fail  failed episode that ended with finish_task
  nosave         no env_history.json
  bengali_answer failed episode whose finish_task answer contains Bengali script
"""
import glob, json, os, re, sys
from math import comb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
RUNS = {'gemma-EN': ('gemma4_31b_think', 'EN'), 'gemma-BN': ('gemma4_31b_bn', 'BN'),
        'gptoss-EN': ('gpt-oss_20b_en', 'GO'), 'gptoss-BN': ('gpt-oss_20b_bn', 'GB')}
BN_RE = re.compile('[ঀ-৿]')


def subtasks():
    out = []
    for f in glob.glob('tasks/*/subtasks/*.json'):
        p = os.path.normpath(f).split(os.sep)
        out.append(f'{p[1]}/{p[3][:-5]}')
    return sorted(out)


def apps(key):
    return key.split('-')[0]


def official(tag):
    d = {}
    for l in open(f'results/{tag}_result.jsonl', encoding='utf-8'):
        r = json.loads(l)
        d[f"{r['task_id']}/{r['subtask_id']}"] = bool(r['is_pass'])
    return d


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def episode(key, tag):
    t, s = key.split('/')
    p = f'tasks/{t}/outputs/{s}/{tag}/env_history.json'
    if not os.path.exists(p):
        return None
    h = json.load(open(p, encoding='utf-8'))
    acts = [x[0] for x in h]
    obs = [str(x[1]) for x in h]
    last = acts[-1] if acts else None
    end = last.get('action') if isinstance(last, dict) else None
    ans = last.get('answer', '') if end == 'finish_task' else ''
    return {'steps': len(h), 'malformed': any('Malformed action' in o for o in obs), 'end': end,
            'bn_answer': bool(BN_RE.search(str(ans)))}


def main(use_official):
    keys = subtasks()
    corr = json.load(open('analysis/failure_codes_all_runs.json', encoding='utf-8'))['pass']
    # failure_codes_all_runs.json holds only the first 51 gpt-oss Bangla subtasks; the full rescore
    # of all 300 (same three repairs, fa_rescore.py) is in rescored_gpt-oss_20b_bn.json
    corr['GB'] = json.load(open('analysis/rescored_gpt-oss_20b_bn.json', encoding='utf-8'))
    P, stats, by_app = {}, {}, {}
    for name, (tag, ck) in RUNS.items():
        P[name] = official(tag) if use_official else {k: bool(corr[ck].get(k, False)) for k in keys}
        s = dict(n=len(keys), npass=0, nfail=0, malformed=0, stuck=0, maxsteps=0, finished_fail=0, nosave=0,
                 bengali_answer=0)
        steps = []
        ba = {}
        for k in keys:
            ok = P[name].get(k, False)
            a = apps(k)
            ba.setdefault(a, [0, 0]); ba[a][1] += 1; ba[a][0] += ok
            e = episode(k, tag)
            if e:
                steps.append(e['steps'])
            if ok:
                s['npass'] += 1
                continue
            s['nfail'] += 1
            if e is None:
                s['nosave'] += 1
                continue
            s['malformed'] += e['malformed']
            s['bengali_answer'] += e['bn_answer']
            if e['end'] == 'got_stuck':
                s['stuck'] += 1
            elif e['end'] == 'finish_task':
                s['finished_fail'] += 1
            else:
                s['maxsteps'] += 1
        s['avg_steps'] = round(sum(steps) / len(steps), 2)
        stats[name], by_app[name] = s, ba
    mc = {}
    for a, b in [('gemma-EN', 'gemma-BN'), ('gptoss-EN', 'gptoss-BN'), ('gemma-EN', 'gptoss-EN'), ('gemma-BN', 'gptoss-BN')]:
        x = sum(1 for k in keys if P[a].get(k) and not P[b].get(k))
        y = sum(1 for k in keys if P[b].get(k) and not P[a].get(k))
        mc[f'{a} vs {b}'] = {'only_first': x, 'only_second': y, 'p': mcnemar(x, y)}
    # lenient bound: credit every failed episode whose final answer is in Bangla script
    lenient = {n: stats[n]['npass'] + stats[n]['bengali_answer'] for n in stats}
    out = {'scores': 'official' if use_official else 'corrected', 'stats': stats, 'mcnemar': mc,
           'pass_by_app': by_app, 'lenient_npass': lenient}
    return out


if __name__ == '__main__':
    off = '--official' in sys.argv
    res = main(off)
    if off:
        ref = json.load(open('analysis/paper_stats.json', encoding='utf-8'))
        bad = [(r, f, res['stats'][r][f], ref['stats'][r][f]) for r in ref['stats'] for f in ref['stats'][r]
               if res['stats'][r][f] != ref['stats'][r][f]]
        bad += [(c, res['mcnemar'][c]['only_first'], ref['mcnemar'][c]['only_first']) for c in ref['mcnemar']
                if (res['mcnemar'][c]['only_first'], res['mcnemar'][c]['only_second']) !=
                (ref['mcnemar'][c]['only_first'], ref['mcnemar'][c]['only_second'])]
        print('validation mismatches:', bad if bad else 'none')
    else:
        json.dump(res, open('analysis/paper_stats_corrected.json', 'w', encoding='utf-8'), indent=1)
    print(json.dumps(res, indent=1))
