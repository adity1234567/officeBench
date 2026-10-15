# Rewrite of `COLING_2027 (1).pdf` → `paper_acl/main.tex`

**Files.**
- `main.tex` and `refs.bib`: the paper, ACL style (`acl.sty`, `acl_natbib.bst`).
- `main.pdf`: notes shown (13 pages). `main_clean.pdf`: notes hidden (12 pages). In both, the main text ends before Limitations, within 8 pages.
- `figures/make_figures.py`: generates `fig_overview.pdf` and `fig_chains.pdf`.
- `analysis/acl_rewrite_stats.py` writes `analysis/acl_rewrite_tables.json` and `.md`. It computes every OfficeBench number from the run logs and applies Holm correction across all seven comparisons.
- `analysis/paper_failing_contain.py`: counts Bangla-script answers with a failing English keyword check (41 of 46).
- `analysis/fa_rescore.py`: the repaired OfficeBench scorer (existing).

To hide the notes, change `\showverifytrue` to `\showverifyfalse` (line 20).

**Sources of numbers.**
- OfficeBench: computed from the run logs in this repository.
- τ²-bench, WorkBench and TheAgentCompany: no raw data is in the repository. Their numbers are transcribed from `sobhar_kaj/*_FAILURE_ANALYSIS.pdf`, and their source is recorded in the script output.

## Gap-by-gap change log

