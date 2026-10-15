# TheAgentCompany — per-task logging & tracing runbook

This document explains two things:

1. **How to watch the log of a task that is running right now.**
2. **How to reproduce the per-task trace setup** so that every task writes a readable
   `trace_<task>.txt` (full `input → think → act → result` for every agent step), which is
   what you read to find out *why* a task passed or failed.

It is written so that another engineer — or Claude working in another copy of this repo —
can set it up from scratch. File paths below are relative to the `tac-docker/` folder unless
noted; the OpenHands harness repo is the sibling `TheAgentCompany/` folder.

---

## 0. Background: where the data already lives

You do **not** need any external tracing service (LangSmith, etc.) to see what the agent did.
OpenHands already writes a complete **trajectory** for every task:

- `run_eval.py` sets `save_trajectory_path=.../traj_<task>.json` (see
  `TheAgentCompany/evaluation/run_eval.py`, in `get_config`).
- The trajectory is a JSON **list of events** in order. Each agent action event carries the
  model's own reasoning in a `thought` field, plus the action itself; each result is an
  `observation` event. So the file contains, per step:
  `thought (THINK) → command/browser/python (ACT) → observation (RESULT)`.
- The score is in the sibling `eval_<task>.json` (`final_score` + per-checkpoint `checkpoints`).

Because everything is in `traj_<task>.json`, a trace can be rendered **at any time**, during
the run or long after — you never have to re-run a task just to get its trace.

Output files for a run live in the folder passed as `--outputs-path` (e.g.
`TheAgentCompany/evaluation/outputs_set2/`):

```
traj_<task>-image.json    # raw trajectory (every event)
eval_<task>-image.json    # score + checkpoints
state_<task>-image.json   # final agent state
trace_<task>-image.txt    # readable trace (produced by this setup)
screenshots/<task>/       # browser screenshots
```

---

## 1. Watch a running task's log

The run is launched in the harness container and its stdout is redirected to a log file on the
host, e.g. `tac-docker/run-set2d.log`. The agent's live reasoning is **not** in that stdout —
stdout only shows harness/OpenHands lifecycle lines. The agent's thoughts land in
`traj_<task>.json`, which is written **when the task finishes**. So "watching live" means two
different things:

### 1a. Follow the run's lifecycle (which task, scores as they land)

```bash
# which task is running, every score, every trace written, retries, and the end
grep -aE "^Running |final_score|trace written|attempt .* no result|Evaluation run finished" \
    tac-docker/run-set2d.log | tail -8
```

Is the run process still alive, and is it actually doing work (vs. a stalled build)?

```bash
docker exec tac-harness ps aux | grep -c "[r]un_eval.py"   # 2 = alive, 0 = dead
docker exec tac-harness sh -c 'cat /proc/loadavg'          # ~1-3 = working, ~0 = stalled build
docker exec tac-harness ps -eo etime,cmd | grep "[b]uildx build"  # how long the image build has run
```

### 1b. See a finished task's full reasoning

As soon as a task completes, its `traj_` and `trace_` files appear in the outputs folder:

```bash
ls -t TheAgentCompany/evaluation/outputs_set2/trace_*.txt | head
less TheAgentCompany/evaluation/outputs_set2/trace_<task>-image.txt
```

### 1c. See the live score as JSON

```bash
python - <<'PY'
import json
e=json.load(open("TheAgentCompany/evaluation/outputs_set2/eval_<task>-image.json"))
print(e["final_score"], [c["result"] for c in e["checkpoints"]])
PY
```

> There is no true token-by-token live stream of the agent while a single task is mid-flight —
> OpenHands flushes the trajectory at task end. If you need live LLM-call streaming, that is the
> one case where an external tracer (LangSmith via LiteLLM callback) adds something; for failure
> analysis the per-task trace is enough.

---

## 2. Reproduce the per-task tracing (do this once)

Two pieces: a **renderer script** and a **one-line hook** in the runner.

### 2a. Add the renderer `harness/traj_to_trace.py`

Create `tac-docker/harness/traj_to_trace.py` with exactly this content:

