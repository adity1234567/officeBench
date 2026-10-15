"""Evidence helper: how is write_to_file described to the agent in EN vs BN?"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for tag in ('gemma4_31b_think', 'gemma4_31b_bn'):
    p = os.path.join(ROOT, 'tasks', '1-15', 'outputs', '0', tag, 'llm_history.json')
    blob = json.dumps(json.load(open(p, encoding='utf-8')), ensure_ascii=False)
    print('==', tag, len(blob), 'chars')
    for m in list(re.finditer(r'write_to_file', blob))[:1]:
        print('  ctx:', blob[max(0, m.start() - 160): m.start() + 420].replace('\\n', ' '))
    for kw in ('append', 'end of', 'শেষে', 'যোগ'):
        print('  count %-6r %d' % (kw, blob.count(kw)))