| # | Gap | What was done |
|---|-----|---------------|
| 1 | Template title, empty abstract, intro with only RQ3 | New title; 197-word abstract; full introduction with problem, two concrete examples from our runs, design, RQ1–RQ3 and four contributions. |
| 2 | Boilerplate, empty §4.5, Bangla TODOs, pasted notes in §6.2, nonexistent Tables 5/6 and Appendix C, `Table ??`, no Limitations | The empty §4.5 heading was first removed, then restored with content as **§4.5 "Evaluation-setup failures in both languages"**. It covers OfficeBench scorer repairs (19/24/6/9 runs flipped from fail to pass, computed), benchmark defects (47/149 gemma English failures, 39/131 both-fail tasks, 57 tasks decided by a defect, task 1-2/0), τ² simulated-user early stops (46 vs 26 flags) and English-speaking simulated users (33 and 54 runs), and harness limits (llm helper 50-token cap, reply cap, empty replies, TAC authentication walls, τ² provider exclusions, WorkBench provider errors: +7.1, n=85). Everything else in this row was removed. Each pasted note in §6.2 was either quantified (§4.4) or moved to Discussion as a labelled hypothesis. Every table and appendix reference resolves (no undefined references). Real Limitations and Ethical Considerations sections added. |
| 3 | Cases presented as share of the gap | RQ3 now speaks only about cases ("these are cases, not shares of the gap"). With data: added **Table 5** with raw gap, corrected-grading gap and confound-removal gap, each with a 95% CI and symmetric/one-sided marked. Not done: re-coding OfficeBench and τ²-bench BN-pass/EN-fail tasks with the same codebook (needs new annotation); stated in Limitations. |
| 4 | "Most causes lie outside the agent" | Replaced with "the largest group, 74 cases (45.4%)"; agent 69 (42.3%), unclear 20 (12.3%). |
| 5 | General-weakness label unverifiable | Range reported: 14.7% as labelled, 27.0% with unclear cases, 54.6% with general-weakness cases, and the text states why the upper bound is safer. |
| 6 | Checker–agent boundary | One rule stated in §3.5: a script- or numeral-only difference is a checker artefact; a changed English value is an agent failure. Applying it relabels one TheAgentCompany case (translation → checker). This is reported in the text, not applied silently (translation 9→8, checker 22→23, evaluation-side total unchanged). |
| 7 | "Run-to-run noise" as TAC's dominant cause | Removed as a dominant cause. TAC now "has too few cases for a dominant cause (3 general, 3 unclear, of which 2 are Bangla reruns that disagree)". The rerun evidence (13 reruns: 1 completion and 3 score changes) is reported in RQ1 and Limitations. |
| 8 | τ² n = 218 vs 149; TAC 23 vs 21 | Reconciled from the reports. τ²: 218 paired tasks (gemma4-31b) and 149 (gpt-oss-20b) after dropping infrastructure-error pairs, of which 149 are gradeable in all four cells. TAC: 23 task pairs over 21 unique tasks, with the unique-task gap also reported (9.5 points, 2/0). The pre-exclusion τ² sample size is unknown → `\verify`. |
| 9 | CIs promised but missing | Paired bootstrap 95% CIs added for all seven comparisons (Table 2). OfficeBench CIs recomputed (4,000 resamples, seed 7) and they match the reports exactly. |
| 10 | Discordant counts | `b/c` added for every McNemar test (Table 2, subgroup text, model-gap text). |
| 11 | Subgroups without n/tests | App-count subgroups now give discordant counts and Holm-adjusted p (single-app p_H = .004; two-app .186; three-app 1.00). Task-type swings are explicitly descriptive with n (Section 5 and Appendix C); per-type tests are not possible from rates alone. |
| 12 | Inconsistent counts in notes | "67 lost / 15 won" → recomputed **82 / 17** in English and 48 / 27 in Bangla (the 67/15 came from the shipped scorer). "44 language-induced failures" → dropped (the corrected count is 42 EN-pass/BN-fail). 14.1-point comparison → its subset (149 shared τ² tasks) and both gaps (+13.4, −0.7) are now reported. |
| 13 | MELR unstable | MELR always shown with n; TAC's 33.3% is called "not informative" (three discordant tasks). |
| 14 | "Score difference comes from the language alone" | Replaced: §3.2 says what is controlled and that translation and Bangla simulated users are part of the treatment. |
| 15 | Localization rules cause checker failures | Stated as part of the treatment in §3.2. Per-benchmark localization rows added to Table 1. New audit of the OfficeBench translation actually used: names kept in Latin script in 43/103 mentions; 44 instructions with Bengali digits, 50 with ASCII digits, 14 with both; 1/262 file names changed. |
| 16 | Missing configuration details; κ interpretation | Appendix B lists every configuration value that is known, and `\verify` marks each unknown one. κ is reported per benchmark with N: τ² 0.39 is "fair" (Landis–Koch), WorkBench 0.59/0.77, OfficeBench 0.78 on 16 cases. |
| 17 | gpt-oss Bangla gain | Explicitly not read as better understanding; invalid actions 1,671 → 955 (recomputed, matches). |
| 18 | Anecdotal trajectory claims (later pass restored the supported parts: models fail at different stages, wasted vs true step budget, gpt-oss losses to gemma, agent-builder recommendations, troubleshooting +6/-11) | §4.4 keeps only measured patterns, each with a denominator (Table 6). Verification deficit: 3/180 vs 20/112 writing runs read back. Out-of-step failures on three-app tasks: 38/46. Identical repetition: 7–17% of failed steps. The rest moved to Discussion as five hypotheses, each with a test. **Contradicted:** "repetition is not recovery" as a general pattern; most failed steps are not repeated identically. |
| 19 | Premature termination on τ² | Stated as simulator-caused (10 of 11) in RQ2 and the Table 3 caption. Not presented as an agent mechanism. |
| 20 | WorkBench "evaluator expects English wording" | Removed. WorkBench grades database state; its one checker/ambiguity case is a degenerate task. |
| 21 | Positioning | Related Work rewritten in four paragraphs. Each closest work is described by what it measures (gap size or argument-language errors), contrasted with our component-level attribution. |
| 22 | τ-bench, OpenHands, 2026 citations | τ-bench and OpenHands are now cited. All 2026 citations were checked online: arXiv IDs and authors match. MAPS was corrected from "GAIA and SWE-bench in ten languages" to "four agent suites in eleven languages". Its page numbers were dropped because they could not be verified. Luo et al. now has the full author list. |

## Draft numbers that changed after recomputation (never silent)

