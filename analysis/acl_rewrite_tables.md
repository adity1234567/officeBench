# Tables for paper_acl/main.tex

## RQ1: seven comparisons (Holm across seven)

| bench | model | n | EN | BN | gap | 95% CI | MELR | EN-only | BN-only | p | p_Holm | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OB | gemma4-31b | 300 | 50.3 | 42.3 | +8.0 | [3.0, 13.0] | 15.9 | 42 | 18 | 0.0027 | 0.016 | computed |
| OB | gpt-oss-20b | 300 | 28.7 | 35.3 | -6.7 | [-12.0, -1.3] | -23.3 | 25 | 45 | 0.0225 | 0.112 | computed |
| WB | gemma4-31b | 90 | 81.1 | 82.2 | -1.1 | [-10.0, 7.8] | -1.4 | 7 | 8 | 1.0000 | 1.000 | WORKBENCH report |
| WB | gpt-oss-20b | 90 | 58.9 | 53.3 | +5.6 | [-5.6, 16.7] | 9.4 | 15 | 10 | 0.4244 | 1.000 | WORKBENCH report |
| tau2 | gemma4-31b | 218 | 49.5 | 38.1 | +11.5 | [5.0, 17.4] | 23.1 | 40 | 15 | 0.0010 | 0.007 | TAU2 report |
| tau2 | gpt-oss-20b | 149 | 38.9 | 39.6 | -0.7 | [-10.7, 8.7] | -1.7 | 26 | 27 | 1.0000 | 1.000 | TAU2 report |
| TAC | gemma4-31b | 23 | 39.1 | 26.1 | +13.0 | [0.0, 26.1] | 33.3 | 3 | 0 | 0.2500 | 1.000 | TAC report |

## OfficeBench by number of apps (Holm across three, per model)

- gemma 1-app: n=93 EN 67.7 BN 51.6 EN-only 18 BN-only 3 p=0.001 p_Holm=0.004
- gemma 2-app: n=95 EN 63.2 BN 53.7 EN-only 16 BN-only 7 p=0.093 p_Holm=0.186
- gemma 3-app: n=112 EN 25.0 BN 25.0 EN-only 8 BN-only 8 p=1.000 p_Holm=1.000
- gptoss 1-app: n=93 EN 44.1 BN 53.8 EN-only 9 BN-only 18 p=0.122 p_Holm=0.244
- gptoss 2-app: n=95 EN 38.9 BN 43.2 EN-only 14 BN-only 18 p=0.597 p_Holm=0.597
- gptoss 3-app: n=112 EN 7.1 BN 13.4 EN-only 2 BN-only 9 p=0.065 p_Holm=0.196

## Model gap on OfficeBench

{"EN": {"gemma_only": 82, "gptoss_only": 17, "p": 2.180641080014394e-11}, "BN": {"gemma_only": 48, "gptoss_only": 27, "p": 0.020298406990107445}, "gptoss_losses_EN": {"tasks": 82, "with_malformed_action": 80, "ended_stuck": 18, "ended_at_step_limit": 24, "primary_code_FMT": 33}}

## Trajectory measurements (OfficeBench)

- gemma-EN: {"runs_with_history": 299, "malformed_actions_total": 273, "out_of_steps_failures_by_apps": {"1": 3, "2": 5, "3": 38}, "failures": 149, "out_of_steps_no_rejected_step": 13, "out_of_steps_half_or_more_rejected": 9, "runs_with_write": 180, "runs_write_verified": 3, "failed_steps": 284, "failed_steps_followed_by_identical_action": 30, "runs_with_failed_step": 71, "runs_with_3plus_identical_rejected_actions": 9}
- gemma-BN: {"runs_with_history": 299, "malformed_actions_total": 194, "out_of_steps_failures_by_apps": {"1": 5, "2": 4, "3": 30}, "failures": 173, "out_of_steps_no_rejected_step": 21, "out_of_steps_half_or_more_rejected": 10, "runs_with_write": 178, "runs_write_verified": 4, "failed_steps": 213, "failed_steps_followed_by_identical_action": 34, "runs_with_failed_step": 42, "runs_with_3plus_identical_rejected_actions": 9}
- gptoss-EN: {"runs_with_history": 299, "malformed_actions_total": 1671, "out_of_steps_failures_by_apps": {"1": 14, "2": 18, "3": 49}, "failures": 214, "out_of_steps_no_rejected_step": 0, "out_of_steps_half_or_more_rejected": 44, "runs_with_write": 112, "runs_write_verified": 20, "failed_steps": 1640, "failed_steps_followed_by_identical_action": 283, "runs_with_failed_step": 282, "runs_with_3plus_identical_rejected_actions": 60}
- gptoss-BN: {"runs_with_history": 299, "malformed_actions_total": 955, "out_of_steps_failures_by_apps": {"1": 8, "2": 13, "3": 37}, "failures": 194, "out_of_steps_no_rejected_step": 1, "out_of_steps_half_or_more_rejected": 9, "runs_with_write": 155, "runs_write_verified": 19, "failed_steps": 949, "failed_steps_followed_by_identical_action": 64, "runs_with_failed_step": 261, "runs_with_3plus_identical_rejected_actions": 12}

## Bangla-script final answers among failures

{"gemma-BN": {"failures": 173, "bangla_script_answers": 46}, "gptoss-BN": {"failures": 194, "bangla_script_answers": 7}}

## Translation audit (instructions used in the Bangla runs)

{"instructions": 298, "translated": 298, "with_bengali_digits": 44, "with_ascii_digits": 50, "with_both_digit_scripts": 14, "name_mentions": 103, "name_mentions_kept_latin": 43, "file_tokens": 262, "file_tokens_changed": 1}

## Confound shares

{"counts": {"C1": 24, "C2": 35, "C3": 9, "C4": 8, "C5": 22, "C6": 45, "C7": 20}, "total": 163, "evaluation_side_pct": 45.4, "agent_pct": 42.3, "unclear_pct": 12.3, "bangla_specific_range_pct": [14.7, 27.0, 54.6]}