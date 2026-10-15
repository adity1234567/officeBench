# Does Language Matter? — ACL submission package

```
paper/
  main.tex     the full paper
  refs.bib     bibliography (all entries cited; no extras)
  README.md    this file
```

## Building

`main.pdf` is built and current: **12 pages** (8 content + limitations, references and appendix), no LaTeX
errors, no undefined references or citations. `acl.sty` and `acl_natbib.bst` are vendored here
(from <https://github.com/acl-org/acl-style-files>).

This machine has no TeX distribution, so the PDF was produced with
[Tectonic](https://tectonic-typesetting.github.io/) — a single self-contained binary that
fetches only the packages the document needs:

```bash
tectonic -X compile main.tex        # runs LaTeX + BibTeX + LaTeX as needed
```

Any standard toolchain works too:

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

Or drop `main.tex` + `refs.bib` into an Overleaf project made from the ACL template.

`\usepackage[review]{acl}` gives the anonymised, line-numbered submission build (what is
compiled now). Remove `[review]` for camera-ready.

**Do not** add `\bibliographystyle{acl_natbib}` to `main.tex` — `acl.sty` already sets it, and
a second one makes BibTeX abort with *"Illegal, another \bibstyle command"*.

### Page budget
Content runs to page 6; references start on page 7 and the appendix is page 8. ACL counts
references and appendices separately, so there is roughly **two pages of headroom** for figures
or added analysis before hitting the long-paper limit.

## Where the numbers come from

Every figure in the paper is derived from the benchmark's own scorer and the raw trajectories,
not from intermediate summaries:

| Source | What it provides |
|---|---|
| `results/{gemma4_31b_think,gemma4_31b_bn,gpt-oss_20b_en,gpt-oss_20b_bn}_result.jsonl` | authoritative per-subtask pass/fail (written by `evaluation.py`) |
| `tasks/*/outputs/*/<model>_<tag>/env_history.json` | actions and observations per step (failure signals, episode length) |
| `tasks/*/outputs/*/<model>_<tag>/llm_history.json` | prompts and model replies (reasoning) |
| `analysis/paper_stats.json` | the computed table: pass rates, per-app splits, McNemar, failure signals |

All four runs cover the full 300 subtasks. Statistics were re-verified against
`paper_stats.json` before the paper was written.

> Note: `analysis/failure_codes_all_runs.json` is an **earlier** coding snapshot. Its pass
> counts disagree with the official scorer by 2–8% because some episodes were re-run after it
> was produced. The paper deliberately does **not** use it for any reported number; it is kept
> only for the qualitative code vocabulary reproduced in Appendix B.

## Headline results

| Model | Lang | 1-app | 2-app | 3-app | All |
|---|---|---|---|---|---|
| gemma4:31b | EN | 66.7 | 54.7 | 16.1 | **44.0** |
| gemma4:31b | BN | 45.2 | 45.3 | 16.1 | 34.3 |
| gpt-oss:20b | EN | 44.1 | 34.7 | 5.4 | 26.7 |
| gpt-oss:20b | BN | 53.8 | 38.9 | 8.9 | 32.3 |

Paired exact McNemar (300 subtasks, same items both conditions):

| Comparison | b | c | p |
|---|---|---|---|
| gemma EN vs BN | 41 | 12 | 8.2e-05 |
| gpt-oss EN vs BN | 23 | 40 | 0.043 |
| gemma vs gpt-oss (EN) | 67 | 15 | 5.3e-09 |
| gemma vs gpt-oss (BN) | 33 | 27 | 0.52 |

## Figures

`analysis/figures/` holds `fig0_teaser.svg`, `fig1_study_design.svg`, `fig2_failure_coding.svg`,
`fig_pipeline.svg`, `fig_steps.svg`. They are **not yet referenced** in `main.tex`. To include
one, convert it to PDF (`inkscape --export-type=pdf fig.svg` or `rsvg-convert -f pdf`) and add a
`figure` environment. Check that any counts drawn in a figure match the paper's tables before
including it — the figure scripts predate the final runs.

## Not included

A third model (`nemotron-3-nano:30b`, 32B) was mid-evaluation at writing time (~33/300) and is
deliberately absent from all results. The Limitations section says so.
