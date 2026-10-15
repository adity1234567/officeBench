"""Build analysis/failure_analysis_report.md by running failure_analysis_pipeline.md on OfficeBench (gemma4:31b EN vs BN).

Inputs:  analysis/fa_rows.json (aligned runs), analysis/fa_labels.py (42 trace notes),
         analysis/failure_codes_all_runs.json (earlier per-run codes, used for the both-fail comparison),
         tasks/*/outputs/*/gemma4_31b_{think,bn}/env_history.json (answers for the answer-language cases).
Run:     python analysis/fa_step2_paired.py   (writes fa_rows.json)
         python analysis/fa_report.py
"""
import json, math, os, random, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fa_labels as L
import fa_figs
import fa_results_data as RD

rows = json.load(open(os.path.join(HERE, 'fa_rows.json'), encoding='utf-8'))
codes = json.load(open(os.path.join(HERE, 'failure_codes_all_runs.json'), encoding='utf-8'))
byid = {r['id']: r for r in rows}


# ------------------------------------------------------------------ statistics
def mcnemar(b, c):
    m = b + c
    if not m:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(m, j) for j in range(k + 1)) / 2 ** m)


def wilson(x, n, z=1.96):
    if not n:
        return (float('nan'), float('nan'))
    ph = x / n
    d = 1 + z * z / n
    c0 = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (c0 - h, c0 + h)


def summarize(rs, seed=7, B=4000):
    n = len(rs)
    pp = sum(r['en'] and r['bn'] for r in rs); pf = sum(r['en'] and not r['bn'] for r in rs)
    fp = sum(not r['en'] and r['bn'] for r in rs); ff = n - pp - pf - fp
    se, sb = (pp + pf) / n, (pp + fp) / n
    gap = se - sb
    melr = gap / se if se else float('nan')
    random.seed(seed)
    gs, ms = [], []
    for _ in range(B):
        s = [rs[random.randrange(n)] for _ in range(n)]
        e = sum(x['en'] for x in s) / n; b = sum(x['bn'] for x in s) / n
        gs.append(e - b); ms.append((e - b) / e if e else 0)
    gs.sort(); ms.sort()
    q = lambda a, p: a[min(len(a) - 1, max(0, int(p * len(a))))]
    m = pf + fp
    g = (pf / m - .5) if m else 0.0
    lo, hi = wilson(pf, m) if m else (float('nan'), float('nan'))
    odds = (pf / fp) if fp else float('inf')
    return dict(n=n, pp=pp, pf=pf, fp=fp, ff=ff, en=se, bn=sb, gap=gap, melr=melr, p=mcnemar(pf, fp),
                gap_ci=(q(gs, .025), q(gs, .975)), melr_ci=(q(ms, .025), q(ms, .975)),
                en_ci=wilson(pp + pf, n), bn_ci=wilson(pp + fp, n), g=g, odds=odds,
                odds_ci=((lo / (1 - lo)) if lo == lo and lo < 1 else float('nan'),
                         (hi / (1 - hi)) if hi == hi and hi < 1 else float('inf')))


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


pc = lambda x, d=1: ('%.' + str(d) + 'f%%') % (100 * x)
pp_ = lambda x, d=1: ('%+.' + str(d) + 'f pp') % (100 * x)
fmtp = lambda p: '<0.001' if p < 0.001 else '%.3f' % p

# ------------------------------------------------------------------ cases
def last_answer(tid, sid, tag):
    h = json.load(open(os.path.join(ROOT, 'tasks', tid, 'outputs', sid, tag, 'env_history.json'), encoding='utf-8'))
    for a, o in reversed(h):
        if isinstance(a, dict) and a.get('action') == 'finish_task':
            return str(a.get('answer'))
    return ''


def n_steps(tid, sid, tag):
    return len(json.load(open(os.path.join(ROOT, 'tasks', tid, 'outputs', sid, tag, 'env_history.json'), encoding='utf-8')))


cases = {}
for cid, (goal, kw) in L.AL.items():
    t, s = cid.split('/')
    en_a, bn_a = last_answer(t, s, 'gemma4_31b_think'), last_answer(t, s, 'gemma4_31b_bn')
    extra = ''
    if cid == '1-2/4':
        extra = (' The English pass is itself weak: its answer says both have 5, and the check expects “Tom”, which '
                 'appears only because the sentence names both men (C-WEAKCHECK). Neither answer is right by the check’s intent.')
    if cid == '2-32/0':
        extra = (' The Bangla run read only company_budget.jpg before answering; English read both images. '
                 'The answer is right but the evidence was thinner (premature finish, contributing).')
    cases[cid] = dict(
        goal=goal,
        en='Answer: “%s”' % en_a[:110], bn='Answer: “%s”' % bn_a[:110],
        diverge={'2-32/0': 'Step 4: English OCRs a second image, Bangla answers after the first.',
                 '1-2/3': 'Step 0: Bangla starts in the shell and email apps before reading the calendars.'}.get(cid, 'Final answer step: the answer is written in a different script.'),
        missing='None; the content is right, the script is not.',
        fp=9, ftype=9,
        root='Nothing in the task or the tool text says which language to answer in; the Bangla agent answers in Bangla script and digits and the check searches for the ASCII keyword “%s”.' % kw,
        conf='C5', level='high', exit=0,
        evidence='In %s, English passed with “%s”. In Bangla the agent reached the same content but wrote “%s”, so the keyword “%s” is absent and the check fails.%s' % (cid, en_a[:160], bn_a[:160], kw, extra))
for cid, d in L.LABELS.items():
    cases[cid] = d
assert set(cases) == {r['id'] for r in rows if r['en'] and not r['bn']}, 'label set does not match EN-pass/BN-fail set'

# ------------------------------------------------------------------ section numbers
S = summarize(rows)
grp = {a: summarize([r for r in rows if r['apps'] == a]) for a in (1, 2, 3)}
adj = holm([grp[a]['p'] for a in (1, 2, 3)])
pf_ids = [r['id'] for r in rows if r['en'] and not r['bn']]
fp_ids = [r['id'] for r in rows if not r['en'] and r['bn']]
NPF = len(pf_ids)

cnt = lambda key, f=lambda v: v: collections.Counter(f(cases[i][key]) for i in pf_ids)
c_conf, c_fp, c_ft, c_exit = cnt('conf'), cnt('fp'), cnt('ftype'), cnt('exit')
by_apps_conf = {a: collections.Counter(cases[i]['conf'] for i in pf_ids if byid[i]['apps'] == a) for a in (1, 2, 3)}
by_apps_n = collections.Counter(byid[i]['apps'] for i in pf_ids)
level_c = collections.Counter(cases[i]['level'] for i in pf_ids)

# scenarios
def drop(ids):
    s = set(ids)
    return [r for r in rows if r['id'] not in s]


def flip_bn_pass(ids):
    s = set(ids)
    return [dict(r, bn=True) if r['id'] in s else r for r in rows]