| Draft | Rewrite | Why |
|-------|---------|-----|
| "25 of the 28 out-of-step failures occur in three-app tasks" (gemma English) | 38 of 46 | Recomputed from logs: failed runs that did not end in finish or stuck. The draft's count definition is not recorded. |
| GPT-OSS "reading back 17/103 writing runs" | 20/112 | Recomputed with an explicit read-back definition (Table 6 caption). |
| "GPT-OSS drops to only 6/112 three-app tasks" | 8/112 | 6/112 is the shipped-scorer count; 8/112 is the corrected one used throughout. |
| "loses 67 tasks that Gemma passes … winning 15" | 82 / 17 | Same reason (shipped vs repaired scorer). The draft's "mostly through format failures and loops" is now measured: 80 of the 82 gpt-oss runs contain a rejected action, 33 are coded action format, 42 end stuck or at the step limit. |
| "44 language-induced failures" | dropped | It conflicts with 42 EN-pass/BN-fail; the language-specific codes are 27 of 42. |
| "only six are pure budget failures" (gpt-oss) | 0 of 81 out-of-step failures have no rejected step; 44 of 81 have at least half their steps rejected | Recomputed with an explicit definition (Table 6). It supports the draft's point (wasted budget) with a different count. |
| "recovery in 4 of 18 failed Bangla lookups" (τ²) | dropped | There are no τ² traces in this repository to verify it. |

## Unresolved `\verify` notes (14)

1. §3.1: WorkBench sampling seed value.
2. §3.1: τ²-bench sample size before infrastructure exclusions; the draft's Table 1 says 149.
3. Table 1: τ² policy language. The draft says English; the τ² report says it was translated.
4. §3.2: the "independent review" of translations (reviewer, coverage). The OfficeBench audit shows the rules were applied unevenly.
5. §3.3: the 100-iteration cap for TheAgentCompany (in the draft, not in the sources).
6. §3.5: annotator identity for OfficeBench and τ²-bench, and the source of κ = 0.63 in the draft's range.
7. §5: who assigned task types and how.
8. Appendix B: Ollama version, quantization, num_ctx.
9. Appendix B: per-model reply caps (512 / 2,048) as stated in the OfficeBench report.
10. Appendix B: TheAgentCompany iteration cap.
11. Appendix B: WorkBench and τ² step limits.
12. Appendix B: model playing TheAgentCompany coworkers.
13. Appendix B: translation tool and review for WorkBench, τ² and TheAgentCompany.
14. Appendix B: annotators for OfficeBench and τ²-bench.

## Still open

- **Symmetric attribution.** Coding the OfficeBench and τ²-bench BN-pass/EN-fail cases with the same codebook would turn RQ3 from case-level into gap-level evidence (Limitations).
- **Second annotation.** TheAgentCompany has no second annotation, and most OfficeBench cases have one annotator.
- **Translation re-run.** A re-run of OfficeBench Bangla with an audited translation (`analysis/bn_cache.json` v2; tag `bn2`) was started but has not completed. No v2 results are used.

## Later structural edits

- Results subsections 4.1-4.3 now open with a descriptive heading, then the RQ question, then a one-paragraph **Finding** that states the main result, followed by the supporting numbers.
- The TheAgentCompany rerun detail moved from 4.1 to Limitations (single runs). The Bangla-specific range sentences in 4.3 were merged, because the Finding states the range.
- 4.4 extended beyond OfficeBench with the run-level signals recorded for tau2-bench, WorkBench and TheAgentCompany (from the reports): unmade required writes, wrong-argument writes, step-limit hits, tool calls per run or task, invented-argument crashes, read loops. A new Limitations paragraph explains why step-level measures exist only for OfficeBench (the only benchmark with full logs in the repository).
- For space: the per-benchmark agreement details (kappa with n) moved to Appendix A, with a one-sentence summary in 3.5; the hypotheses list became a compact paragraph (H1-H5); the duplicate tau2 exclusion sentence in 4.5 was dropped.
- 4.4 and Limitations now justify the OfficeBench-only step-level measures methodologically, instead of by data availability. Only OfficeBench defines rejected actions identically for both models (a parsed text action every step), has no simulated user, uses a shared 20-step budget, and has the largest paired sample (1,200 runs). On WorkBench one invalid call fails the run outright; on tau2-bench the simulated user co-produces the trajectory; TheAgentCompany has 23 pairs for one model. The WorkBench 24-call read-loop anecdote was dropped for space.


## Draft §4.5 "Where Trajectories Break": why each point was kept or not

Rule: a point stays in Results only if it has a count with a denominator and helps answer RQ1–RQ3.
A plausible but untested point goes to Discussion as a labelled hypothesis with a test. A point
with no content, numbers that do not reproduce, or a contradiction in the data is dropped.