```python
#!/usr/bin/env python3
"""Render an OpenHands trajectory (traj_<task>.json) as a readable step-by-step trace.

Shows, per step: the agent's THINKING (`thought`), the ACTION (bash/python/browser/message),
and the RESULT (observation). Read this to find out *why* a task failed.

Usage:
    python traj_to_trace.py <traj.json> [<out.txt>]   # one file
    python traj_to_trace.py --dir <outputs_dir>        # every traj_*.json in a dir
"""
import json
import os
import sys
import glob


def clip(s, n):
    s = '' if s is None else str(s)
    return s if len(s) <= n else s[:n] + f'\n        ... [truncated, {len(s) - n} more chars]'


def render(traj_path, out_path=None):
    with open(traj_path, encoding='utf-8') as f:
        traj = json.load(f)

    task = os.path.basename(traj_path).replace('traj_', '').replace('.json', '')
    eval_path = os.path.join(os.path.dirname(traj_path), f'eval_{task}.json')
    score_line = 'score: (no eval file found)'
    if os.path.exists(eval_path):
        try:
            e = json.load(open(eval_path, encoding='utf-8'))
            fs = e.get('final_score', {})
            cps = ' '.join(f"cp{i + 1}={c['result']}/{c['total']}" for i, c in enumerate(e.get('checkpoints', [])))
            score_line = f"score: {fs.get('result')} / {fs.get('total')}   [{cps}]"
        except Exception as ex:
            score_line = f'score: (could not read eval file: {ex})'

    L = []
    L.append('=' * 78)
    L.append(f'TASK   : {task}')
    L.append(f'{score_line}')
    L.append(f'steps  : {len(traj)} trajectory entries')
    L.append('=' * 78)
    L.append('Legend:  [THINK] LLM reasoning   [ACT] action taken   [RESULT] observation')
    L.append('')

    step = 0
    for h in traj:
        kind = h.get('action')
        args = h.get('args') or {}
        obs = h.get('observation')

        if kind == 'system':
            L.append('--- SYSTEM PROMPT (agent role + tools) ' + '-' * 39)
            L.append(clip(args.get('content'), 1500))
            L.append('')
            continue

        if kind == 'message':
            src = h.get('source', '')
            L.append(f'--- INPUT / MESSAGE (from {src}) ' + '-' * 44)
            L.append(clip(args.get('content'), 4000))
            L.append('')
            continue

        if obs is not None:
            if obs == 'recall':
                continue
            label = {'run': 'bash output', 'browse': 'browser page', 'run_ipython': 'python output'}.get(obs, obs)
            success = h.get('success')
            tail = '' if success is None else f'  (success={success})'
            L.append(f'    [RESULT: {label}]{tail}')
            L.append('    ' + clip(h.get('content'), 2500).replace('\n', '\n    '))
            L.append('')
            continue

        thought = args.get('thought') or args.get('final_thought') or ''
        if kind in ('run', 'browse_interactive', 'run_ipython', 'finish', 'recall'):
            step += 1
            L.append(f'========== STEP {step} :: {kind} ' + '=' * (52 - len(str(step)) - len(kind)))
            if thought.strip():
                L.append('  [THINK]')
                L.append('    ' + clip(thought, 3000).replace('\n', '\n    '))
            if kind == 'run':
                L.append('  [ACT: bash]')
                L.append('    $ ' + clip(args.get('command'), 2000).replace('\n', '\n      '))
            elif kind == 'run_ipython':
                L.append('  [ACT: python]')
                L.append('    ' + clip(args.get('code'), 2000).replace('\n', '\n    '))
            elif kind == 'browse_interactive':
                L.append('  [ACT: browser]')
                L.append('    ' + clip(args.get('browser_actions'), 1500).replace('\n', '\n    '))
            elif kind == 'finish':
                L.append('  [ACT: finish]  task_completed=' + str(args.get('task_completed')))
                if args.get('final_thought') and not thought.strip():
                    L.append('    ' + clip(args.get('final_thought'), 3000).replace('\n', '\n    '))
            L.append('')

    if out_path is None:
        out_path = traj_path.replace('traj_', 'trace_').replace('.json', '.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    return out_path


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    if a[0] == '--dir':
        for p in sorted(glob.glob(os.path.join(a[1], 'traj_*.json'))):
            print('wrote', render(p))
    else:
        print('wrote', render(a[0], a[1] if len(a) > 1 else None))


if __name__ == '__main__':
    main()
```