# EN-fail/BN-pass subtasks the earlier report (section 6.3) attributes to English environment traps; taken from that report, not re-verified here
EN_TRAPS = ['2-36/3', '3-89/0', '2-34/0', '2-45/0', '3-70/0', '3-61/0', '2-39/0']
assert all(i in fp_ids for i in EN_TRAPS)
ids_of = lambda *cs: [i for i in pf_ids if cases[i]['conf'] in cs]
SCEN = [
    ('S0  All 300 subtasks (as scored)', rows),
    ('S1  Drop translation-confounded subtasks (C3)', drop(ids_of('C3'))),
    ('S2  Drop user-simulator-confounded subtasks (C2)', rows),
    ('S3  Drop tool/environment-confounded subtasks (C4)', drop(ids_of('C4'))),
    ('S4  Drop answer-language / weak-check subtasks (C5)', drop(ids_of('C5'))),
    ('S5  Drop C3 + C4 + C5', drop(ids_of('C3', 'C4', 'C5'))),
    ('S6  Drop C3 + C4 + C5 + C6 (leave C1 and C7)', drop(ids_of('C3', 'C4', 'C5', 'C6'))),
    ('S7  Credit Bangla answers that are correct but in Bangla script (C5 → BN pass)', flip_bn_pass(ids_of('C5'))),
    ('S8  S7, and drop C3 + C4', [dict(r, bn=True) if r['id'] in set(ids_of('C5')) else r for r in drop(ids_of('C3', 'C4'))]),
    ('S9  S5 made symmetric: also drop the 7 EN-fail/BN-pass subtasks that the earlier analysis traced to English environment traps', drop(ids_of('C3', 'C4', 'C5') + EN_TRAPS)),
]
SC = [(name, summarize(rs)) for name, rs in SCEN]

R = RD.R
FIG_FOREST = fa_figs.forest(SC)
FIG_CONF = fa_figs.confounds(R, L.CONF, by_apps_conf, ['C5', 'C7', 'C1', 'C3', 'C4', 'C6'])
FIG_SUCC = fa_figs.success_by_size(R)
FIG_PAIR = fa_figs.paired(R)
FIG_CAUSE = fa_figs.causes(R)
FIG_PAT = fa_figs.patterns(R)
FIGN = {'pair_go': 5, 'sig': 6, 'conf_go': 13, 'forest_go': 14}   # figure numbers used by Part II
exec(compile(open(os.path.join(HERE, 'fa_p2_calc.py'), encoding='utf-8').read(), 'fa_p2_calc.py', 'exec'))

# both-fail and EN-fail/BN-pass comparison from the earlier per-run codes
CN = {'BM': 'Benchmark defect', 'WC': 'Wrong content', 'SB': 'Out of steps', 'TL': 'Cut-off output loop',
      'ER': 'Empty result, gave up', 'TR': 'Task read differently', 'PF': 'Premature finish', 'CAP': 'Capability claim',
      'FMT': 'Action format', 'DL': 'Deliberation loop', 'AL': 'Answer language', 'NC': 'Name case',
      'WD': 'Word choice', 'TX': 'Translation', 'OTH': 'Other', 'INF': 'Infrastructure'}
ff_ids = [r['id'] for r in rows if not r['en'] and not r['bn']]
ff_bn = collections.Counter(byid[i]['cat_bn'] for i in ff_ids)
pf_bn = collections.Counter(byid[i]['cat_bn'] for i in pf_ids)
ff_same = sum(1 for i in ff_ids if byid[i]['cat_en'] == byid[i]['cat_bn'])
ff_apps = collections.Counter(byid[i]['apps'] for i in ff_ids)
pp_ids = [r['id'] for r in rows if r['en'] and r['bn']]
pp_apps = collections.Counter(byid[i]['apps'] for i in pp_ids)
fp_apps = collections.Counter(byid[i]['apps'] for i in fp_ids)

random.seed(11)
blind = sorted(random.sample(pf_ids, 12), key=lambda s: (int(s.split('-')[0]), int(s.split('-')[1].split('/')[0]), int(s.split('/')[1])))

# ------------------------------------------------------------------ rendering
o = []
w = o.append


def table(head, body, align=None):
    w('| ' + ' | '.join(head) + ' |')
    w('|' + '|'.join((':---' if (align and align[i] == 'l') or (not align and i == 0) else '---:') for i in range(len(head))) + '|')
    for r in body:
        w('| ' + ' | '.join(str(x) for x in r) + ' |')
    w('')


def dist_table(counter, labels, total, first='Label'):
    body = []
    for k, lab in labels:
        if counter.get(k, 0):
            body.append([lab, counter[k], pc(counter[k] / total)])
    table([first, 'Cases', 'Share of %d' % total], body, 'lrr')


w('# OfficeBench failure analysis: English vs Bangla (gemma4:31b and gpt-oss:20b)')
w('')
w('*Generated by `analysis/fa_report.py` on 2026-10-10, following `failure_analysis_pipeline.md` step by step. '
  'Every number below is computed from the aligned runs and the trace notes in `analysis/fa_labels.py` (42 gemma cases) and `analysis/fa_labels_gptoss.py` (25 gpt-oss cases).*')
w('')
w('## Summary of results')
w('')
w('- **gemma4:31b is worse in Bangla.** %s in English against %s in Bangla (gap %s, 95%% interval [%.1f, %.1f] pp, McNemar p = %s). Of the %d English-pass/Bangla-fail subtasks, %d are answer-language or checker artefacts, %d come from the translated prompt, %d are tool or harness failures, %d are genuine Bangla agent failures and %d are unclear or also occur in English. '
  'With the confounded cases removed on both sides the gap is %s and its interval includes zero.'
  % (pc(S['en']), pc(S['bn']), pp_(S['gap']), 100 * S['gap_ci'][0], 100 * S['gap_ci'][1], fmtp(S['p']), NPF, c_conf['C5'], c_conf['C3'], c_conf['C4'], c_conf['C1'], c_conf['C6'] + c_conf['C7'], pp_(SC[9][1]['gap'])))
w('- **gpt-oss:20b is better in Bangla.** %s in English against %s in Bangla (gap %s, 95%% interval [%.1f, %.1f] pp, McNemar p = %s): %d subtasks pass only in Bangla against %d only in English. '
  '%d of those %d Bangla-only passes are English runs that failed on the benchmark\u2019s action format, and the Bangla prompt cuts invalid actions from %d to %d.'
  % (pc(SG['en']), pc(SG['bn']), pp_(SG['gap']), 100 * SG['gap_ci'][0], 100 * SG['gap_ci'][1], fmtp(SG['p']), SG['fp'], SG['pf'], fp_codes['FMT'], NFG,
     sum(v['malformed'] for v in SIGS['GO'].values()), sum(v['malformed'] for v in SIGS['GB'].values())))
w('- **The two models differ by %s** (95%% interval [%.1f, %.1f] pp): a Bangla prompt hurts one and helps the other on this benchmark, so a single \u201cBangla is worse\u201d claim does not hold across models.'
  % (pp_(DID), 100 * DID_CI[0], 100 * DID_CI[1]))
