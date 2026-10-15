#!/usr/bin/env python3
"""Render an OfficeBench run (llm_history.json + env_history.json) as a readable step-by-step trace.

Shows, per step: the INPUT the agent saw (prompt minus the repeated step history), what the
model produced (THINK = raw LLM output), the ACTION executed, and the RESULT (observation).
The header carries the evaluation verdict and, on failure, the first check that failed.
Read this to find out *why* a task passed or failed.

Usage (run from the repo root):
    python history_to_trace.py <output_dir>                      # one run, e.g. tasks/1-1/outputs/0/gemma4_31b_rest
    python history_to_trace.py --tag <model>_<tag>               # every run with that suffix, e.g. gemma4_31b_rest
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def clip(s, n):
    s = '' if s is None else str(s)
    return s if len(s) <= n else s[:n] + f'\n        ... [truncated, {len(s) - n} more chars]'


def indent(s, pad='    '):
    return pad + s.replace('\n', '\n' + pad)


def evaluate(task_id, subtask_id, testbed_dir):
    """Return (passed, reason) using the same checks as evaluation.py."""
    import evaluation
    config = json.load(open(os.path.join(ROOT, 'tasks', task_id, 'subtasks', f'{subtask_id}.json')))
    cwd = os.getcwd()
    os.chdir(ROOT)  # evaluators resolve paths relative to the repo root
    try:
        for item in config['evaluation']:
            fn = getattr(evaluation, item['function'])
            if not fn(testbed_dir, item['args']):
                return False, f"{item['function']} {json.dumps(item['args'])}"
        return True, 'all checks passed'
    except Exception as e:
        return False, f'evaluator error: {e!r}'
    finally:
        os.chdir(cwd)


def split_thought(response):
    """Separate the agent's reasoning from the json command it emitted.

    With the Thought-then-Action prompt the model replies
    `##Thought: <reasoning> ##Command: <json>`; older runs have no marker.
    """
    if response and '##Command:' in response:
        thought = response.split('##Command:', 1)[0]
        return thought.replace('##Thought:', '').strip()
    return (response or '').strip()


def strip_history(prompt):
    # every prompt repeats all previous steps; they are already shown as earlier STEPs
    lines = [l for l in prompt.split('\n') if not l.startswith(' - Step ')]
    return '\n'.join(lines)


def render(output_dir, out_path=None):
    output_dir = os.path.normpath(output_dir)
    parts = output_dir.replace(os.sep, '/').split('/')
    task_id, subtask_id, run_name = parts[-4], parts[-2], parts[-1]

    settings_path = os.path.join(output_dir, 'settings.json')
    settings = json.load(open(settings_path, encoding='utf-8')) if os.path.exists(settings_path) else {}
    llm = json.load(open(os.path.join(output_dir, 'llm_history.json'), encoding='utf-8'))
    env = json.load(open(os.path.join(output_dir, 'env_history.json'), encoding='utf-8'))

    testbed = os.path.relpath(os.path.join(output_dir, 'testbed'), ROOT).replace(os.sep, '/')
    passed, reason = evaluate(task_id, subtask_id, './' + testbed)

    last_action = env[-1][0] if env else None
    if isinstance(last_action, dict) and last_action.get('action') == 'finish_task':
        end = 'agent called finish_task'
    elif isinstance(last_action, dict) and last_action.get('action') == 'got_stuck':
        end = 'agent got stuck (repeated action)'
    else:
        end = f'stopped after {len(env)} actions (max_iter or crash)'

    L = []
    L.append('=' * 78)
    L.append(f'TASK   : {task_id}/{subtask_id}   run: {run_name}   model: {settings.get("model_name", "?")}')
    L.append(f'goal   : {settings.get("task", "?")}')
    L.append(f'score  : {"PASS" if passed else "FAIL"}   [{reason}]')
    L.append(f'steps  : {len(llm)} LLM calls, {len(env)} env actions   end: {end}')
    L.append('=' * 78)
    L.append('Legend:  [INPUT] prompt shown   [THINK] raw LLM output   [ACT] action executed   [RESULT] observation')
    L.append('')

    if llm:
        L.append('--- SYSTEM PROMPT (agent role + apps) ' + '-' * 40)
        L.append(clip(llm[0][0], 1500))
        L.append('')

    # one LLM call per env action; the final got_stuck action is synthesized without an LLM call
    for i in range(max(len(llm), len(env))):
        L.append(f'========== STEP {i + 1} ' + '=' * (66 - len(str(i + 1))))
        if i < len(llm):
            _, prompt, response = llm[i]
            L.append('  [INPUT]')
            L.append(indent(clip(strip_history(prompt), 2500)))
            L.append('  [THINK]')
            L.append(indent(clip(split_thought(response), 3000)))
        if i < len(env):
            action, observation = env[i]
            L.append('  [ACT]')
            L.append(indent(clip(json.dumps(action) if isinstance(action, dict) else action, 2000)))
            L.append('  [RESULT]')
            L.append(indent(clip(observation, 2500)))
        L.append('')

    if out_path is None:
        out_path = os.path.join(output_dir, 'trace.txt')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    return out_path, passed, reason


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(1)
    if a[0] == '--tag':
        dirs = sorted(glob.glob(os.path.join(ROOT, 'tasks', '*', 'outputs', '*', a[1])))
        for d in dirs:
            if os.path.exists(os.path.join(d, 'llm_history.json')):
                path, passed, _ = render(d)
                print('trace written:', os.path.relpath(path, ROOT), 'PASS' if passed else 'FAIL')
    else:
        path, passed, reason = render(a[0], a[1] if len(a) > 1 else None)
        print('trace written:', path, 'PASS' if passed else 'FAIL', reason)


if __name__ == '__main__':
    main()
