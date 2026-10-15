import json
import os
import fire
import shutil
from datetime import datetime
import pytz

from utils.helper import build_docker
from utils.env import OfficeAgentEnv
from utils.policies import LLMPolicy
from utils.llm import load_env_file, safe_model_name

from intercode.envs.ic_env import ACTION_EXEC


def push_llm_config(container_name, model_name=None):
    """Copy the agent's model endpoint into the container as /llm_config.json so the
    in-container `llm` app uses the same provider/model as the agent (e.g. gpt-oss:20b via
    Ollama) rather than OpenAI. The api key lives only in this ephemeral file, never in the repo."""
    import subprocess
    import tempfile
    env = load_env_file()
    # For a locally served agent model the container cannot reach the host's 127.0.0.1, so the
    # runner passes OFFICEBENCH_LLM_BASE_URL (e.g. http://host.docker.internal:11434/v1) to keep
    # the in-container llm app on the same model as the agent.
    cfg = {'base_url': os.environ.get('OFFICEBENCH_LLM_BASE_URL', env.get('base_url', '')),
           'api_key': os.environ.get('OFFICEBENCH_LLM_API_KEY', env.get('api_key', '')),
           'model': model_name or env.get('model', 'gpt-3.5-turbo-0125')}
    if not cfg['base_url'] or not cfg['api_key']:
        return  # nothing configured; llm app falls back to /openai_key.txt
    fd, path = tempfile.mkstemp(suffix='.json')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(cfg, f)
        r = subprocess.run(['docker', 'cp', path, f'{container_name}:/llm_config.json'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"Warning: failed to push llm_config to container: {r.stderr}")
    finally:
        os.remove(path)


def main(docker_name='officebench',
         container_name='officebench-debug',
         dockerfile_path='./docker/Dockerfile',
         model_name=None,
         task_dir='tasks/1-1',
         config_file='tasks/1-1/subtasks/0.json',
         task=None,
         tag=None,
         max_iter=20,
         mode='default',
         lang='en'):
    if model_name is None:
        model_name = load_env_file().get('model', 'gpt-4o-2024-05-13')
    build_docker(docker_name, dockerfile_path)

    config = json.load(open(config_file))
    task = config.get('task', task)
    if lang == 'bn':
        # Bangla experiment: feed the model the Bangla task text (from the translation cache
        # built earlier); the English run and its config files are untouched.
        try:
            cache = json.load(open('analysis/bn_cache.json', encoding='utf-8'))
            task = cache.get((task or '').strip(), task)
        except Exception as e:
            print(f"Warning: could not load Bangla task from cache: {e}")
    subtask_id = config_file.split('/')[-1].split('.')[0]
    if tag is None:
        timezone = pytz.timezone('America/Los_Angeles')
        tag = datetime.now(timezone).strftime('%Y%m%d%H%M%S')
    output_dir = f'{task_dir}/outputs/{subtask_id}/{safe_model_name(model_name)}_{tag}'
    
    assert mode in ['force_new', 'use_llm_cache', 'default']
    if mode == 'force_new':
        force_new = True
        use_llm_cache = False
    elif mode == 'use_llm_cache':
        force_new = False
        use_llm_cache = True
    else:
        force_new = False
        use_llm_cache = False

    if os.path.exists(output_dir) and use_llm_cache and not force_new:
        assert os.path.exists(f'{output_dir}/llm_history.json'), f"LLM history not found: {output_dir}/llm_history.json"
        llm_cache = {}
        llm_history = json.load(open(f'{output_dir}/llm_history.json'))
        for item in llm_history:
            llm_cache[item[1]] = item[2]
    else:
        llm_cache = None

    if os.path.exists(output_dir) and not force_new and not use_llm_cache:
        print(f"Output directory already exists: {output_dir}")
        return
    
    if os.path.exists(output_dir) and force_new:
        print(f"Force new mode: removing existing output directory: {output_dir}")
        shutil.rmtree(output_dir)

    env = OfficeAgentEnv(image_name=docker_name, 
                         container_name=container_name,
                         task=task,
                         verbose=True)
    env.reset()
    env.prepare_docker_env(
        testbed_dir=f'{task_dir}/testbed/',
        app_dir=f'apps/',
    )
    push_llm_config(container_name, model_name)
    env.cache_docker_status(local_cache_dir=f'{task_dir}/cache/{subtask_id}/')

    if 'gpt' in model_name and 'oss' not in model_name:
        api_key = open('openai_key.txt').read().strip()
    elif 'gemini' in model_name:
        api_key = open('gemini_key.txt').read().strip()
    else:
        api_key = ""

    policy = LLMPolicy(
        model_name=model_name,
        key=api_key,
        env=env,
        config=config,
        llm_cache=llm_cache,
        debug_mode=True,
        lang=lang,
    )
    try:
        obs = env.observation
        done = False
        n_iter = 0
        while not done:
            n_iter += 1
            action = policy.forward(env)
            obs, reward, done, info = env.step(action)
            if n_iter >= max_iter:
                print(f"Max iterations reached: {max_iter}")
                break
    except KeyboardInterrupt:
        print("Exiting InterCode environment...")
    
    os.makedirs(output_dir, exist_ok=True)
    env.cache_docker_status(local_cache_dir=output_dir)
    env.dump_history(output_dir)
    policy.dump_history(output_dir)
    with open(f'{output_dir}/settings.json', 'w') as f:
        json.dump(config | {'model_name': model_name}, f, indent=2)
    
    env.close()

if __name__ == '__main__':
    fire.Fire(main)