w('- **One genuine Bangla mechanism appears in both models:** a name written only in Bangla script is lower-cased for a case-sensitive lookup, the lookup returns nothing and the run ends (3 gemma cases, 6 gpt-oss cases).')
w('- **The benchmark itself decides many results.** A benchmark defect decides at least one of the three runs with full root-cause coding on %d subtasks; the checker reads only English answers.' % R['bm_any'])
w('- **Limits.** One run per cell at temperature 0; one annotator and no second reviewer; gpt-oss Bangla failures beyond the first 51 subtasks are not root-cause coded.')
w('')

w('## 0. Scope and how the pipeline was adapted')
w('')
w('The pipeline file was written for tau2-style dialogue benchmarks. This report applies it to the data in this repository: '
  '**OfficeBench, 300 subtasks, two models (gemma4:31b and gpt-oss:20b), one English run and one Bangla run of each per subtask**, '
  'temperature 0. Sections 1\u201315 analyse gemma4:31b (`gemma4_31b_think`, `gemma4_31b_bn`); Part II analyses gpt-oss:20b (`gpt-oss_20b_en`, `gpt-oss_20b_bn`). Pass/fail is the corrected score from `analysis/failure_codes_all_runs.json` (email check, mailbox matching and UTF-8 fixes applied).')
w('')
table(['Pipeline item', 'In this report'], [
    ['Dataset', 'One: OfficeBench. Dataset-wise distribution is therefore replaced by app-count (single-, two-, three-app).'],
    ['Model', 'Two models, each with a complete English and Bangla run: gemma4:31b (Sections 1\u201315) and gpt-oss:20b (Part II).'],
    ['Domain', 'Domain = number of apps a subtask uses (1, 2, 3).'],
    ['“Bangla user simulator”', 'Not applicable: OfficeBench has no simulated user. Confound C2 is kept in the tables and is zero by construction. The role it plays in tau2 (a translated component producing wrong task content) is covered by C3, translation.'],
    ['“Dialogue-state failure”', 'Not applicable (single-turn tasks). Kept in the taxonomy, zero cases.'],
    ['Failure taxonomy', 'Section 6 list used as written, plus two types added because 17 cases did not fit: **Output-language mismatch** and **Reasoning on observed data**.'],
    ['Decision tree', 'Section 8 used as written, with a **Step 0 added** in front: “is the output already correct for the task as written?”. Without it, 15 correct Bangla answers have no exit.'],
    ['Second reviewer', '**Not done.** All 42 gemma notes and all 25 gpt-oss notes are by one annotator. Sections 14 and II.12 list blind subsets for a second reviewer.'],
], 'll')



# ------------------------------------------------------------------ R results of all runs
def fig(cap, path, wide=False):
    w('![%s](%s%s)' % (cap, path, ' "wide"' if wide else ''))
    w('')


w('## R. Results of all runs')
w('')
w('Four runs are compared, each on all 300 subtasks: gemma4:31b and gpt-oss:20b, each with an English and a Bangla prompt. '
  'All scores are the corrected ones. The gpt-oss Bangla run finished after the first draft of this analysis and was rescored with `analysis/fa_rescore.py` (Part II). '
  'The paired failure analysis in Sections 1–15 covers gemma; Part II covers gpt-oss.')
w('')


def rr(k, a):
    p_, n_ = R['rate'][k][a]
    return '%d / %d (%s)' % (p_, n_, pc(p_ / n_)) if n_ else '–'


table(['Run', 'Model', 'Prompt', 'Subtasks', 'All', 'Single-app', 'Two-app', 'Three-app'],
      [[k, m, l, R['n'][k], rr(k, None), rr(k, 1), rr(k, 2), rr(k, 3)] for k, m, l in RD.RUNS], 'lllrrrrr')
w('### R.1 The study in two figures')
w('')
fig('Figure 1. The pipeline, step by step: what each step does, how, and what it hands to the next.', 'figures/fig_steps.svg', True)
fig('Figure 2. How the study works: the four cells, one 20-step run in the container, and the scoring with three repaired defects.', 'figures/fig1_study_design.svg', True)
w('### R.2 Success rate by run and task size')
w('')
fig('Figure 3. Success rate of the four runs by number of apps in the subtask.', FIG_SUCC)
w('- gemma4:31b passes **%s** in English and **%s** in Bangla; gpt-oss:20b passes **%s** in English and **%s** in Bangla.'
  % (pc(R['rate']['EN'][None][0] / 300), pc(R['rate']['BN'][None][0] / 300), pc(R['rate']['GO'][None][0] / 300), pc(R['rate']['GB'][None][0] / 300)))
w('- **The two models move in opposite directions.** gemma is lower in Bangla (%s), gpt-oss is higher in Bangla (%s), and the models differ by %s (95%% interval [%.1f, %.1f] pp).'
  % (pp_(S['gap']), pp_(SG['gap']), pp_(DID), 100 * DID_CI[0], 100 * DID_CI[1]))
w('- Every run falls sharply with task size: gemma English from %s on single-app to %s on three-app; gpt-oss English from %s to %s.'
  % (pc(R['rate']['EN'][1][0] / 93), pc(R['rate']['EN'][3][0] / 112), pc(R['rate']['GO'][1][0] / 93), pc(R['rate']['GO'][3][0] / 112)))
w('- The English–Bangla gap of gemma sits in single-app (%s) and two-app (%s) tasks; on three-app tasks both languages pass the same %d of 112.'
  % (pp_(R['rate']['EN'][1][0] / 93 - R['rate']['BN'][1][0] / 93), pp_(R['rate']['EN'][2][0] / 95 - R['rate']['BN'][2][0] / 95), R['rate']['EN'][3][0]))
w('')
w('### R.3 gemma4:31b, English against Bangla, subtask by subtask')
w('')
fig('Figure 4. Paired outcome of gemma4:31b English and Bangla on the same subtasks.', FIG_PAIR)
w('- %d subtasks pass only in English and %d only in Bangla. The English-only group is the one analysed case by case in Sections 4–12.' % (S['pf'], S['fp']))
w('- On three-app tasks the two directions are equal (%d and %d), so there is no net gap even though %d subtasks change outcome.' % (grp[3]['pf'], grp[3]['fp'], grp[3]['pf'] + grp[3]['fp']))
w('')
w('### R.4 gpt-oss:20b, English against Bangla, subtask by subtask')
w('')
fig('Figure 5. Paired outcome of gpt-oss:20b English and Bangla on the same subtasks.', FIG_PAIR_GO)
w('- %d subtasks pass only in English and **%d only in Bangla**, the opposite balance to gemma. The Bangla-only group is the larger one at every task size (%d against %d single-app, %d against %d two-app, %d against %d three-app).'
  % (SG['pf'], SG['fp'], grp_go[1]['fp'], grp_go[1]['pf'], grp_go[2]['fp'], grp_go[2]['pf'], grp_go[3]['fp'], grp_go[3]['pf']))
