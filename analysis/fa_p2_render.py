# Part II (gpt-oss:20b) rendering. Executed inside fa_report.py's namespace after fa_p2_calc.py.
w('## Part II. The pipeline applied to gpt-oss:20b')
w('')
w('The gpt-oss Bangla run finished after the first draft of this report: **300 of 300 subtasks**. It was scored with `analysis/fa_rescore.py`, which applies the same three repairs '
  'as the other runs and reproduces the existing corrected scores exactly for gemma English (151), gemma Bangla (127), gpt-oss English (86) and the first 51 gpt-oss Bangla subtasks (30), with zero mismatches. '
  'Sections II.1–II.10 follow the same pipeline steps as Sections 1–14 for gpt-oss.')
w('')

# ---- II.1 data
w('### II.1 Data and alignment (pipeline section 1)')
w('')
w('300 of 300 task IDs are present in both gpt-oss runs. Action histories are recorded for %d runs in each language; one subtask per run has none (2-40/3 in English, 3-46/0 in Bangla) but still has its output files, so it is scored from the files. '
  'Fields and paths are as in Section 1 with the run tags `gpt-oss_20b_en` and `gpt-oss_20b_bn`.' % n_sig)
w('')

# ---- II.2 basic outcome
w('### II.2 Basic outcome (pipeline section 2)')
w('')
body = []
for name, s in [('Overall', SG), ('Single-app', grp_go[1]), ('Two-app', grp_go[2]), ('Three-app', grp_go[3])]:
    body.append([name, s['n'], '%d (%s)' % (s['pp'] + s['pf'], pc(s['en'])), '%d (%s)' % (s['pp'] + s['fp'], pc(s['bn'])),
                 pp_(s['gap']), pc(s['melr']), s['pp'], '**%d**' % s['pf'], '**%d**' % s['fp'], s['ff']])
table(['Setting', 'n', 'EN pass', 'BN pass', 'Gap (EN−BN)', 'MELR', 'PP', '**PF**', '**FP**', 'FF'], body, 'lrrrrrrrrr')
w('Same definitions as Section 2. **The gap is negative: gpt-oss passes more subtasks in Bangla than in English** (%d against %d), and the Bangla advantage holds at every task size. '
  'The paired outcome is %d EN-pass/BN-fail against %d EN-fail/BN-pass.' % (SG['pp'] + SG['fp'], SG['pp'] + SG['pf'], SG['pf'], SG['fp']))
w('')
w('Figure %d (Section R.4) shows the paired outcome as bars.' % FIGN['pair_go'])
w('')

# ---- II.3 statistics
w('### II.3 Statistics (pipeline section 11)')
w('')
body = []
for name, s in [('Overall', SG), ('Single-app', grp_go[1]), ('Two-app', grp_go[2]), ('Three-app', grp_go[3])]:
    body.append([name, '%s [%s, %s]' % (pc(s['en']), pc(s['en_ci'][0]), pc(s['en_ci'][1])),
                 '%s [%s, %s]' % (pc(s['bn']), pc(s['bn_ci'][0]), pc(s['bn_ci'][1])),
                 '%s [%.1f, %.1f]' % (pp_(s['gap']), 100 * s['gap_ci'][0], 100 * s['gap_ci'][1]),
                 '%s [%.1f, %.1f]' % (pc(s['melr']), 100 * s['melr_ci'][0], 100 * s['melr_ci'][1])])
table(['Setting', 'EN success [95% CI]', 'BN success [95% CI]', 'Gap [95% CI, pp]', 'MELR [95% CI, %]'], body, 'lrrrr')
body = []
for k, a in enumerate((1, 2, 3)):
    s = grp_go[a]
    body.append(['%d-app' % a, '%d / %d' % (s['pf'], s['fp']), fmtp(s['p']), fmtp(adj_go[k]), '%.2f' % s['g'], '%.2f' % s['odds']])
body.append(['**Overall (not in Holm family)**', '%d / %d' % (SG['pf'], SG['fp']), fmtp(SG['p']), '—', '%.2f' % SG['g'], '%.2f' % SG['odds']])
table(['Setting', 'b / c (PF / FP)', 'McNemar p', 'Holm-adjusted p', 'Cohen’s g', 'Odds b/c'], body, 'lrrrrr')
w('The overall Bangla advantage is %s (95%% interval [%.1f, %.1f] pp), McNemar p = %s, g = %.2f (negative sign: Bangla ahead). After Holm correction across the three task sizes the subgroup tests give adjusted p = %s, %s and %s, '
  'so the direction is consistent but no single size is significant on its own.'
  % (pp_(SG['gap']), 100 * SG['gap_ci'][0], 100 * SG['gap_ci'][1], fmtp(SG['p']), SG['g'], fmtp(adj_go[0]), fmtp(adj_go[1]), fmtp(adj_go[2])))
