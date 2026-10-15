import json
import apps

from utils.llm import ChatGPT, Gemini, vLLM

import logging


class BasePolicy:
    def __init__(self):
        pass

    def forward(self, *args, **kwargs):
        raise NotImplementedError
    
class HumanPolicy(BasePolicy):
    def __init__(self):
        super().__init__()
    
    def forward(self, query, observation, available_actions):
        action = input('> ')
        return action


PROMPT_DICT = {
    'prompt_undecided_app': (
        '##Task: {task}\n'
        '##Available apps: {available_apps}\n'
        '##Instruction:\n'
        " - choose an app from the avaiblable apps: {{'app': 'system', 'action': 'switch_app', 'target_app': [THE_APP_YOU_CHOOSE]}}\n"
        '##Format: write "##Thought:" then your reasoning, then "##Command:" then one json action.\n'
        '##Thought:'
    ),
    'prompt_undecided_app_w_history': (
        '##Task: {task}\n'
        '##History:\n'
        '{history}'
        '##Available apps: {available_apps}\n'
        '##Instruction:\n'
        " - choose an app from the avaiblable apps: {{'app': 'system', 'action': 'switch_app', 'target_app': [THE_APP_YOU_CHOOSE]}}\n"
        '##Format: write "##Thought:" then your reasoning, then "##Command:" then one json action.\n'
        '##Thought:'
    ),
    'prompt_decided_app': (
        '##Task: {task}\n'
        '##History:\n'
        '{history}'
        '##Current apps: {current_app}\n'
        '##Instruction: Choose one action from the list as the next step.\n'
        '{detailed_instruction}'
        " - switch to another app among {available_apps}: {{'app': 'system', 'action': 'switch_app', 'target_app': [THE_APP_YOU_CHOOSE]}}\n"
        " - finish the task with your answer as None if the task is not a question: {{'app': 'system', 'action': 'finish_task', 'answer': 'None'}}\n"
        " - finish the task with your answer if the task is a question: {{'app': 'system', 'action': 'finish_task', 'answer': [ANSWER]}}\n"
        '##Format: write "##Thought:" then your reasoning, then "##Command:" then one json action.\n'
        '##Thought:'
    )
}

# Bangla app descriptions (app key stays English; it is the switch_app target).
APP_INTRO_BN = {
    'calendar': 'calendar: ক্যালেন্ডারে প্রতিদিনের ইভেন্ট পরিচালনার অ্যাপ।',
    'excel': 'excel: এক্সেল ফাইল পরিচালনার (পড়া, লেখা ইত্যাদি) অ্যাপ।',
    'ocr': 'ocr: ছবি থেকে টেক্সট শনাক্ত করার অ্যাপ।',
    'pdf': 'pdf: পিডিএফ ফাইল পরিচালনার (ফরম্যাট রূপান্তর ও পড়া) অ্যাপ।',
    'shell': 'shell: সিস্টেমে শেল কমান্ড চালানোর অ্যাপ।',
    'word': 'word: ওয়ার্ড ফাইল পরিচালনার (পড়া, লেখা, রূপান্তর ইত্যাদি) অ্যাপ।',
    'email': 'email: ইমেইল পরিচালনার (পাঠানো, পড়া) অ্যাপ।',
    'llm': 'llm: প্রশ্নের উত্তর দেওয়া বা টেক্সট তৈরির জন্য large language model-এর সাথে ইন্টারঅ্যাক্ট করার অ্যাপ।',
}