| Draft item | Why keep | Why not | Where it is now |
|---|---|---|---|
| Opening: agent / interface / environment taxonomy | States the paper's core idea (failures come from different parts of the pipeline) | Never defined or applied; competes with the C1–C7 codebook | Measured through the stage × cause table (§4.3, Appendix C); no second taxonomy |
| a. Models fail at different layers | Measured (107/214 vs 12/149 no valid action; WorkBench args 40/79 vs 11/33); explains RQ1's opposite directions | Covers all failures, not Bangla-only; two models only; failure masking | §4.4 "The two models fail at different stages" |
| b. Long-horizon error accumulation | Counts are real (38/46 out-of-step failures on three-app tasks); explain the zero three-app gap | "Accumulation" not measured; draft numbers did not reproduce (6/112 is 8/112, 25/28 is 38/46) | Counts in §4.1/§4.4; mechanism is H2 |
| c. Verification deficit | Measured contrast (3/180 vs 20/112); explains why name-case slips become fatal | Causal effect untested; read-back is a heuristic; same in both languages; 17/103 did not reproduce | §4.4; cause is H1 |
| d. Meta-control and wasted budget | Budget split measured (gemma 13/46 true budget failures; gpt-oss 0/81, 44/81 mostly rejected; 9/58 in Bangla) | "Despite correct reasoning" not checked; one WorkBench anecdote; repetition only 7–17% | Budget split in Table 6; "control fails when the plan is right" is H6 |
| e. State reconstruction tax, model × scaffold, fixes | Compatibility fits the data (80/82 gpt-oss losses contain rejected actions; 33 coded format); fixes are practical | The "tax" had no text; reasoning was never measured separately; fixes untested; 67/15 is the old scorer's count | H3 (sharpened: interface reliability rather than reasoning); H7 for plan reconstruction (premise verified in utils/policies.py: the prompt carries past actions and observations, not earlier ##Thought text); fixes in §6, marked untested |
| f. Error propagation, "repetition is not recovery" | Chains show a small slip plus no recovery leading to failure; 60 gpt-oss English runs with 3 or more identical rejected actions | General claim contradicted (7–17%); "4 of 18 lookups" and "six pure budget failures" not reproducible; four examples only | Chains in the Appendix figure; counts in Table 6; general claim is H5 |
| 4.6 Evaluation Setup Failures (empty) | Scorer bugs, defects, simulator and harness limits lower both languages | Only as an empty heading | Restored as §4.5 |

## Additions in this round (v8; v7 is saved in previous/)

- **Stage × cause cross-table** (Appendix C, `analysis/acl_stage_by_cause.py` → `analysis/acl_stage_by_cause.json`), parsed from the per-case notes. Its totals reproduce the stage table (Table 3) and the cause table (Table 4) exactly for all seven analyses. In §4.3, the new paragraph "Stage and cause differ" reports:
  - final-answer failures are checker artefacts (18/19);
  - only 10 of 35 simulated-user cases are early stops, and 20 start at task level;
  - tool-level failures are mostly agent-caused (30/38);
  - genuine Bangla failures start at grounding (13), understanding or planning (3) or tool use (8), never at control or the final answer.
- **§4.2 is now positional only.** The causal sentences (checker, simulated customer) moved to §4.3.
- **Hypotheses:** H6 (control can fail when the plan is right) and H7 (the scaffold forces plan reconstruction) added; H3 sharpened.
- **§4.5:** "agents still err inside defect-broken tasks" is now quantified. 18 of 19 gpt-oss English runs whose primary cause is a defect contain rejected actions, against 12 of 47 for gemma (`analysis/acl_rewrite_stats.py`).
- **Layout, to stay within 8 pages without cutting findings:**
  - RQ1+RQ2 tables and RQ3 attribution + corrected-gap tables are now side by side in two full-width bands;
  - short stage names (task level, tool level, control, final answer) are defined in the caption;
  - the TheAgentCompany relabelling note moved from §3.5 to Appendix A;
  - contributions, the Related Work benchmark sentence, two captions and the "Other benchmarks" paragraph were tightened.