w('')
w('**The two models move in opposite directions.** Taking the English-minus-Bangla gap for gemma (%s) and for gpt-oss (%s) on the same 300 subtasks, their difference is **%s** '
  '(95%% bootstrap interval [%.1f, %.1f] pp), which excludes zero.' % (pp_(S['gap']), pp_(SG['gap']), pp_(DID), 100 * DID_CI[0], 100 * DID_CI[1]))
w('')

# ---- II.4 case selection
w('### II.4 Cases analysed (pipeline section 3)')
w('')
table(['Group', 'Count', 'How analysed here'], [
    ['EN-pass / BN-fail', SG['pf'], '**All %d** traced and labelled (Appendix D).' % SG['pf']],
    ['EN-fail / BN-pass', SG['fp'], 'The largest discordant group, so it is not skipped: English run’s earlier root-cause code and behaviour signals for all %d (Section II.9).' % SG['fp']],
    ['EN-pass / BN-pass', SG['pp'], 'Counted only.'],
    ['EN-fail / BN-fail', SG['ff'], 'Counted only. The Bangla run’s failures are not root-cause coded beyond the first 51 subtasks.'],
], 'lrl')

# ---- II.5-II.8 labels
w('### II.5 Trace notes (pipeline section 4)')
w('')
w('One note per EN-pass/BN-fail case, in Appendix D. A worked example:')
w('')
d = GL['2-36/0']
for lab, val in [('Task goal', d['goal']), ('English', d['en']), ('Bangla', d['bn']), ('First divergence', d['diverge']), ('Final failed or missing action', d['missing']),
                 ('Failure type', L.FT[d['ftype']]), ('Root cause', d['root']), ('Confound decision', '%s (%s confidence)' % (L.CONF[d['conf']], d['level'])), ('Evidence', d['evidence'])]:
    w('- %s: %s' % (lab, val))
w('')
w('### II.6 First failure point (pipeline section 5)')
w('')
dist_table(gfp, [(i, L.FP[i]) for i in range(len(L.FP))], NPG, 'First failure point')
w('### II.7 Failure type (pipeline section 6)')
w('')
dist_table(gft, [(i, L.FT[i]) for i in range(len(L.FT))], NPG, 'Failure type')
w('### II.8 Confound type and root-cause exits (pipeline sections 7–8)')
w('')
dist_table(gconf, [(k, '%s  %s' % (k, v)) for k, v in L.CONF.items()], NPG, 'Confound')
w('Confidence of the annotator: high %d, medium %d, low %d.' % (glevel['high'], glevel['medium'], glevel['low']))
w('')
fig('Figure %d. Confound class of the 25 gpt-oss EN-pass/BN-fail cases, split by number of apps.' % FIGN['conf_go'], FIG_CONF_GO)
table(['Exit step', 'Cases'], [[L.EXIT[k], gexit.get(k, 0)] for k in range(8)], 'lr')
w('Observations:')
w('')
w('- **The name-case failure replicates across models.** %d of the %d cases are lookups with a lower-cased name (“bob”) that returns nothing, %s. The same mechanism produced 3 of the gemma genuine cases; '
  'the two models fail on the same two subtasks (1-21/1 and 1-21/2). It is the one Bangla-specific agent mechanism seen in both.'
  % (sum(1 for i in pf_go if GL[i]['conf'] == 'C1' and GL[i]['fp'] == 1), NPG, 'in the email and calendar apps'))
w('- **Answer-language failures are rarer than in gemma.** Only 4 of the %d cases have an answer in Bangla script (1-12/0, 1-21/2, 2-32/0, 2-33/1) and 2 of them are C5 language cases, against 15 of 42 for gemma; gpt-oss reasons in English and mostly answers in English. '
  'The other C5 cases are checker mismatches: a required verbatim sentence (1-19/4), an address the task does not ask for (2-2/0), a file the task does not name (2-26/0) and a keyword that appears only through the subject wording (2-43/1).'
  % NPG)
w('- **The llm app returns empty strings for gpt-oss** (2-36/0, 3-89/0): all %d calls in those two Bangla runs came back empty, because the app calls the same reasoning model with a 50-token answer limit. This is a tool failure that the English runs avoided by not using the app.' % 14)
w('- **%d of %d cases (%s) are unclear:** wrong comparisons or missing outputs on identical inputs, with nothing in the trace tied to Bangla.' % (gconf['C7'], NPG, pc(gconf['C7'] / NPG)))
w('')