# Bangla prompt templates. Labels are Bangla; the JSON action schema stays English, and the
# ##Thought/##Command markers are unchanged (the parser keys on them).
PROMPT_DICT_BN = {
    'prompt_undecided_app': (
        '##টাস্ক: {task}\n'
        '##উপলব্ধ অ্যাপ: {available_apps}\n'
        '##নির্দেশনা:\n'
        " - উপলব্ধ অ্যাপ থেকে একটি অ্যাপ বেছে নিন: {{'app': 'system', 'action': 'switch_app', 'target_app': [THE_APP_YOU_CHOOSE]}}\n"
        '##ফরম্যাট: আগে "##Thought:" দিয়ে যুক্তি, তারপর "##Command:" দিয়ে একটি json অ্যাকশন লিখুন।\n'
        '##Thought:'
    ),
    'prompt_undecided_app_w_history': (
        '##টাস্ক: {task}\n'
        '##ইতিহাস:\n'
        '{history}'
        '##উপলব্ধ অ্যাপ: {available_apps}\n'
        '##নির্দেশনা:\n'
        " - উপলব্ধ অ্যাপ থেকে একটি অ্যাপ বেছে নিন: {{'app': 'system', 'action': 'switch_app', 'target_app': [THE_APP_YOU_CHOOSE]}}\n"
        '##ফরম্যাট: আগে "##Thought:" দিয়ে যুক্তি, তারপর "##Command:" দিয়ে একটি json অ্যাকশন লিখুন।\n'
        '##Thought:'
    ),
    'prompt_decided_app': (
        '##টাস্ক: {task}\n'
        '##ইতিহাস:\n'
        '{history}'
        '##বর্তমান অ্যাপ: {current_app}\n'
        '##নির্দেশনা: পরবর্তী পদক্ষেপ হিসেবে তালিকা থেকে একটি অ্যাকশন বেছে নিন।\n'
        '{detailed_instruction}'
        " - {available_apps} এর মধ্যে অন্য একটি অ্যাপে সুইচ করুন: {{'app': 'system', 'action': 'switch_app', 'target_app': [THE_APP_YOU_CHOOSE]}}\n"
        " - টাস্কটি প্রশ্ন না হলে উত্তর None দিয়ে শেষ করুন: {{'app': 'system', 'action': 'finish_task', 'answer': 'None'}}\n"
        " - টাস্কটি প্রশ্ন হলে উত্তর দিয়ে শেষ করুন: {{'app': 'system', 'action': 'finish_task', 'answer': [ANSWER]}}\n"
        '##ফরম্যাট: আগে "##Thought:" দিয়ে যুক্তি, তারপর "##Command:" দিয়ে একটি json অ্যাকশন লিখুন।\n'
        '##Thought:'
    )
}


