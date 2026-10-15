"""Every number used in paper_acl/main.tex that can be computed from data in this repository.

OfficeBench numbers are computed from the run logs (tasks/*/outputs/*/<tag>/env_history.json) and the
corrected pass/fail of the repaired scorer (analysis/failure_codes_all_runs.json and, for the full
gpt-oss Bangla run, analysis/rescored_gpt-oss_20b_bn.json; see analysis/fa_rescore.py).
tau2-bench, WorkBench and TheAgentCompany have no raw data here: their discordant counts and bootstrap
intervals are transcribed from the four failure-analysis reports (sobhar_kaj/*.pdf) and marked as such.

    python analysis/acl_rewrite_stats.py      -> analysis/acl_rewrite_tables.json and .md
"""
import glob, json, os, random, re
from math import comb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TAGS = {'gemma-EN': 'gemma4_31b_think', 'gemma-BN': 'gemma4_31b_bn',
        'gptoss-EN': 'gpt-oss_20b_en', 'gptoss-BN': 'gpt-oss_20b_bn'}
CK = {'gemma-EN': 'EN', 'gemma-BN': 'BN', 'gptoss-EN': 'GO', 'gptoss-BN': 'GB'}
BN_RE = re.compile('[ঀ-৿]')
BN_DIGIT = re.compile('[০-৯]')


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0] * len(ps), 0
    for r, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - r) * ps[i]))
        adj[i] = run
    return adj


def keys():
    out = []
    for f in glob.glob('tasks/*/subtasks/*.json'):
        p = os.path.normpath(f).split(os.sep)
        out.append(f'{p[1]}/{p[3][:-5]}')
    return sorted(out)


K = keys()
corr = json.load(open('analysis/failure_codes_all_runs.json', encoding='utf-8'))['pass']
corr['GB'] = json.load(open('analysis/rescored_gpt-oss_20b_bn.json', encoding='utf-8'))
P = {r: {k: bool(corr[CK[r]].get(k, False)) for k in K} for r in TAGS}
apps = {k: int(k.split('-')[0]) for k in K}


def hist(k, run):
    t, s = k.split('/')
    f = f'tasks/{t}/outputs/{s}/{TAGS[run]}/env_history.json'
    return json.load(open(f, encoding='utf-8')) if os.path.exists(f) else None


def boot_gap(a, b, n=4000, seed=7):
    rnd = random.Random(seed)
    diffs = []
    for _ in range(n):
        idx = [rnd.randrange(len(K)) for _ in K]
        diffs.append(100 * (sum(P[a][K[i]] for i in idx) - sum(P[b][K[i]] for i in idx)) / len(K))
    diffs.sort()
    return round(diffs[int(0.025 * n)], 1), round(diffs[int(0.975 * n) - 1], 1)


T = {}
# ---------------- RQ1: OfficeBench gaps ----------------
ob = {}
for m in ['gemma', 'gptoss']:
    e, b = f'{m}-EN', f'{m}-BN'
    ne, nb = sum(P[e].values()), sum(P[b].values())
    bb = sum(1 for k in K if P[e][k] and not P[b][k])
    cc = sum(1 for k in K if P[b][k] and not P[e][k])
    ob[m] = dict(n=len(K), en=round(100 * ne / len(K), 1), bn=round(100 * nb / len(K), 1),
                 gap=round(100 * (ne - nb) / len(K), 1), melr=round(100 * (ne - nb) / ne, 1),
                 en_only=bb, bn_only=cc, p=mcnemar(bb, cc), ci=boot_gap(e, b))
    sub = {}
    for a in (1, 2, 3):
        ks = [k for k in K if apps[k] == a]
        x = sum(1 for k in ks if P[e][k] and not P[b][k]); y = sum(1 for k in ks if P[b][k] and not P[e][k])
        sub[a] = dict(n=len(ks), en=round(100 * sum(P[e][k] for k in ks) / len(ks), 1),
                      bn=round(100 * sum(P[b][k] for k in ks) / len(ks), 1), en_only=x, bn_only=y, p=mcnemar(x, y))
    for a, adj in zip((1, 2, 3), holm([sub[a]['p'] for a in (1, 2, 3)])):
        sub[a]['p_holm'] = adj
    ob[m]['by_apps'] = sub
T['officebench'] = ob

