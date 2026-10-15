"""Evidence helper: Bangla task line and key BN writes for the translation/ambiguity cases."""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for cid in ['2-38/2', '3-17/0', '3-55/0', '3-56/0', '3-68/0', '2-40/2', '2-17/0', '1-11/0', '2-20/0', '3-64/0', '3-15/0', '2-1/0']:
    t, s = cid.split('/')
    d = os.path.join(ROOT, 'tasks', t, 'outputs', s, 'gemma4_31b_bn')
    cfg = json.load(open(os.path.join(ROOT, 'tasks', t, 'subtasks', s + '.json'), encoding='utf-8'))
    h = json.load(open(os.path.join(d, 'llm_history.json'), encoding='utf-8'))
    blob = json.dumps(h, ensure_ascii=False)
    m = re.search(r'(?:টাস্ক|Task)\s*[:：]\s*([^"\\]{10,400})', blob)
    print('==', cid, '| EN task:', cfg['task'])
    print('   BN task:', m.group(1).strip() if m else '(not found)')
    env = json.load(open(os.path.join(d, 'env_history.json'), encoding='utf-8'))
    if cid in ('3-68/0',):
        for a, o in env:
            if isinstance(a, dict) and a.get('action') in ('set_cell', 'send_email'):
                print('   ', json.dumps(a, ensure_ascii=False)[:230])
    if cid == '2-40/2':
        print('   BN email:', [a for a, o in env if isinstance(a, dict) and a.get('action') == 'send_email'][0].get('content'))
    if cid == '3-15/0':
        for a, o in env[-5:]:
            print('   ', json.dumps(a, ensure_ascii=False)[:260])
