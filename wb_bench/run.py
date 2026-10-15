"""Run the WorkBench-on-OfficeBench tasks with one model in EN and BN, then grade.

    python wb_bench/run.py --model_name gemma4:31b --tag wb1 [--only T03.v1] [--langs en,bn]

Mirrors agent_interact.py (same env, policy, prompts, max_iter) with three differences:
/testbed is wiped before each task, the end state is dumped as JSON from inside the container
(email subjects such as 'Catch up soon?' are not valid Windows file names, so docker cp of the
testbed would fail), and each run is graded immediately. Finished runs are skipped on rerun.
"""
import glob
import subprocess
import json
import os
import sys
import time

import fire

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.append(os.path.join(ROOT, 'results'))  # the intercode package lives in results/intercode
os.chdir(ROOT)

from utils.helper import build_docker  # noqa: E402
from utils.env import OfficeAgentEnv  # noqa: E402
from utils.policies import LLMPolicy  # noqa: E402
from utils.llm import safe_model_name  # noqa: E402
from agent_interact import push_llm_config  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, 'wb_bench'))
from evaluate import grade  # noqa: E402
from apps.calendar_app import calendar_delete_event  # noqa: E402


# Upstream bug: delete_event quotes the summary with "..", which is lost when the command is
# wrapped for bash, so 'Vendor call' arrives as 'Vendor', nothing matches, and the app still
# reports success. Quote it the way create_event does. Patched here only; apps/ is untouched.
def _delete_event_action(word_dir, args, py_file_path='/apps/calendar_app/calendar_delete_event.py'):
    return "python3 {} --user '''{}''' --summary '''{}'''".format(py_file_path, args['user'], args['summary'])


calendar_delete_event.construct_action = _delete_event_action

# Second upstream bug, in the copy that runs inside the container: delete_event calls
# calendar.subcomponent.remove (AttributeError, caught, reported as failure), so an existing
# event can never be deleted. The container gets a patched copy of apps/; apps/ is untouched.
PATCHED_APPS = 'wb_bench/apps_patched/'


def make_patched_apps():
    import shutil
    if os.path.exists(PATCHED_APPS):
        shutil.rmtree(PATCHED_APPS)
    shutil.copytree('apps', PATCHED_APPS, ignore=shutil.ignore_patterns('__pycache__'))
    path = os.path.join(PATCHED_APPS, 'calendar_app', 'calendar_delete_event.py')
    src = open(path, encoding='utf-8').read()
    assert 'calendar.subcomponent.remove' in src
    open(path, 'w', encoding='utf-8', newline='\n').write(
        src.replace('calendar.subcomponent.remove', 'calendar.subcomponents.remove'))

DUMP = r'''
import json, glob, os
from icalendar import Calendar
from email import policy
from email.parser import BytesParser
out = {"calendar": [], "emails": []}
p = "/testbed/calendar/Alice.ics"
if os.path.exists(p):
    for c in Calendar.from_ical(open(p, "rb").read()).walk():
        if c.name == "VEVENT":
            s, e = c.get("dtstart"), c.get("dtend")
            out["calendar"].append({"summary": str(c.get("summary")),
                                    "start": s.dt.strftime("%Y-%m-%d %H:%M") if s else "",
                                    "end": e.dt.strftime("%Y-%m-%d %H:%M") if e else ""})
for f in sorted(glob.glob("/testbed/emails/*/*.eml")):
    m = BytesParser(policy=policy.default).parsebytes(open(f, "rb").read())
    body = m.get_body(preferencelist=("plain", "html"))
    out["emails"].append({"id": f, "folder": f.split("/")[-2], "from": str(m["From"]), "to": str(m["To"]),
                          "subject": str(m["Subject"]), "body": body.get_content() if body else ""})
print(json.dumps(out))
'''


def dump_state(env):
    code, out = env.container.exec_run(['python3', '-c', DUMP])
    assert code == 0, out.decode('utf-8', 'replace')
    return json.loads(out.decode('utf-8'))


def run_one(variant, lang, model_name, tag, max_iter, docker_name, container_name):
    task_dir = f'wb_bench/tasks/{variant}'
    out_dir = f'{task_dir}/outputs/{lang}/{safe_model_name(model_name)}_{tag}'
    if os.path.exists(f'{out_dir}/result.json'):
        return json.load(open(f'{out_dir}/result.json', encoding='utf-8'))
    config = json.load(open(f'{task_dir}/subtasks/{lang}.json', encoding='utf-8'))
    expected = json.load(open(f'{task_dir}/expected.json', encoding='utf-8'))

    env = OfficeAgentEnv(image_name=docker_name, container_name=container_name, task=config['task'], verbose=True)
    env.reset()
    env.container.exec_run(['rm', '-rf', '/testbed'])
    env.prepare_docker_env(testbed_dir=f'{task_dir}/testbed/', app_dir='apps/')
    patched = os.path.join(PATCHED_APPS, 'calendar_app', 'calendar_delete_event.py')
    r = subprocess.run(['docker', 'cp', patched, f'{container_name}:/apps/calendar_app/calendar_delete_event.py'],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    push_llm_config(container_name, model_name)
    initial = dump_state(env)
    initial_ids = {m['id'] for m in initial['emails']}

    policy = LLMPolicy(model_name=model_name, key='', env=env, config=config, debug_mode=True, lang=lang)
    t0, n_iter, error = time.time(), 0, None
    try:
        done = False
        while not done:
            n_iter += 1
            action = policy.forward(env)
            _, _, done, _ = env.step(action)
            if n_iter >= max_iter:
                print(f'Max iterations reached: {max_iter}')
                break
    except Exception as e:  # keep the partial run; it is graded on whatever state it left
        error = f'{type(e).__name__}: {e}'
        print('RUN ERROR', error)

    final = dump_state(env)
    os.makedirs(out_dir, exist_ok=True)
    env.dump_history(out_dir)
    policy.dump_history(out_dir)
    passed, reasons = grade(final, expected, initial_ids)
    result = {'variant': variant, 'lang': lang, 'model': model_name, 'tag': tag, 'pass': passed,
              'reasons': reasons, 'steps': n_iter, 'seconds': round(time.time() - t0, 1), 'error': error,
              'task': config['task']}
    with open(f'{out_dir}/final_state.json', 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    with open(f'{out_dir}/result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    env.close()
    return result


def main(model_name='gemma4:31b', tag='wb1', only=None, langs='en,bn', max_iter=20,
         docker_name='officebench', container_name='officebench-wb'):
    build_docker(docker_name, './docker/Dockerfile')
    make_patched_apps()
    variants = sorted(os.path.basename(p) for p in glob.glob('wb_bench/tasks/T*'))
    if only:
        variants = [v for v in variants if v in str(only).split(',')]
    langs = langs.split(',') if isinstance(langs, str) else list(langs)
    results = []
    for v in variants:
        for lang in langs:
            r = run_one(v, lang, model_name, tag, max_iter, docker_name, container_name)
            print(f"RESULT {v} {lang} pass={r['pass']} steps={r['steps']} {r['reasons']}", flush=True)
            results.append(r)
    path = f'wb_bench/results_{safe_model_name(model_name)}_{tag}.jsonl'
    with open(path, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    for lang in langs:
        rs = [r for r in results if r['lang'] == lang]
        print(f'{lang}: {sum(r["pass"] for r in rs)}/{len(rs)} passed')


if __name__ == '__main__':
    fire.Fire(main)