w('- The Bangla prompt removes much of gpt-oss’s trouble with the benchmark’s action format (Figure 6): invalid actions fall from %d to %d, calls to its own built-in tools from %d to %d, stuck runs from %d to %d, and finished runs rise from %d to %d.'
  % (sum(v['malformed'] for v in SIGS['GO'].values()), sum(v['malformed'] for v in SIGS['GB'].values()),
     sum(v['builtin'] for v in SIGS['GO'].values()), sum(v['builtin'] for v in SIGS['GB'].values()),
     sum(v['end'] == 'stuck' for v in SIGS['GO'].values()), sum(v['end'] == 'stuck' for v in SIGS['GB'].values()),
     sum(v['end'] == 'finish' for v in SIGS['GO'].values()), sum(v['end'] == 'finish' for v in SIGS['GB'].values())))
w('')
fig('Figure 6. gpt-oss:20b English against Bangla: invalid actions, built-in tool calls and how runs end.', FIG_SIG)
w('### R.5 Why runs fail')
w('')
fig('Figure 7. Primary root cause of every failed run, for the three runs with full root-cause coding, grouped into six families.', FIG_CAUSE)


def fam(k, codes):
    return sum(R['cat'][k].get(c, 0) for c in codes)


tot = {k: sum(R['cat'][k].values()) for k in R['cat']}
NOACT = ('ER', 'PF', 'CAP', 'FMT')
LANG = ('AL', 'NC', 'WD', 'TX')
w('- **Benchmark defects** are the largest single cause for gemma (%s of English failures, %s of Bangla) and still %s of gpt-oss English failures.'
  % (pc(fam('EN', ('BM',)) / tot['EN']), pc(fam('BN', ('BM',)) / tot['BN']), pc(fam('GO', ('BM',)) / tot['GO'])))
w('- **gpt-oss English** fails mostly by not producing a valid action: %d of %d failures (%s) are coded no valid action or gave up, %d of them action-format failures.'
  % (fam('GO', NOACT), tot['GO'], pc(fam('GO', NOACT) / tot['GO']), R['cat']['GO']['FMT']))
w('- **Bangla-specific causes** (answer script, name case, word choice, translation) are %d of gemma’s %d Bangla failures (%s); the rest also occur in English.'
  % (fam('BN', LANG), tot['BN'], pc(fam('BN', LANG) / tot['BN'])))
w('- gpt-oss Bangla has root-cause codes only for the %d failures among its first 51 subtasks, so it is left out of Figure 7; its 25 EN-pass/BN-fail cases are analysed by hand in Part II.' % tot['GB'])
w('')
w('### R.6 What fails everywhere')
w('')
fig('Figure 8. How the four runs agree on each subtask.', FIG_PAT)
w('- **%d** subtasks fail in all four runs and **%d** pass in all four.' % (R['fail_all4'], R['pass_all4']))
w('- Using the three runs that have root-cause codes for every failure: **%d** subtasks fail in all three, **%d** of them for the identical coded cause, and a benchmark defect decides at least one of the three runs on **%d** subtasks, which makes fixing the benchmark the most direct way to raise every score.'
  % (R['fail_all'], R['fail_all_same'], R['bm_any']))
w('')
w('### R.7 Pilot runs')
w('')
w('Earlier, smaller runs, taken from the long failure report (not recomputed here: the result files for these runs are padded with fails for subtasks that were never run).')
w('')
table(['Run tags', 'Model', 'Written reasoning', 'Subtasks run', 'Passed'],
      [['gemma4_31b_first10, next20, probe, rest, gemmatest', 'gemma4:31b', 'no', 91, 61],
       ['qwen2.5-7b_test, batch10', 'qwen2.5-7b', 'no', 12, 3]], 'lllrr')
w('Writing the reasoning before each action barely helped gemma on single-app tasks (58 against 60 of 87). Seven of the twelve Qwen2.5-7B runs ended stuck after repeated malformed actions.')
w('')

# ------------------------------------------------------------------ 1
w('## 1. Data prepared (pipeline section 1)')
w('')
w('Every subtask has one row. Alignment check: **300 of 300 task IDs appear in both runs; none are English-only or Bangla-only.**')
w('')
table(['Field', 'Where it comes from'], [
    ['dataset, model, task ID, run ID', 'OfficeBench / gemma4:31b / `task/subtask` (e.g. `1-2/0`) / `gemma4_31b_think`, `gemma4_31b_bn`'],
    ['English and Bangla pass/fail', '`analysis/failure_codes_all_runs.json` → `pass.EN`, `pass.BN` (saved as `analysis/fa_rows.json`)'],
    ['Trajectory paths', '`tasks/<t>/outputs/<s>/gemma4_31b_{think,bn}/env_history.json` (actions and observations), `llm_history.json` (prompts and thoughts)'],
    ['Final state', '`.../gemma4_31b_{think,bn}/testbed/` (files after the run)'],
    ['Task metadata', '`tasks/<t>/subtasks/<s>.json` (task text and the evaluation functions)'],
    ['Tool calls, arguments, results, final answer', 'inside `env_history.json` as (action, observation) pairs'],
], 'll')

# ------------------------------------------------------------------ 2
w('## 2. Basic outcome (pipeline section 2)')
w('')
head = ['Setting', 'n', 'EN pass', 'BN pass', 'Gap (EN−BN)', 'MELR', 'PP', '**PF**', 'FP', 'FF']
body = []
for name, s in [('Overall', S), ('Single-app', grp[1]), ('Two-app', grp[2]), ('Three-app', grp[3])]:
    body.append([name, s['n'], '%d (%s)' % (s['pp'] + s['pf'], pc(s['en'])), '%d (%s)' % (s['pp'] + s['fp'], pc(s['bn'])),
                 pp_(s['gap']), pc(s['melr']), s['pp'], '**%d**' % s['pf'], s['fp'], s['ff']])
table(head, body, 'lrrrrrrrrr')
w('MELR = (EN − BN) / EN. PP = EN-pass/BN-pass, **PF = EN-pass/BN-fail**, FP = EN-fail/BN-pass, FF = EN-fail/BN-fail. '
  'Denominator is the number of aligned subtasks in the row.')
w('')
w('**%d subtasks are EN-pass/BN-fail**, %d are EN-fail/BN-pass. The gap is entirely in short tasks: on three-app tasks both languages pass %d of %d (%s), on single-app tasks the gap is %s.'
  % (S['pf'], S['fp'], grp[3]['pp'] + grp[3]['pf'], grp[3]['n'], pc(grp[3]['en']), pp_(grp[1]['gap'])))
w('')