# ---- II.9 why Bangla wins
w('### II.9 Why gpt-oss does better in Bangla')
w('')
w('The %d subtasks that Bangla passes and English fails are the larger group, so the pipeline asks for their cause.' % NFG)
w('')
CNL = dict(CN)
table(['English run’s root-cause code', 'Subtasks', 'Share of %d' % NFG],
      [['%s  %s' % (k, CNL.get(k, '')), v, pc(v / NFG)] for k, v in fp_codes.most_common()], 'lrr')
w('- **%d of %d (%s)** of these English failures are coded *action format* (could not produce a valid action), the largest single code.' % (fp_codes['FMT'], NFG, pc(fp_codes['FMT'] / NFG)))
w('- In **all %d** of the English runs there is at least one malformed action; they contain **%d** calls to the model’s built-in tools (container.exec, repo_browser, …) against **%d** in the same subtasks in Bangla, and %d of them ended as stuck.'
  % (fp_mal_runs, fp_builtin_en, fp_builtin_bn, fp_stuck_en))
w('- Across all runs, the Bangla prompt cut gpt-oss’s invalid actions from %d to %d, built-in tool calls from %d to %d, and stuck runs from %d to %d (Figure %d).'
  % (sum(v['malformed'] for v in SIGS['GO'].values()), sum(v['malformed'] for v in SIGS['GB'].values()),
     sum(v['builtin'] for v in SIGS['GO'].values()), sum(v['builtin'] for v in SIGS['GB'].values()),
     sum(v['end'] == 'stuck' for v in SIGS['GO'].values()), sum(v['end'] == 'stuck' for v in SIGS['GB'].values()), FIGN['sig']))
w('- %d of the %d subtasks are also passed by gemma in English, so they are not unusually hard.' % (fp_gem_en, NFG))
w('')
w('Figure %d (Section R.4) shows these signals for all runs.' % FIGN['sig'])
w('')
w('*Reading:* the Bangla advantage of gpt-oss comes with a large reduction in English-specific format failures, not with better handling of the content. '
  'The Bangla prompt is in a different script from the benchmark’s English action format, and the model falls back less often on its own tool-calling habit. '
  'This is consistent with the pattern but not proven by it: one run per cell, and the signals are counted automatically, not read case by case.')
w('')

# ---- II.10 sensitivity
w('### II.10 Sensitivity analysis (pipeline section 11)')
w('')
fig('Figure %d. gpt-oss English minus Bangla gap with 95%% interval under each scenario. Negative means Bangla is ahead.' % FIGN['forest_go'], FIG_FOREST_GO)
body = [[name, s['n'], pc(s['en']), pc(s['bn']), pp_(s['gap']), '[%.1f, %.1f]' % (100 * s['gap_ci'][0], 100 * s['gap_ci'][1]), pc(s['melr']), '%d / %d' % (s['pf'], s['fp']), fmtp(s['p'])]
        for name, s in SCG]
table(['Scenario', 'n', 'EN', 'BN', 'Gap', 'Gap 95% CI (pp)', 'MELR', 'PF / FP', 'McNemar p'], body, 'lrrrrrrrr')
sg0, sg3, sg6 = SCG[0][1], SCG[3][1], SCG[6][1]
w('S1–S4 remove only English-pass/BN-fail cases, so the Bangla advantage grows by construction (S3: %s). '
  'S6 treats the other side the same way and also removes the English-fail/BN-pass subtasks where English failed on the action format: the gap falls to %s (95%% interval [%.1f, %.1f] pp, p = %s)%s. '
  'The Bangla advantage of gpt-oss therefore rests largely on those English action-format failures, not on the other subtasks.'
  % (pp_(sg3['gap']), pp_(sg6['gap']), 100 * sg6['gap_ci'][0], 100 * sg6['gap_ci'][1], fmtp(sg6['p']),
     ' and the interval includes zero' if sg6['gap_ci'][0] <= 0 <= sg6['gap_ci'][1] else ''))
w('')

# ---- II.11 findings
w('### II.11 Findings for gpt-oss (pipeline section 12)')
w('')
w('**G1. gpt-oss is better in Bangla, gemma is worse; the models differ by %s (interval [%.1f, %.1f] pp).** '
  'We find %d of 300 passes in Bangla against %d in English for gpt-oss (%s; McNemar p = %s), consistent at all three task sizes. *Boundary:* one run per cell; the effect is not significant within any single task size after Holm correction.'
  % (pp_(DID), 100 * DID_CI[0], 100 * DID_CI[1], SG['pp'] + SG['fp'], SG['pp'] + SG['pf'], pp_(SG['gap']), fmtp(SG['p'])))
