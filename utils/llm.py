import os
import json
from openai import OpenAI
import time
import numpy as np
import google.generativeai as genai


def load_env_file():
    # read `key = "value"` lines from .env in OfficeBench/ or its parent directory
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path in [os.path.join(root, '.env'), os.path.join(os.path.dirname(root), '.env')]:
        if os.path.exists(path):
            values = {}
            for line in open(path, encoding='utf-8'):
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                values[key.strip()] = value.strip().strip('"').strip("'")
            return values
    return {}


def safe_model_name(model_name):
    # model names like `gemma4:31b` or `Qwen/Qwen2.5-7B` are used in paths
    return model_name.replace('/', '_').replace(':', '_')


class ChatGPT:
    def __init__(self, model_name, key, system_message=None):
        self.model_name = model_name
        self.key = key
        self.system_message = system_message
        
        self.client = OpenAI(
            api_key=key
        )
                

    def get_model_options(
        self,
        temperature=0,
        per_example_max_decode_steps=1024,
        per_example_top_p=1,
        n_sample=1,
    ):
        return dict(
            temperature=temperature,
            n=n_sample,
            top_p=per_example_top_p,
            max_tokens=per_example_max_decode_steps,
        )

    def generate_plus_with_score(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        messages = [
            {
                "role": "system",
                "content": (
                    "I will give you some examples, you need to follow the examples and complete the text, and no other content."
                    if self.system_message is None
                    else self.system_message
                ),
            },
            {"role": "user", "content": prompt},
        ]
        gpt_responses = None
        retry_num = 0
        retry_limit = 2
        error = None
        while gpt_responses is None:
            try:
                gpt_responses = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stop=end_str,
                    **options,
                )
                error = None
            except Exception as e:
                print(str(e), flush=True)
                error = str(e)
                if "This model's maximum context length is" in str(e):
                    print(e, flush=True)
                    gpt_responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                elif retry_num > retry_limit:
                    error = "too many retry times"
                    gpt_responses = {
                        "choices": [{"message": {"content": "PLACEHOLDER"}}]
                    }
                else:
                    time.sleep(60)
                retry_num += 1
        if error:
            raise Exception(error)
        results = []
        for i, res in enumerate(gpt_responses["choices"]):
            text = res["message"]["content"]
            fake_conf = (len(gpt_responses["choices"]) - i) / len(
                gpt_responses["choices"]
            )
            results.append((text, np.log(fake_conf)))

        return results

    def generate(self, prompt, options=None, end_str=None):
        if options is None:
            options = self.get_model_options()
        options["n"] = 1
        result = self.generate_plus_with_score(prompt, options, end_str)[0][0]
        return result


class Gemini:
    # gemini-1.0-pro
    # gemini-1.5-pro
    def __init__(self, model_name, key, system_message=None):
        self.model_name = model_name
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(model_name)
        self.system_message = system_message

    def generate(self, prompt):
        combined_prompt = (
            f"{self.system_message}\n\n{prompt}" if self.system_message else prompt
        )
        response = self.model.generate_content(
            combined_prompt,
            generation_config=genai.types.GenerationConfig(
                # Only one candidate for now.
                candidate_count=1,
                max_output_tokens=1024,
                temperature=1.0,
            ),
        )
        return response.text


class vLLM:
    def __init__(self, model_name, system_message=None):
        self.model_name = model_name
        self.system_message = system_message
        env = load_env_file()
        self.client = OpenAI(
            base_url=os.environ.get("VLLM_BASE_URL", env.get("base_url", "http://localhost:8000/v1")),
            api_key=os.environ.get("VLLM_API_KEY", env.get("api_key", "token-abc123")),
        )
    
    def get_model_options(
        self,
        temperature=0,
        per_example_max_decode_steps=2048,
        per_example_top_p=1,
        n_sample=1,
    ):
        # reasoning models (e.g. gpt-oss) spend many tokens on their reasoning channel
        # before emitting the action, so the budget must be generous or content comes back empty
        return dict(
            temperature=temperature,
            n=n_sample,
            top_p=per_example_top_p,
            max_tokens=per_example_max_decode_steps,
        )

    def generate(self, prompt):
        try:
            options = self.get_model_options()
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": prompt},
                ],
                **options,
            )
            message = completion.choices[0].message
            content = message.content or ''
            if not content and message.tool_calls:
                # Ollama may parse the JSON action as a native tool call named
                # `app:action`, leaving content empty; rebuild the action text
                call = message.tool_calls[0].function
                app, _, action = call.name.partition(':')
                args = json.loads(call.arguments or '{}')
                return json.dumps({'app': app, 'action': action, **args})
            # reasoning models return their thinking in a separate `reasoning` field; fold it
            # into the Thought/Command format so the thinking is logged and the action still parses
            reasoning = getattr(message, 'reasoning', None) or ''
            if reasoning and '##Command:' not in content:
                return f"##Thought: {reasoning.strip()}\n##Command: {content.strip()}"
            return content
        except Exception as e:
            print("Generation Error:", e)
            return "None"