# ------------------------------------------------------------------ 3
w('## 3. Which cases were analysed (pipeline section 3)')
w('')
table(['Group', 'Count', 'How analysed here'], [
    ['EN-pass / BN-fail', S['pf'], '**All %d** read trace-against-trace and labelled (Section 4 and Appendix A).' % S['pf']],
    ['EN-fail / BN-fail', S['ff'], 'Not re-read. Compared through the earlier per-run root-cause codes for all %d (Appendix B), as the general-difficulty baseline.' % S['ff']],
    ['EN-pass / BN-pass', S['pp'], 'Counted by app size only (stable-success profile, Appendix B).'],
    ['EN-fail / BN-pass', S['fp'], 'Not labelled here. The earlier analysis already traced all %d (7 English traps, 7 shorter Bangla reasoning, 4 other); see `analysis/full_failure_report_pdf.py`, section 6.3.' % S['fp']],
], 'lrl')

# ------------------------------------------------------------------ 4
w('## 4. Trace notes (pipeline section 4)')
w('')
w('The failure analysis follows one procedure for every failed run (Figure 9 shows it on a real subtask; Figure 10 is the coding scheme).')
w('')
w('One note per EN-pass/BN-fail case, with the nine fields the pipeline asks for. The 42 notes are in Appendix A in the pipeline’s field order. '
  'Two worked examples show the level of detail.')
w('')
for cid in ('3-56/0', '1-15/0'):
    d = cases[cid]
    w('**%s**' % cid)
    w('')
    w('- Task goal: %s' % d['goal'])
    w('- English: %s' % d['en'])
    w('- Bangla: %s' % d['bn'])
    w('- First divergence: %s' % d['diverge'])
    w('- Final failed or missing action: %s' % d['missing'])
    w('- Failure type: %s' % L.FT[d['ftype']])
    w('- Root cause: %s' % d['root'])
    w('- Confound decision: %s (%s confidence)' % (L.CONF[d['conf']], d['level']))
    w('- Evidence: %s' % d['evidence'])
    w('')

fig('Figure 9. One real subtask carried through the pipeline: the answer is right, two of four checks demand an event the task never asks for.', 'figures/fig0_teaser.svg', True)
fig('Figure 10. How failures are characterized: one question, one primary code, contributing tags.', 'figures/fig2_failure_coding.svg', True)

# ------------------------------------------------------------------ 5
w('## 5. First failure point (pipeline section 5)')
w('')
w('Rule applied: label the earliest upstream point, not the visible final error. For the answer-language cases the earliest point is the final response itself, because every earlier step matches English.')
w('')
dist_table(c_fp, [(i, L.FP[i]) for i in range(len(L.FP))], NPF, 'First failure point')
w('Reading the table: %d of %d cases (%s) have **no error before the final response**. Among the other %d, the earliest breaks are '
  'tool arguments (%d), planning (%d), instruction understanding (%d) and entity grounding (%d).'
  % (c_fp[9], NPF, pc(c_fp[9] / NPF), NPF - c_fp[9], c_fp[5], c_fp[3], c_fp[0], c_fp[1]))
w('')

# ------------------------------------------------------------------ 6
w('## 6. Failure type (pipeline section 6)')
w('')
dist_table(c_ft, [(i, L.FT[i]) for i in range(len(L.FT))], NPF, 'Failure type')
w('The special cases listed in the pipeline map as follows: *premature STOP before the final tool call* → no equivalent (no simulated user); '
  '*internal ID used as a name* → closest is the lower-cased mailbox name (Wrong tool argument, 3); '
  '*changed task constraint* → the dropped column (1-11/0), the filtered roster (2-20/0) and four translation-driven misreadings (Understanding, 6 in all), plus the wrong calendar owner (2-17/0, Wrong tool argument); '
  '*compound task partially completed* → 3-15/0 (image skipped) and the two three-app step-budget cases.')
w('')

# ------------------------------------------------------------------ 7
w('## 7. Confound type (pipeline section 7)')
w('')
dist_table(c_conf, [(k, '%s  %s' % (k, v)) for k, v in L.CONF.items()], NPF, 'Confound')
fig('Figure 11. Confound class of the 42 EN-pass/BN-fail cases, split by number of apps.', FIG_CONF)
w('Confidence of the annotator on the confound label: high %d, medium %d, low %d.'
  % (level_c['high'], level_c['medium'], level_c['low']))
w('')
w('By app count:')
w('')
table(['Confound'] + ['%d-app (n=%d)' % (a, by_apps_n[a]) for a in (1, 2, 3)],
      [['%s  %s' % (k, v)] + [by_apps_conf[a].get(k, 0) for a in (1, 2, 3)] for k, v in L.CONF.items()], 'lrrr')

# ------------------------------------------------------------------ 8
w('## 8. Root-cause decision tree (pipeline section 8)')
w('')
w('Each EN-pass/BN-fail case leaves the tree at the first step that fires. Counts of exits:')
w('')
table(['Exit step', 'Cases', 'Root cause assigned'],
      [[L.EXIT[k], c_exit.get(k, 0), {
          0: 'Output already correct; check is English-only or weak (C5)',
          1: 'Translation/localization error (C3)',
          2: '— (no user simulator)',
          3: 'Understanding or grounding failure (C1 where mechanism is shown, otherwise C6/C7)',
          4: '— (no wrong-tool case found)',
          5: 'Wrong tool argument (C1)',
          6: 'Tool/environment (C4) or shared cap failure (C6)',
          7: 'Verification / abandonment (C7)'}[k]] for k in range(8)], 'lrl')
w('No case exits at Step 4: in every EN-pass/BN-fail case the Bangla agent selected an app and action that exists and that English also used or could have used.')
w('')

# ------------------------------------------------------------------ 9
w('## 9. Evidence for each root cause (pipeline section 9)')
w('')
w('Each of the 42 cases carries the six required items: English outcome, Bangla outcome, first failure point, the action or message that shows it, why it is not simply a general model failure, and the confound label. '
  'They are in Appendix A. The “why not general” item is the *Root cause* line plus the check against the English run; it is explicitly weak for the %d C6 and %d C7 cases, which is why they sit outside the lower bound on genuine Bangla effects.'
  % (c_conf['C6'], c_conf['C7']))
w('')

# ------------------------------------------------------------------ 10
w('## 10. Counts (pipeline section 10)')
w('')
w('Items 1–3 are in Sections 5–7. The remaining items:')
w('')
gen = c_conf['C1']
table(['Count', 'Cases', 'Share of %d' % NPF], [
    ['Genuine Bangla-related agent failures (C1), after filtering', gen, pc(gen / NPF)],
    ['Bangla user-simulator-caused (C2)', c_conf['C2'], pc(c_conf['C2'] / NPF)],
    ['Translation-caused (C3)', c_conf['C3'], pc(c_conf['C3'] / NPF)],
    ['Tool/environment-caused (C4)', c_conf['C4'], pc(c_conf['C4'] / NPF)],
    ['Answer-language / weak-check (C5)', c_conf['C5'], pc(c_conf['C5'] / NPF)],
    ['General weakness present in both (C6)', c_conf['C6'], pc(c_conf['C6'] / NPF)],
    ['Unclear, candidates for genuine failure (C7)', c_conf['C7'], pc(c_conf['C7'] / NPF)],
], 'lrr')
w('Dataset-wise: single dataset. Model-wise: single model. Domain-wise (app count) is in the Section 7 table: %d single-app, %d two-app, %d three-app cases.'
  % (by_apps_n[1], by_apps_n[2], by_apps_n[3]))