# ---------------- RQ1: all seven comparisons, Holm across seven ----------------
# discordant counts: OfficeBench computed above; others transcribed from the reports
pe = lambda m: sum(P[f'{m}-EN'].values())
pb = lambda m: sum(P[f'{m}-BN'].values())
# (bench, model, n, EN passes, BN passes, EN-only, BN-only, bootstrap CI, source)
seven = [
    ('OB', 'gemma4-31b', 300, pe('gemma'), pb('gemma'), ob['gemma']['en_only'], ob['gemma']['bn_only'], ob['gemma']['ci'], 'computed'),
    ('OB', 'gpt-oss-20b', 300, pe('gptoss'), pb('gptoss'), ob['gptoss']['en_only'], ob['gptoss']['bn_only'], ob['gptoss']['ci'], 'computed'),
    ('WB', 'gemma4-31b', 90, 73, 74, 7, 8, (-10.0, 7.8), 'WORKBENCH report'),
    ('WB', 'gpt-oss-20b', 90, 53, 48, 15, 10, (-5.6, 16.7), 'WORKBENCH report'),
    ('tau2', 'gemma4-31b', 218, 108, 83, 40, 15, (5.0, 17.4), 'TAU2 report'),
    ('tau2', 'gpt-oss-20b', 149, 58, 59, 26, 27, (-10.7, 8.7), 'TAU2 report'),
    ('TAC', 'gemma4-31b', 23, 9, 6, 3, 0, (0.0, 26.1), 'TAC report'),
]
ps = [mcnemar(r[5], r[6]) for r in seven]
rows = []
for r, p, ph in zip(seven, ps, holm(ps)):
    n, e, b = r[2], r[3], r[4]
    assert e - b == r[5] - r[6], r   # passes and discordant counts must agree
    rows.append(dict(bench=r[0], model=r[1], n=n, en=round(100 * e / n, 1), bn=round(100 * b / n, 1),
                     gap=round(100 * (e - b) / n, 1), melr=round(100 * (e - b) / e, 1), en_only=r[5], bn_only=r[6],
                     p=p, p_holm=ph, ci=list(r[7]), source=r[8]))
T['seven'] = rows
T['ob_model_gap'] = {
    'EN': dict(gemma_only=sum(1 for k in K if P['gemma-EN'][k] and not P['gptoss-EN'][k]),
               gptoss_only=sum(1 for k in K if P['gptoss-EN'][k] and not P['gemma-EN'][k])),
    'BN': dict(gemma_only=sum(1 for k in K if P['gemma-BN'][k] and not P['gptoss-BN'][k]),
               gptoss_only=sum(1 for k in K if P['gptoss-BN'][k] and not P['gemma-BN'][k]))}
for l in ('EN', 'BN'):
    d = T['ob_model_gap'][l]; d['p'] = mcnemar(d['gemma_only'], d['gptoss_only'])
# how gpt-oss fails on the English tasks that only gemma solves
cats = json.load(open('analysis/failure_codes_all_runs.json', encoding='utf-8'))['cat']['GO']
lost = [k for k in K if P['gemma-EN'][k] and not P['gptoss-EN'][k]]
lm = ls = lo = 0
for k in lost:
    t, s_ = k.split('/')
    f = f'tasks/{t}/outputs/{s_}/gpt-oss_20b_en/env_history.json'
    if not os.path.exists(f):
        continue
    h = json.load(open(f, encoding='utf-8'))
    lm += any(str(o).startswith('Malformed action') for _, o in h)
    end = h[-1][0].get('action') if h and isinstance(h[-1][0], dict) else None
    ls += end == 'got_stuck'; lo += end not in ('got_stuck', 'finish_task')
T['ob_model_gap']['gptoss_losses_EN'] = dict(tasks=len(lost), with_malformed_action=lm, ended_stuck=ls,
                                             ended_at_step_limit=lo,
                                             primary_code_FMT=sum(1 for k in lost if cats.get(k) == 'FMT'))
# agent errors inside benchmark-defect runs (section 4.5): runs whose primary cause is BM that
# still contain a rejected action
allcats = json.load(open('analysis/failure_codes_all_runs.json', encoding='utf-8'))['cat']
T['bm_runs_with_rejected_action'] = {}
for code, tag in (('EN', 'gemma4_31b_think'), ('GO', 'gpt-oss_20b_en')):
    bm = [k for k, v in allcats[code].items() if v == 'BM']
    n_rej = 0
    for k in bm:
        t, s_ = k.split('/')
        f = f'tasks/{t}/outputs/{s_}/{tag}/env_history.json'
        if os.path.exists(f) and any(str(o).startswith('Malformed action') for _, o in json.load(open(f, encoding='utf-8'))):
            n_rej += 1
    T['bm_runs_with_rejected_action'][tag] = dict(bm_runs=len(bm), with_rejected_action=n_rej)

