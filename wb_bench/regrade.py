"""Regrade finished runs from their saved final_state.json with the current evaluate.py.

    python wb_bench/regrade.py --model_name gemma4:31b --tag wb1
"""
import glob
import json
import os
import sys

import fire

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from evaluate import grade  # noqa: E402


def main(model_name='gemma4:31b', tag='wb1'):
    name = model_name.replace('/', '_').replace(':', '_') + f'_{tag}'
    rows = []
    for path in sorted(glob.glob(os.path.join(HERE, 'tasks', '*', 'outputs', '*', name, 'result.json'))):
        out_dir = os.path.dirname(path)
        task_dir = os.path.dirname(os.path.dirname(os.path.dirname(out_dir)))
        result = json.load(open(path, encoding='utf-8'))
        final = json.load(open(os.path.join(out_dir, 'final_state.json'), encoding='utf-8'))
        expected = json.load(open(os.path.join(task_dir, 'expected.json'), encoding='utf-8'))
        initial_ids = {'/testbed/emails/' + os.path.relpath(p, os.path.join(task_dir, 'testbed', 'emails')).replace(os.sep, '/')
                       for p in glob.glob(os.path.join(task_dir, 'testbed', 'emails', '*', '*.eml'))}
        result['pass'], result['reasons'] = grade(final, expected, initial_ids)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        rows.append(result)
    with open(os.path.join(HERE, f'results_{name}.jsonl'), 'w', encoding='utf-8') as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    for lang in ('en', 'bn'):
        rs = [r for r in rows if r['lang'] == lang]
        print(f'{lang}: {sum(r["pass"] for r in rs)}/{len(rs)} passed')
    for r in rows:
        print(r['variant'], r['lang'], 'PASS' if r['pass'] else 'FAIL', '; '.join(r['reasons']))


if __name__ == '__main__':
    fire.Fire(main)