w('')
w('The upper bound on genuine Bangla effects is C1 + C7 = %d cases (%s of %d); the lower bound is C1 = %d (%s).'
  % (gen + c_conf['C7'], pc((gen + c_conf['C7']) / NPF), NPF, gen, pc(gen / NPF)))
w('')

# ------------------------------------------------------------------ 11
w('## 11. Statistical analysis (pipeline section 11)')
w('')
w('Paired design: same 300 subtasks in both languages. McNemar exact two-sided test on discordant pairs; 95% intervals: Wilson for proportions, '
  'paired bootstrap (4000 resamples of subtasks, seed 7) for the gap and MELR. Effect size: Cohen’s *g* = b/(b+c) − 0.5 on discordant pairs (conventions: 0.05 small, 0.15 medium, 0.25 large) and the discordant odds ratio b/c.')
w('')
body = []
for name, s in [('Overall', S), ('Single-app', grp[1]), ('Two-app', grp[2]), ('Three-app', grp[3])]:
    body.append([name, '%s [%s, %s]' % (pc(s['en']), pc(s['en_ci'][0]), pc(s['en_ci'][1])),
                 '%s [%s, %s]' % (pc(s['bn']), pc(s['bn_ci'][0]), pc(s['bn_ci'][1])),
                 '%s [%s, %s]' % (pp_(s['gap']), '%.1f' % (100 * s['gap_ci'][0]), '%.1f' % (100 * s['gap_ci'][1])),
                 '%s [%s, %s]' % (pc(s['melr']), '%.1f' % (100 * s['melr_ci'][0]), '%.1f' % (100 * s['melr_ci'][1]))])
table(['Setting', 'EN success [95% CI]', 'BN success [95% CI]', 'Gap [95% CI, pp]', 'MELR [95% CI, %]'], body, 'lrrrr')
body = []
for k, a in enumerate((1, 2, 3)):
    s = grp[a]
    body.append(['%d-app' % a, '%d / %d' % (s['pf'], s['fp']), fmtp(s['p']), fmtp(adj[k]),
                 '%.2f' % s['g'], ('%.1f' % s['odds']) if s['odds'] != float('inf') else '∞'])
body.append(['**Overall (not in Holm family)**', '%d / %d' % (S['pf'], S['fp']), fmtp(S['p']), '—', '%.2f' % S['g'], '%.1f' % S['odds']])
table(['Setting', 'b / c (PF / FP)', 'McNemar p', 'Holm-adjusted p', 'Cohen’s g', 'Odds b/c'], body, 'lrrrrr')
w('Holm is applied across the three app-count subgroup tests. The overall test is a single pre-specified comparison and is reported unadjusted. '
  'The overall gap is %s with a 95%% interval of [%.1f, %.1f] pp (MELR %s, interval [%.1f, %.1f]%%), g = %.2f (between the medium and large conventions). The single-app gap is significant after Holm (adjusted p = %s); the two-app gap is not (adjusted p = %s); the three-app gap is exactly zero.'
  % (pp_(S['gap']), 100 * S['gap_ci'][0], 100 * S['gap_ci'][1], pc(S['melr']), 100 * S['melr_ci'][0], 100 * S['melr_ci'][1], S['g'], fmtp(adj[0]), fmtp(adj[1])))
w('')
w('### Sensitivity analysis')
w('')
w('Scenarios remove confounded subtasks from the whole sample (both languages), or credit the Bangla run for answers that are right but written in Bangla script. S2 equals S0 because there is no user simulator.')
w('')
body = []
for name, s in SC:
    body.append([name, s['n'], pc(s['en']), pc(s['bn']), pp_(s['gap']),
                 '[%.1f, %.1f]' % (100 * s['gap_ci'][0], 100 * s['gap_ci'][1]), pc(s['melr']), '%d / %d' % (s['pf'], s['fp']), fmtp(s['p'])])
table(['Scenario', 'n', 'EN', 'BN', 'Gap', 'Gap 95% CI (pp)', 'MELR', 'PF / FP', 'McNemar p'], body, 'lrrrrrrrr')
fig('Figure 12. English minus Bangla gap with 95% interval under each sensitivity scenario. Amber intervals exclude zero.', FIG_FOREST)
s0, s5, s7, s8, s9 = SC[0][1], SC[5][1], SC[7][1], SC[8][1], SC[9][1]
zero_in = lambda x: x['gap_ci'][0] <= 0 <= x['gap_ci'][1]
w('How to read this. Removing the %d C3, C4 and C5 subtasks (S5) takes the gap from %s to %s (p = %s); crediting the Bangla answers that are correct in content (S7) takes it to %s (p = %s). '
  'Two cautions apply.'
  % (c_conf['C3'] + c_conf['C4'] + c_conf['C5'], pp_(s0['gap']), pp_(s5['gap']), fmtp(s5['p']), pp_(s7['gap']), fmtp(s7['p'])))
w('')
w('1. **S1–S6 are asymmetric.** Every confounded subtask identified in this report is an EN-pass/BN-fail case, so dropping them lowers the gap mechanically. '
  'The EN-fail/BN-pass side was not audited with the same care. S9 applies the same treatment to the 7 subtasks that the earlier analysis (section 6.3 of the long report) traced to English environment traps: '
  'the gap is %s (95%% interval [%.1f, %.1f] pp, p = %s)%s. Four more EN-fail/BN-pass subtasks were attributed to translation helping the Bangla run; their IDs are not recorded, so they could not be removed, and the true symmetric gap is a little smaller still.'
  % (pp_(s9['gap']), 100 * s9['gap_ci'][0], 100 * s9['gap_ci'][1], fmtp(s9['p']), ', and the interval includes zero' if zero_in(s9) else ', and the interval excludes zero'))
w('')
w('2. **S7 is conservative.** Three further Bangla answers are correct in content but sit in subtasks that English fails (1-22/2, 1-22/3, 1-22/4), so they are not in the EN-pass/BN-fail set and S7 does not credit them.')
w('')
w('What can be said: the measured overall gap is of the size that the identified confounds (checker language, translation, harness) can account for; what is left after filtering is %d C1 cases, %d C6 cases and %d C7 cases, '
  'too few to establish a Bangla-specific cost with one run per cell. That is a statement about this evidence, not proof that Bangla has no cost.'
  % (c_conf['C1'], c_conf['C6'], c_conf['C7']))
w('')