class LLMPolicy(BasePolicy):
    def __init__(self, model_name, key, env, config, llm_cache=None, debug_mode=False, lang='en'):
        super().__init__()

        self.lang = lang  # 'en' or 'bn' (Bangla system prompt + instructions; JSON actions stay English)
        self.system_message = self.construct_system_message(config, env.available_apps)
        if 'gpt' in model_name and 'oss' not in model_name:
            self.llm = ChatGPT(model_name, key, self.system_message)
        elif 'gemini' in model_name:
            self.llm = Gemini(model_name, key, self.system_message)
        else:
            self.llm = vLLM(model_name, self.system_message)
            
        self.llm_history = []

        self.action_window = []
        self.action_window_size = 5

        self.llm_cache = llm_cache

        self.logger = logging.getLogger(__name__)

        self.debug_mode = debug_mode

    def dump_history(self, output_dir):
        with open(f'{output_dir}/llm_history.json', 'w') as f:
            json.dump(self.llm_history, f, indent=2)

    def construct_system_message(self, config, available_apps):
        username = config['username']
        date = config['date']
        weekday = config['weekday']
        time = config['time']
        if self.lang == 'bn':
            return self.construct_system_message_bn(available_apps, username, date, weekday, time)
        app_introduction = ''
        for app in available_apps:
            app_introduction += f' - {apps.AVAILABLE_APPS[app].INTRO}\n'
        system_message = (
            f"Today is {date} ({weekday}). The current time is {time}. You are an AI assistant for user {username}.\n"
            "You can help solve the task step by step.\n"
            "You can interact with an operation system and use apps to solve the task.\n"
            "You must follow the instructions and use the given json format to call APIs.\n"
            "You can only generate one action at a time.\n"
            "Before every action, reason about the current state and what to do next. "
            "Reply in exactly this format, with the reasoning first and then a single action:\n"
            "##Thought: <your step-by-step reasoning for this step>\n"
            "##Command: <one action as a single-line json object>\n"
            "You must switch to an app with the switch_app action before you can use that app's actions. "
            "After switching, use only the exact action names and argument names shown in the instruction for the current app; do not invent action or argument names.\n"
            "You can find files for your task in `/testbed/data`. If you don't know the filenames, please switch to shell app and call commands to list the directory.\n"
            "You have following apps installed in the system:\n"
            f"{app_introduction}"
        ).strip()
        return system_message

    def construct_system_message_bn(self, available_apps, username, date, weekday, time):
        # Bangla system prompt. App keys and the ##Thought/##Command markers stay English
        # (they are identifiers the parser and executor depend on); descriptions are Bangla.
        app_introduction = ''
        for app in available_apps:
            app_introduction += f' - {APP_INTRO_BN.get(app, apps.AVAILABLE_APPS[app].INTRO)}\n'
        return (
            f"আজকের তারিখ {date} ({weekday})। বর্তমান সময় {time}। আপনি ব্যবহারকারী {username}-এর জন্য একজন AI সহকারী।\n"
            "আপনি ধাপে ধাপে কাজটি সমাধান করতে সাহায্য করতে পারেন।\n"
            "আপনি একটি অপারেটিং সিস্টেমের সাথে ইন্টারঅ্যাক্ট করতে পারেন এবং কাজ সমাধানে অ্যাপ ব্যবহার করতে পারেন।\n"
            "আপনাকে অবশ্যই নির্দেশনা অনুসরণ করতে হবে এবং API কল করতে প্রদত্ত json ফরম্যাট ব্যবহার করতে হবে।\n"
            "আপনি একবারে কেবল একটি অ্যাকশন তৈরি করতে পারেন।\n"
            "প্রতিটি অ্যাকশনের আগে বর্তমান অবস্থা ও পরবর্তী পদক্ষেপ নিয়ে যুক্তি দিন। ঠিক এই ফরম্যাটে উত্তর দিন — প্রথমে যুক্তি, তারপর একটি একক অ্যাকশন:\n"
            "##Thought: <এই ধাপের জন্য আপনার ধাপে ধাপে যুক্তি>\n"
            "##Command: <একটি single-line json অবজেক্ট হিসেবে একটি অ্যাকশন>\n"
            "কোনো অ্যাপের অ্যাকশন ব্যবহারের আগে আপনাকে switch_app অ্যাকশন দিয়ে সেই অ্যাপে সুইচ করতে হবে। "
            "সুইচ করার পর, বর্তমান অ্যাপের নির্দেশনায় দেখানো সঠিক action ও argument নামগুলোই ব্যবহার করুন; নিজে থেকে কোনো নাম বানাবেন না।\n"
            "আপনার কাজের ফাইলগুলো `/testbed/data`-তে পাবেন। ফাইলের নাম না জানলে shell অ্যাপে সুইচ করে ডিরেক্টরি তালিকা দেখার কমান্ড চালান।\n"
            "সিস্টেমে নিম্নলিখিত অ্যাপগুলো ইনস্টল করা আছে:\n"
            f"{app_introduction}"
        ).strip()

    def proc_action(self, action):
        # Thought-then-Action format: the real command follows the last ##Command: marker,
        # so reasoning above it (even if it mentions braces) cannot be mistaken for the action.
        if '##Command:' in action:
            action = action.rsplit('##Command:', 1)[1]
        if '{' not in action or '}' not in action:
            return action
        left = action.find('{')
        right = action.rfind('}') + 1
        action = action[left:right]
        return action

    def forward(self, env):
        prompt = self.build_prompt(env)
        if self.llm_cache:
            if prompt in self.llm_cache:
                print('!!!')
                print('LLM Cache Hit!')
                print('!!!')
                response = self.llm_cache[prompt]
            else:
                response = self.llm.generate(prompt)
        else:
            response = self.llm.generate(prompt)

        self.llm_history.append((self.system_message, prompt, response))

        if self.debug_mode:
            print('\n\n' + '>'*20)
            print(f'System: {self.system_message}')
            print(f'Prompt: {prompt}')
            print(f'Response: {response}')
            print('<'*20 + '\n\n')

        action = self.proc_action(response)
        if action == '':
            action = response

        self.action_window.append(action)
        self.action_window = self.action_window[-self.action_window_size:]
        if len(self.action_window) >= self.action_window_size and all([action == self.action_window[0] for action in self.action_window]):
            self.logger.warning(f"LLM Policy: Action stuck in the action window: {action}")
            action = repr({'app': 'system', 'action': 'got_stuck'})   

        return action
    
    def build_prompt(self, env):
        PD = PROMPT_DICT_BN if self.lang == 'bn' else PROMPT_DICT
        if env.current_app is None:
            if len(env.history) == 0:
                prompt = PD['prompt_undecided_app'].format_map({
                    'task': env.task,
                    'available_apps': list(env.available_apps.keys()),
                })
            else:
                # construct history
                history = ''
                for i, (action, observation) in enumerate(env.history):
                    if observation:
                        observation = observation.replace('\n', '\\n')
                        history += f' - Step {i}: {action} -> [{observation}]\n'
                    else:
                        history += f' - Step {i}: {action}\n'
                prompt = PD['prompt_undecided_app_w_history'].format_map({
                    'task': env.task,
                    'history': history,
                    'available_apps': list(env.available_apps.keys()),
                })
        else:
            # construct history
            history = ''
            for i, (action, observation) in enumerate(env.history):
                if observation:
                    observation = observation.replace('\n', '\\n')
                    history += f' - Step {i}: {action} -> [{observation}]\n'
                else:
                    history += f' - Step {i}: {action}\n'
            # construct detailed instruction
            detailed_instruction = ''
            for action in env.get_available_actions():
                action_module = apps.AVAILABLE_ACTIONS[env.current_app][action]
                detailed_instruction += f" - {action_module.DEMO}\n"
            avaiblable_apps = [app for app in env.available_apps.keys() if app != env.current_app]
            prompt = PD['prompt_decided_app'].format_map({
                'task': env.task,
                'history': history,
                'current_app': env.current_app,
                'detailed_instruction': detailed_instruction,
                'available_apps': avaiblable_apps,
            })

        return prompt