# ---------------- RQ2 / 4.4: trajectory measurements (OfficeBench) ----------------
FILE_WRITE = {('excel', 'set_cell'), ('excel', 'delete_cell'), ('excel', 'create_new_file'),
              ('word', 'write_to_file'), ('word', 'create_new_file')}
FILE_READ = {('excel', 'read_file'), ('word', 'read_file'), ('pdf', 'read_file')}


def failed_obs(o):
    o = str(o)
    return o.startswith('Malformed action') or o.lower().startswith('error') or 'Traceback' in o


traj = {}
for run in TAGS:
    malformed_total = 0; runs_with_hist = 0
    outsteps_by_app = {1: 0, 2: 0, 3: 0}
    outsteps_no_rejected = outsteps_half_rejected = 0
    write_runs = verified_runs = 0
    fail_steps = repeated_after_fail = 0
    runs_with_fail = runs_identical_streak3 = 0
    for k in K:
        h = hist(k, run)
        if h is None:
            continue
        runs_with_hist += 1
        acts = [x[0] for x in h]; obs = [x[1] for x in h]
        malformed_total += sum(1 for o in obs if str(o).startswith('Malformed action'))
        last = acts[-1] if acts else None
        end = last.get('action') if isinstance(last, dict) else None
        if not P[run][k] and end not in ('finish_task', 'got_stuck'):
            outsteps_by_app[apps[k]] += 1
            # out-of-step failure: was the budget spent on valid steps or on rejected ones?
            nrej = sum(1 for o in obs if failed_obs(o))
            if nrej == 0:
                outsteps_no_rejected += 1
            elif nrej >= len(h) / 2:
                outsteps_half_rejected += 1
        # verification: a written file is later read back (read_file of the same file, or a shell
        # command naming it); a created calendar event is followed by list_events
        written, ver = [], False
        for i, a in enumerate(acts):
            if not isinstance(a, dict):
                continue
            key = (a.get('app'), a.get('action'))
            fp = os.path.basename(str(a.get('file_path', a.get('filename', ''))))
            if key in FILE_WRITE and fp:
                written.append((i, fp, 'file'))
            if key == ('calendar', 'create_event'):
                written.append((i, '', 'cal'))
        for i, fp, kind in written:
            for a in acts[i + 1:]:
                if not isinstance(a, dict):
                    continue
                key = (a.get('app'), a.get('action'))
                if kind == 'file' and ((key in FILE_READ and os.path.basename(str(a.get('file_path', ''))) == fp)
                                       or (key[0] == 'shell' and fp in str(a.get('command', '')))):
                    ver = True
                if kind == 'cal' and key == ('calendar', 'list_events'):
                    ver = True
        if written:
            write_runs += 1; verified_runs += ver
        # repetition after a failed step: the next action is identical to the failed one
        had_fail = False
        for i in range(len(h) - 1):
            if failed_obs(obs[i]):
                had_fail = True; fail_steps += 1
                if json.dumps(acts[i + 1], sort_keys=True, ensure_ascii=False) == json.dumps(acts[i], sort_keys=True, ensure_ascii=False):
                    repeated_after_fail += 1
        runs_with_fail += had_fail
        streak = best = 1
        for i in range(1, len(h)):
            same = json.dumps(acts[i], sort_keys=True, ensure_ascii=False) == json.dumps(acts[i - 1], sort_keys=True, ensure_ascii=False)
            streak = streak + 1 if (same and failed_obs(obs[i]) and failed_obs(obs[i - 1])) else 1
            best = max(best, streak)
        runs_identical_streak3 += best >= 3
    nfail = sum(1 for k in K if not P[run][k])
    traj[run] = dict(runs_with_history=runs_with_hist, malformed_actions_total=malformed_total,
                     out_of_steps_failures_by_apps=outsteps_by_app, failures=nfail,
                     out_of_steps_no_rejected_step=outsteps_no_rejected,
                     out_of_steps_half_or_more_rejected=outsteps_half_rejected,
                     runs_with_write=write_runs, runs_write_verified=verified_runs,
                     failed_steps=fail_steps, failed_steps_followed_by_identical_action=repeated_after_fail,
                     runs_with_failed_step=runs_with_fail, runs_with_3plus_identical_rejected_actions=runs_identical_streak3)
T['trajectory'] = traj

