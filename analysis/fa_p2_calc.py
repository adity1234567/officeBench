# Part II (gpt-oss:20b) calculations. Executed inside fa_report.py's namespace (uses summarize, holm, mcnemar, fmtp, fa_figs, RD, L, HERE, json, os, random, collections).
import fa_labels_gptoss as G

GL = G.LABELS
rows_go = json.load(open(os.path.join(HERE, 'fa_rows_gptoss.json'), encoding='utf-8'))
goid = {r['id']: r for r in rows_go}
SG = summarize(rows_go)
grp_go = {a: summarize([r for r in rows_go if r['apps'] == a]) for a in (1, 2, 3)}
adj_go = holm([grp_go[a]['p'] for a in (1, 2, 3)])
pf_go = [r['id'] for r in rows_go if r['en'] and not r['bn']]
fp_go = [r['id'] for r in rows_go if not r['en'] and r['bn']]
ff_go = [r['id'] for r in rows_go if not r['en'] and not r['bn']]
NPG, NFG = len(pf_go), len(fp_go)
assert set(pf_go) == set(GL)

gconf = collections.Counter(GL[i]['conf'] for i in pf_go)
gfp = collections.Counter(GL[i]['fp'] for i in pf_go)
gft = collections.Counter(GL[i]['ftype'] for i in pf_go)
gexit = collections.Counter(GL[i]['exit'] for i in pf_go)
glevel = collections.Counter(GL[i]['level'] for i in pf_go)
g_by_apps = {a: collections.Counter(GL[i]['conf'] for i in pf_go if goid[i]['apps'] == a) for a in (1, 2, 3)}
g_apps_n = collections.Counter(goid[i]['apps'] for i in pf_go)

# why English failed on the subtasks Bangla passes: the English run's earlier root-cause code, and behaviour signals
fp_codes = collections.Counter(goid[i]['cat_en'] for i in fp_go)
fp_sig_en = [goid[i]['sig_en'] for i in fp_go if goid[i]['sig_en']]
fp_sig_bn = [goid[i]['sig_bn'] for i in fp_go if goid[i]['sig_bn']]
fp_mal_runs = sum(1 for x in fp_sig_en if x['malformed'])
fp_builtin_en, fp_builtin_bn = sum(x['builtin'] for x in fp_sig_en), sum(x['builtin'] for x in fp_sig_bn)
fp_stuck_en = sum(1 for x in fp_sig_en if x['end'] == 'stuck')
fp_gem_en = sum(goid[i]['gem_en'] for i in fp_go)
SIGS = json.load(open(os.path.join(HERE, 'fa_signals.json'), encoding='utf-8'))
n_sig = len(SIGS['GO'])

# difference between the models: (EN - BN) for gemma minus (EN - BN) for gpt-oss, paired by subtask
_both = [(byid[i]['en'], byid[i]['bn'], goid[i]['en'], goid[i]['bn']) for i in byid]
_d = lambda xs: (sum(x[0] for x in xs) - sum(x[1] for x in xs) - sum(x[2] for x in xs) + sum(x[3] for x in xs)) / len(xs)
DID = _d(_both)
random.seed(5)
_bs = sorted(_d([_both[random.randrange(len(_both))] for _ in range(len(_both))]) for _ in range(4000))
DID_CI = (_bs[int(.025 * 4000)], _bs[int(.975 * 4000) - 1])

# sensitivity scenarios (gpt-oss)
g_ids = lambda *cs: [i for i in pf_go if GL[i]['conf'] in cs]
_drop = lambda ids: [r for r in rows_go if r['id'] not in set(ids)]
FP_FMT = [i for i in fp_go if goid[i]['cat_en'] == 'FMT']
SCG_ROWS = [
    ('S0  All 300 subtasks (as scored)', rows_go),
    ('S1  Drop tool/environment cases (C4)', _drop(g_ids('C4'))),
    ('S2  Drop answer-language / weak-check cases (C5)', _drop(g_ids('C5'))),
    ('S3  Drop C4 + C5', _drop(g_ids('C4', 'C5'))),
    ('S4  Drop C4 + C5 + C6', _drop(g_ids('C4', 'C5', 'C6'))),
    ('S5  Credit Bangla answers that fail only on the check (C5 → BN pass)', [dict(r, bn=True) if r['id'] in set(g_ids('C5')) else r for r in rows_go]),
    ('S6  S3 made symmetric: also drop the %d EN-fail/BN-pass subtasks where English failed on action format' % len(FP_FMT), _drop(g_ids('C4', 'C5') + FP_FMT)),
]
SCG = [(name, summarize(rs)) for name, rs in SCG_ROWS]

# figures
FIG_PAIR_GO = fa_figs.paired(R, 'pair_go', 'res_paired_gptoss.svg', 'gpt-oss:20b', 'Amber is English-only passes, teal is Bangla-only passes: for gpt-oss the teal segment is the larger one at every size.')
FIG_SIG = fa_figs.signals(R)
FIG_CONF_GO = fa_figs.confounds(R, L.CONF, g_by_apps, ['C7', 'C1', 'C5', 'C4', 'C6'], 'res_confounds_gptoss.svg', NPG, 'gpt-oss:20b')
FIG_FOREST_GO = fa_figs.forest(SCG, {'S0': 'As scored', 'S1': 'Drop tool/environment cases (C4)', 'S2': 'Drop answer-language cases (C5)',
                                     'S3': 'Drop C4 + C5', 'S4': 'Drop C4 + C5 + C6', 'S5': 'Credit Bangla answers (C5)',
                                     'S6': 'S3, plus drop English format-failure subtasks'}, 'res_sensitivity_gptoss.svg', 'gpt-oss:20b')
g_blind = sorted(random.Random(13).sample(pf_go, 10), key=lambda s: (int(s.split('-')[0]), int(s.split('-')[1].split('/')[0]), int(s.split('/')[1])))