# ------------------------------------------------------------------ 12
w('## 12. Findings (pipeline section 12)')
w('')
w('Each finding gives observation, evidence, root cause and boundary. These findings are for gemma4:31b; the gpt-oss findings are in Section II.11.')
w('')
al_n, tx_n = c_conf['C5'], c_conf['C3']
w('**F1. The largest single driver of the English–Bangla gap is that the checker only reads English.** '
  'We find that answer-language mismatch accounts for %d of %d EN-pass/BN-fail cases (%s). In every one the Bangla answer has the same content as the English answer '
  'but is written the answer in Bangla script or Bangla digits (e.g. 1-10/0 “৪০” for 40; 2-31/0 “$২০,০০০” for $20,000), and the check searches for an ASCII keyword. '
  'Nothing in the task or the tool text names an answer language, so the first failure point is the final response. Crediting these answers moves the gap from %s to %s. '
  '*Boundary:* the claim concerns the benchmark’s scoring, not the agent’s capability; one of the %d (1-2/4) is also a weak English pass, so its true English status is uncertain.'
  % (al_n, NPF, pc(al_n / NPF), pp_(s0['gap']), pp_(s7['gap']), al_n))
w('')
w('**F2. A further %d cases (%s) trace to the translated prompt itself.** '
  'The translation changed the task in five ways: it translated a quoted literal (3-56/0 wrote the homework sentence in Bangla), turned “sum” into a verb that also means “add” (3-68/0 wrote two totals, not 1494.97), '
  'presented files to be created as existing ones through the definite marker (2-38/2, 3-17/0), read “make a post reward.jpg” as “make a post *for* reward.jpg” (3-55/0), and applied “except sleeping” to the nap as well (2-40/2). '
  'These are first-failure points in instruction understanding or constraint preservation, upstream of any agent error. '
  '*Boundary:* the Bangla task was machine-translated by the same model family; a human-checked translation could remove them, and would be the cleanest test of how many remain.'
  % (tx_n, pc(tx_n / NPF)))
w('')
w('**F3. Cases that look like genuine Bangla agent failures are few and share one mechanism: rendering an English value from a Bangla prompt.** '
  'After filtering F1, F2 and the harness cases, %d cases (%s) remain that we label genuine. Three change a literal English word or format when writing it (“Trip” for “travelling”, “curd” for “yogurt”, “08:00 AM” for “8:00”) and three look up a mailbox with a lower-cased name (1-20/3, 1-21/1, 1-21/2), '
  'because a name written only in Bangla script has no letter case and the lookup is case-sensitive. '
  'The first failure point is tool-argument construction or entity grounding, not understanding. *Boundary:* each is one run; %d further cases (C7) have no visible mechanism and could be genuine.'
  % (gen, pc(gen / NPF), c_conf['C7']))
w('')
w('**F4. Harness and tool behaviour decide %d cases (%s), independent of language.** '
  'Two runs ended on empty model replies (2-1/0, 2-1/1); 3-9/0 lost two steps to an apostrophe that breaks the shell-invoked llm app; and in 1-15/0 and 1-15/1 the Bangla agent resent the whole document because the word tool is described only as “write text to a word file” (it appends), then every long action was cut off by the reply cap. '
  'The English runs passed by taking the short route in the same environment. *Boundary:* a Bangla-triggered empty generation cannot be ruled out for the two empty-reply runs, and the Bangla agent’s plan was a reasonable reading of an under-specified tool.'
  % (c_conf['C4'], pc(c_conf['C4'] / NPF)))
w('')
w('**F5. The gap is a short-task effect.** '
  'It is %s on single-app tasks (Holm-adjusted p = %s), %s on two-app tasks (adjusted p = %s) and %s on three-app tasks, where both languages pass only %s. '
  'Three-app tasks fail for the same reasons in both languages (step budget, cut-off writes, benchmark defects), which hides any language effect. '
  '%d of the %d C5 cases are single- or two-app, because question-answering tasks are short. *Boundary:* the three-app result is a statement about task difficulty, not evidence that Bangla is as good as English on hard tasks.'
  % (pp_(grp[1]['gap']), fmtp(adj[0]), pp_(grp[2]['gap']), fmtp(adj[1]), pp_(grp[3]['gap']), pc(grp[3]['en']),
     sum(1 for i in pf_ids if cases[i]['conf'] == 'C5' and byid[i]['apps'] < 3), c_conf['C5']))
w('')
w('**F6. Most Bangla failures are not Bangla failures.** '
  'Of the %d EN-fail/BN-fail subtasks, %d (%s) carry the same earlier root-cause code in both languages (Appendix B), and the dominant causes in the two groups differ: the EN-pass/BN-fail set is dominated by '
  'output-language and translation effects, the both-fail set by benchmark defects, wrong content and step budget. '
  '*Boundary:* the both-fail codes come from the earlier per-run classification, not from the case notes in this report.'
  % (S['ff'], ff_same, pc(ff_same / S['ff'])))
w('')
w('**Not claimed.** The data do not support “Bangla agents reason worse”: no EN-pass/BN-fail case has a wrong number, date or path that the trace ties to reading Bangla. The 2-32/1 and 3-87/0 errors (wrong comparison, miscount) occur on identical OCR input and may be sampling variation at one run per cell.')
w('')

# ------------------------------------------------------------------ 13
w('## 13. Paper outputs (pipeline section 13)')
w('')
table(['#', 'Output', 'Status', 'Where'], [
    [1, 'Overall English vs Bangla success table', 'Done', 'Section 2, Section 11'],
    [2, 'MELR by dataset and model', 'Done for the one available dataset/model; by app count', 'Section 2, Section 11'],
    [3, 'Paired outcome table', 'Done', 'Section 2 (PP / PF / FP / FF)'],
    [4, 'Failure-type distribution for PF', 'Done', 'Section 6'],
    [5, 'First-failure-point distribution', 'Done', 'Section 5'],
    [6, 'Confound filtering table', 'Done', 'Section 7, Section 10'],
    [7, 'Before/after confound-filtered results', 'Done', 'Section 11, sensitivity table'],
    [8, 'Two or three short case studies', 'Drafted below (Section 15)', 'Section 15'],
    [9, 'Appendix with annotation rules and long trajectories', 'Rules and 42 notes done; long trajectories are in `analysis/fa_pairs.txt`', 'Appendix A, `analysis/codebook.md`'],
], 'rlll')