# ---------------- answer script (RQ3 checker artefact) ----------------
ans = {}
for run in ('gemma-BN', 'gptoss-BN'):
    n = 0
    for k in K:
        if P[run][k]:
            continue
        h = hist(k, run)
        if not h:
            continue
        last = h[-1][0]
        if isinstance(last, dict) and last.get('action') == 'finish_task' and BN_RE.search(str(last.get('answer', ''))):
            n += 1
    ans[run] = dict(failures=sum(1 for k in K if not P[run][k]), bangla_script_answers=n)
T['answer_script'] = ans

# ---------------- translation audit of the instructions actually used in the runs ----------------
cache = json.load(open('analysis/bn_cache.before_v2.json', encoding='utf-8'))
NAMES = ['Bob', 'Tom', 'Alice', 'Bill', 'Jane', 'Doe', 'Carol', 'Dan', 'Rena', 'Anna']
FILE_RE = re.compile(r'[\w\-./]*\w\.(?:xlsx|xls|docx|doc|pdf|csv|txt|eml|jpg|jpeg|png|ics|json)\b', re.I)
tasks = sorted({json.load(open(f, encoding='utf-8')).get('task', '').strip() for f in glob.glob('tasks/*/subtasks/*.json')} - {''})
au = dict(instructions=len(tasks), translated=0, with_bengali_digits=0, with_ascii_digits=0, with_both_digit_scripts=0,
          name_mentions=0, name_mentions_kept_latin=0, file_tokens=0, file_tokens_changed=0)
for en in tasks:
    bn = cache.get(en)
    if not bn:
        continue
    au['translated'] += 1
    bd, ad = bool(BN_DIGIT.search(bn)), bool(re.search('[0-9]', bn))
    au['with_bengali_digits'] += bd; au['with_ascii_digits'] += ad; au['with_both_digit_scripts'] += bd and ad
    for nm in NAMES:
        if re.search(r'\b' + nm + r'\b', en):
            au['name_mentions'] += 1; au['name_mentions_kept_latin'] += nm in bn
    for t in FILE_RE.findall(en):
        au['file_tokens'] += 1; au['file_tokens_changed'] += t not in bn
T['translation_audit_officebench'] = au

# ---------------- confound table (from the four reports) and derived shares ----------------
conf = {'C1': 24, 'C2': 35, 'C3': 9, 'C4': 8, 'C5': 22, 'C6': 45, 'C7': 20}
tot = sum(conf.values())
T['confound'] = dict(counts=conf, total=tot,
                     evaluation_side_pct=round(100 * (conf['C2'] + conf['C3'] + conf['C4'] + conf['C5']) / tot, 1),
                     agent_pct=round(100 * (conf['C1'] + conf['C6']) / tot, 1), unclear_pct=round(100 * conf['C7'] / tot, 1),
                     bangla_specific_range_pct=[round(100 * conf['C1'] / tot, 1), round(100 * (conf['C1'] + conf['C7']) / tot, 1),
                                                round(100 * (conf['C1'] + conf['C7'] + conf['C6']) / tot, 1)])

json.dump(T, open('analysis/acl_rewrite_tables.json', 'w', encoding='utf-8'), indent=1, default=list)

# markdown summary
L = ['# Tables for paper_acl/main.tex', '', '## RQ1: seven comparisons (Holm across seven)', '',
     '| bench | model | n | EN | BN | gap | 95% CI | MELR | EN-only | BN-only | p | p_Holm | source |', '|' + '---|' * 13]
for r in rows:
    L.append(f"| {r['bench']} | {r['model']} | {r['n']} | {r['en']} | {r['bn']} | {r['gap']:+.1f} | [{r['ci'][0]}, {r['ci'][1]}] | {r['melr']} | {r['en_only']} | {r['bn_only']} | {r['p']:.4f} | {r['p_holm']:.3f} | {r['source']} |")
L += ['', '## OfficeBench by number of apps (Holm across three, per model)', '']
for m in ob:
    for a, s in ob[m]['by_apps'].items():
        L.append(f"- {m} {a}-app: n={s['n']} EN {s['en']} BN {s['bn']} EN-only {s['en_only']} BN-only {s['bn_only']} p={s['p']:.3f} p_Holm={s['p_holm']:.3f}")
L += ['', '## Model gap on OfficeBench', '', json.dumps(T['ob_model_gap']), '', '## Trajectory measurements (OfficeBench)', '']
for r, d in traj.items():
    L.append(f'- {r}: ' + json.dumps(d))
L += ['', '## Bangla-script final answers among failures', '', json.dumps(ans), '',
      '## Translation audit (instructions used in the Bangla runs)', '', json.dumps(au), '',
      '## Confound shares', '', json.dumps(T['confound'])]
open('analysis/acl_rewrite_tables.md', 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(L))