w('')
w('**G2. The Bangla advantage of gpt-oss tracks a drop in English-specific format failures.** '
  '%d of the %d Bangla-only passes are English runs coded action-format failures, every one of the %d English runs had invalid actions, and the Bangla prompt cut built-in-tool fallbacks from %d to %d across all runs. '
  '*Boundary:* automatic counts and one run per cell; it shows association, not that the prompt language is the cause.'
  % (fp_codes['FMT'], NFG, fp_mal_runs, sum(v['builtin'] for v in SIGS['GO'].values()), sum(v['builtin'] for v in SIGS['GB'].values())))
w('')
w('**G3. Of the %d gpt-oss EN-pass/BN-fail cases, %d (%s) are genuine Bangla agent failures and %d of those are one mechanism.** '
  'The %d C1 cases are 6 lower-cased name lookups and one changed word (“Trip” for “travelling”), both seen in gemma. Another %d (%s) are checker or answer-language artefacts (C5), %d (%s) are tool failures (C4) and %d (%s) are unclear (C7). '
  '*Boundary:* single annotator, no second review.'
  % (NPG, gconf['C1'], pc(gconf['C1'] / NPG), 6, gconf['C1'], gconf['C5'], pc(gconf['C5'] / NPG), gconf['C4'], pc(gconf['C4'] / NPG), gconf['C7'], pc(gconf['C7'] / NPG)))
w('')
w('**G4. Name case is the one genuine Bangla mechanism in both models.** Names written only in Bangla script have no letter case; the agent writes them in lower case for case-sensitive lookups of mailboxes and calendars, the lookup returns nothing, and the run ends. '
  'It accounts for 3 gemma cases (1-20/3, 1-21/1, 1-21/2) and 6 gpt-oss cases (1-21/1, 1-21/2, 2-39/0, 2-39/1, 2-39/3, 2-40/1). A case-insensitive lookup in the tools, or the Latin spelling of names in the prompt, would likely remove them.')
w('')
w('**G5. For gpt-oss, the llm app is a separate failure source.** It returned empty strings in every call of two Bangla runs (2-36/0, 3-89/0) and is a known harness problem for a reasoning model with a 50-token limit.')
w('')

# ---- II.12 QC
w('### II.12 Quality control for Part II (pipeline section 14)')
w('')
table(['Check', 'Status', 'Note'], [
    ['Every task ID aligned', 'Pass', '300 of 300.'],
    ['Every metric has a denominator', 'Pass', 'Stated in each table.'],
    ['EN-pass/BN-fail separated from both-fail', 'Pass', 'Section II.4.'],
    ['Confound classes counted separately', 'Pass', 'Section II.8.'],
    ['Scores reproducible', 'Pass', '`fa_rescore.py --validate` reproduces 151 / 127 / 86 / 30-of-51 with zero mismatches.'],
    ['A second reviewer checks a subset', '**Not done**', 'Blind subset (random, seed 13, 10 of %d): %s.' % (NPG, ', '.join('`%s`' % b for b in g_blind))],
    ['EN-fail/BN-fail causes for the Bangla run', '**Not coded**', 'Only the first 51 subtasks have root-cause codes; behaviour signals are used instead.'],
], 'lll')
w('')


def render_appendix_d():
    w('## Appendix D. Trace notes for the %d gpt-oss EN-pass/BN-fail cases' % NPG)
    w('')
    w('Same fields as Appendix A. English run = `gpt-oss_20b_en`, Bangla run = `gpt-oss_20b_bn`.')
    w('')
    for cid in sorted(pf_go, key=lambda s: (int(s.split('-')[0]), int(s.split('-')[1].split('/')[0]), int(s.split('/')[1]))):
        d = GL[cid]
        w('### %s  ·  %s  ·  %d-app' % (cid, d['conf'], goid[cid]['apps']))
        w('')
        w('- **Task goal:** %s' % d['goal'])
        w('- **English:** %s' % d['en'])
        w('- **Bangla:** %s' % d['bn'])
        w('- **First divergence:** %s' % d['diverge'])
        w('- **Final failed / missing action:** %s' % d['missing'])
        w('- **First failure point:** %s  ·  **Type:** %s' % (L.FP[d['fp']], L.FT[d['ftype']]))
        w('- **Root cause:** %s' % d['root'])
        w('- **Confound:** %s (%s)' % (L.CONF[d['conf']], d['level']))
        w('- **Evidence:** %s' % d['evidence'])
        w('')