# ------------------------------------------------------------------ 14
w('## 14. Quality-control checklist (pipeline section 14)')
w('')
table(['Check', 'Status', 'Note'], [
    ['Every task ID aligned between English and Bangla', 'Pass', '300 of 300 aligned (Section 1).'],
    ['Every metric has a denominator', 'Pass', 'Stated in each table header or caption.'],
    ['EN-pass/BN-fail separated from both-fail', 'Pass', 'Sections 2, 3 and Appendix B.'],
    ['Translation errors not counted as genuine Bangla failures', 'Pass', 'C3 is its own class (%d cases).' % c_conf['C3']],
    ['User-simulator errors counted separately', 'Not applicable', 'No user simulator in OfficeBench.'],
    ['Tool/environment failures counted separately', 'Pass', 'C4 is its own class (%d cases).' % c_conf['C4']],
    ['A second reviewer checks a subset', '**Not done**', 'Single annotator. A 12-case blind subset is listed below; `analysis/agreement.py` computes κ from two label CSVs of the same shape as `labels_A.csv` / `labels_B.csv`.'],
    ['Disagreements adjudicated', '**Not done**', 'Depends on the previous item.'],
    ['Case studies match the quantitative patterns', 'Pass', 'Section 15 cases are drawn from the two largest classes (C5, C3) plus one C4.'],
    ['Strong claims only after confound filtering', 'Pass', 'F1–F6 each state the filtered count and a boundary.'],
], 'lll')
w('Blind subset for the second reviewer (random, seed 11, 12 of %d): %s.' % (NPF, ', '.join('`%s`' % b for b in blind)))
w('')
w('Other limits: one run per cell at temperature 0, so run-to-run variation is not measured; the English and Bangla runs are scored by the same corrected checker; the gpt-oss Bangla failures beyond the first 51 subtasks are not root-cause coded; confidence is low on %d of %d notes.' % (level_c['low'], NPF))
w('')

# ------------------------------------------------------------------ 15 case studies
w('## 15. Case studies')
w('')
for cid, title in (('3-68/0', 'A translation that changed the operation'), ('1-10/0', 'A correct answer the checker cannot read'), ('1-15/0', 'A tool that is under-described')):
    d = cases[cid]
    w('**%s — %s.** %s' % (cid, title, d['evidence']))
    w('')
    w('*Root cause:* %s *Label:* %s, %s, first failure point “%s”.' % (d['root'], d['conf'], L.CONF[d['conf']], L.FP[d['fp']]))
    w('')

exec(compile(open(os.path.join(HERE, 'fa_p2_render.py'), encoding='utf-8').read(), 'fa_p2_render.py', 'exec'))

# ------------------------------------------------------------------ appendix A
w('## Appendix A. Trace notes for all %d EN-pass/BN-fail cases' % NPF)
w('')
w('Ordered by task ID. Fields follow pipeline section 4. *Type* is the Section 6 label; *Confound* is Section 7 with annotator confidence.')
w('')
order = sorted(pf_ids, key=lambda s: (int(s.split('-')[0]), int(s.split('-')[1].split('/')[0]), int(s.split('/')[1])))
for cid in order:
    d = cases[cid]
    w('### %s  ·  %s  ·  %d-app' % (cid, d['conf'], byid[cid]['apps']))
    w('')
    w('- **Task goal:** %s' % d['goal'])
    w('- **English:** %s' % d['en'])
    w('- **Bangla:** %s' % d['bn'])
    w('- **First divergence:** %s' % d['diverge'])
    w('- **Final failed / missing action:** %s' % d['missing'])
    w('- **First failure point:** %s  ·  **Type:** %s' % (L.FP[d['fp']], L.FT[d['ftype']]))
    w('- **Root cause:** %s' % d['root'])
    w('- **Confound:** %s (%s)  ·  **Earlier code:** %s (%s)' % (L.CONF[d['conf']], d['level'], byid[cid]['cat_bn'], CN.get(byid[cid]['cat_bn'], '')))
    w('- **Evidence:** %s' % d['evidence'])
    w('')

# ------------------------------------------------------------------ appendix B
w('## Appendix B. Comparison groups')
w('')
w('Primary Bangla-run cause from the earlier per-run classification (`failure_codes_all_runs.json`), for the two failure groups. '
  'This is the Section 3 comparison of EN-pass/BN-fail with EN-fail/BN-fail.')
w('')
keys = sorted(set(pf_bn) | set(ff_bn), key=lambda k: -(pf_bn.get(k, 0) + ff_bn.get(k, 0)))
table(['Earlier code (Bangla run)', 'EN-pass / BN-fail (n=%d)' % NPF, 'EN-fail / BN-fail (n=%d)' % len(ff_ids)],
      [['%s  %s' % (k, CN.get(k, '')), '%d (%s)' % (pf_bn.get(k, 0), pc(pf_bn.get(k, 0) / NPF, 0)),
        '%d (%s)' % (ff_bn.get(k, 0), pc(ff_bn.get(k, 0) / len(ff_ids), 0))] for k in keys], 'lrr')
w('Both-fail subtasks with the *same* earlier code in English and Bangla: %d of %d (%s). '
  'Language-specific codes (AL, NC, WD, TX) account for %d of %d EN-pass/BN-fail cases and %d of %d both-fail cases.'
  % (ff_same, len(ff_ids), pc(ff_same / len(ff_ids)), sum(pf_bn.get(k, 0) for k in ('AL', 'NC', 'WD', 'TX')), NPF,
     sum(ff_bn.get(k, 0) for k in ('AL', 'NC', 'WD', 'TX')), len(ff_ids)))
w('')
table(['Group', 'Single-app', 'Two-app', 'Three-app', 'Total'],
      [['EN-pass / BN-pass', pp_apps[1], pp_apps[2], pp_apps[3], len(pp_ids)],
       ['EN-pass / BN-fail', by_apps_n[1], by_apps_n[2], by_apps_n[3], NPF],
       ['EN-fail / BN-pass', fp_apps[1], fp_apps[2], fp_apps[3], len(fp_ids)],
       ['EN-fail / BN-fail', ff_apps[1], ff_apps[2], ff_apps[3], len(ff_ids)]], 'lrrrr')

# ------------------------------------------------------------------ appendix C
render_appendix_d()

w('## Appendix C. Reproduce')
w('')
w('```')
w('python analysis/fa_step2_paired.py        # aligned runs and paired table  -> analysis/fa_rows.json, fa_step2.json')
w('python analysis/fa_step4_extract.py > analysis/fa_pairs.txt   # condensed side-by-side trajectories')
w('python analysis/fa_rescore.py --validate  # rescorer reproduces the corrected scores (151 / 127 / 86 / 30 of 51)')
w('python analysis/fa_rescore.py gpt-oss_20b_bn   # corrected scores for the full gpt-oss Bangla run')
w('python analysis/fa_signals.py             # behaviour signals (invalid actions, built-in tool calls, endings)')
w('python analysis/fa_gptoss_pairs.py        # gpt-oss paired outcomes -> fa_rows_gptoss.json')
w('python analysis/fa_report.py              # this report from the labels in analysis/fa_labels.py and fa_labels_gptoss.py')
w('```')
w('')
w('Evidence helpers used while labelling: `fa_peek_tasks.py` (Bangla task text), `fa_peek_state.py` (append vs overwrite), `fa_peek_instr.py` (tool description in both languages).')

path = os.path.join(HERE, 'failure_analysis_report.md')
open(path, 'w', encoding='utf-8').write('\n'.join(o) + '\n')
print('wrote', path, len(o), 'lines')
print('conf', dict(c_conf)); print('fp', dict(c_fp)); print('ft', dict(c_ft)); print('exit', dict(c_exit))