> If the trajectory schema differs in your OpenHands version, check the field names once with:
> `python -c "import json;d=json.load(open('traj_X.json'));print({k for h in d for k in h})"`
> and confirm action events carry `args.thought`, `args.command` / `args.browser_actions` /
> `args.code`, and that results are `observation` events with `content`.

### 2b. Hook it into the runner

The harness directory is mounted into the container at `/opt/tac-docker` (see
`docker-compose.yml`: `- .:/opt/tac-docker`). In the task loop of
`harness/run_eval_safe.sh`, **after** the task's `run_eval.py` call and **before** the runtime
cleanup, add:

```bash
    # Render a readable per-task trace (think -> act -> result for every step) next to the
    # trajectory, so a failure can be diagnosed without parsing the raw JSON.
    if [ -f "$OUTPUTS_PATH/traj_${task_name}-image.json" ]; then
        python /opt/tac-docker/harness/traj_to_trace.py \
            "$OUTPUTS_PATH/traj_${task_name}-image.json" \
            "$OUTPUTS_PATH/trace_${task_name}-image.txt" 2>/dev/null \
            && echo "trace written: trace_${task_name}-image.txt"
    fi
```

That is the whole integration. From then on every finished task drops a `trace_*.txt` beside
its trajectory, and the run log prints `trace written: ...`.

> **Windows gotcha:** keep `run_eval_safe.sh` LF-only. A CRLF edit breaks it with
> `$'\r': command not found`. Fix with:
> `python - <<'PY'\nb=open('harness/run_eval_safe.sh','rb').read().replace(b'\r\n',b'\n');open('harness/run_eval_safe.sh','wb').write(b)\nPY`

### 2c. Backfill traces for tasks already run

Any task that already has a `traj_*.json` can be traced retroactively — no re-run needed:

```bash
# one task
python tac-docker/harness/traj_to_trace.py \
    TheAgentCompany/evaluation/outputs_set2/traj_<task>-image.json

# every task in a folder
python tac-docker/harness/traj_to_trace.py --dir TheAgentCompany/evaluation/outputs_set2
```

---

## 3. Reading a trace to classify a failure

Open `trace_<task>-image.txt`. The header shows the score and per-checkpoint pass/fail. Then
read the steps. Decide which of three buckets the failure is in:

| Category | Signature in the trace | Whose fault |
|---|---|---|
| **Reasoning error** | tools succeed, but the plan/judgment is wrong (wrong file chosen, wrong boundary, gives up, skips a required step, claims done without verifying) | the agent/model |
| **Execution / tooling failure** | an action errors and the agent can't recover (auth rejected, bad command) — **but a working path exists** | usually the agent (chose the wrong method) |
| **Environment fault** | server down, file missing, auth broken *even in the browser*, wrong host | your setup |
| **Benchmark fault** | wrong answer key, grader checks something impossible, missing seed file | the benchmark |

To separate "environment fault" from "agent fault" on an execution failure: check whether
**another task in the same run used the same resource successfully**. If yes, the environment is
fine and the agent simply chose a method that doesn't work.

---

## 4. Quick reference — commands

```bash
# live lifecycle of the current run
grep -aE "^Running |final_score|trace written|Evaluation run finished" tac-docker/run-<run>.log | tail

# is it alive / working?
docker exec tac-harness ps aux | grep -c "[r]un_eval.py"
docker exec tac-harness sh -c 'cat /proc/loadavg'

# done/pending + scores for a known task list
cd TheAgentCompany/evaluation/outputs_set2
for t in <task1> <task2> ...; do
  [ -f eval_${t}-image.json ] && \
  python -c "import json;d=json.load(open('eval_${t}-image.json'));print('$t',d['final_score'])"
done

# render / re-render traces
python tac-docker/harness/traj_to_trace.py --dir TheAgentCompany/evaluation/outputs_set2
```
