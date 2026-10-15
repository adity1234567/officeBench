# OfficeBench failure codebook (v1, 2026-09-29)

Unit of analysis: one scored task run (`task_id/subtask_id` + run tag).
Each case gets exactly **one primary code** (the root cause) and any number of **contributing tags**.

## Decision procedure (apply in order)

1. **Is the agent's final output correct for the task as written?**
   Judge meaning, not surface form: read the task text, the initial files, the agent's actions and the final files.
   - If the final files differ from what the agent's *successful* actions wrote → go to 2.
   - If the output is correct (or semantically equivalent) but the case was scored FAIL → go to 3.
   - If the output is wrong → go to 4.
2. **Environment** → `ENV-TOOL`.
3. **Evaluator** → choose `EVAL-CRASH`, `EVAL-MISMATCH` or `EVAL-FORM`.
4. **Agent** → find the *decisive step*: the earliest step that, if it alone were corrected, would most likely have made the run succeed. Code that step with one `A-*` code.

A case scored PASS whose output is actually wrong is coded by step 4 and gets the tag `C-WEAKCHECK`.

## Primary codes

| Code | Definition | Include | Exclude |
|---|---|---|---|
| `ENV-TOOL` | A benchmark app/tool corrupts, drops or misreports an action the agent issued correctly. | Tool reports success but the saved file lacks the written value. | Agent wrote the wrong value. |
| `EVAL-CRASH` | The evaluation function errors and cannot score the output. | Exception while opening/reading the file. | Check runs and returns False. |
| `EVAL-MISMATCH` | The check requires something the task text does not ask for, or reads a different file than the task names. | Checker file ≠ task file; extra required item not in task. | Requirement stated in the task but missed by the agent. |
| `EVAL-FORM` | The output is semantically equivalent to what the task asks; the check rejects only surface form that the task does not fix (leading zeros, %, sign convention, number formatting). | `08:00` vs `8:00`; `-10%` for "reduce 10%". | A label or value the task states literally and the agent changed (→ `A-DEVIATION`). |
| `A-INTENT` | Agent misreads what the task asks it to do: wrong goal, wrong operation, or treats an action task as a question. | Answers in text instead of writing; edits an existing row instead of adding one; ignores a qualifier like "for each day". | Right operation, wrong numbers (→ `A-REASON`). |
| `A-DEVIATION` | Agent performs the right operation but changes a value or name the task states explicitly. | Task says "utilities fee", agent writes "utilities". | Surface-format differences (→ `EVAL-FORM`). |
| `A-STATE` | Agent ignores information it observed in the environment that constrains the answer. | Books a slot it just saw is occupied. | Never looked at the state (→ `A-INTENT` or `A-REASON`). |
| `A-REASON` | Calculation, counting, comparison or logic error on correctly read data. | Wrong average, wrong sum, miscounted items. | Misread instruction (→ `A-INTENT`). |
| `A-ACTION` | Invalid, hallucinated or repeated actions stop progress (malformed JSON, non-existent action, loop until `got_stuck`). | Loop of rejected actions ends the run. | Isolated malformed step the agent recovers from. |

## Contributing tags

| Tag | Meaning |
|---|---|
| `C-LLMAPP` | The in-container `llm` app failed (missing API key) during the run. |
| `C-WEAKCHECK` | The check would accept a wrong answer (e.g., keyword appears anywhere). |
| `C-HARNESS` | Harness/integration problem in this or an earlier attempt (encoding crash, empty reply from tool-call parsing, malformed step caused by the harness). |
| `C-AMBIG` | The task text admits more than one reasonable reading. |

## Grouping (for fishbone and fault tree)

- **Benchmark side:** `ENV-TOOL`, `EVAL-CRASH`, `EVAL-MISMATCH`, `EVAL-FORM`
- **Agent side:** `A-INTENT`, `A-DEVIATION`, `A-STATE`, `A-REASON`, `A-ACTION`
