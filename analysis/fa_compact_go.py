"""Very compact English-vs-Bangla view of the gpt-oss EN-pass/BN-fail cases (evidence helper for labelling)."""
import json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(ROOT, 'analysis', 'fa_rows_gptoss.json'), encoding='utf-8'))


def tok(a, o):
    if isinstance(a, dict):
        act = a.get('action')
        extra = ''
        for k in ('target_app', 'username', 'user', 'file_path', 'pdf_file_path', 'recipient', 'summary', 'answer', 'command'):
            if k in a:
                v = a[k]
                extra = str(v)[:42]
                break
        r = '%s.%s(%s)' % (a.get('app'), act, extra)
        if 'Malformed' in str(o):
            r += '!MAL'
        if str(o).startswith('ERROR') or 'Failed' in str(o)[:60] or 'does not exist' in str(o):
            r += '!ERR'
        return r
    if 'Malformed' in str(o):
        return '[invalid:%s]' % re.sub(r'\s+', ' ', str(a))[:26]
    return '[text]'


def hist(tag, t, s):
    return json.load(open(os.path.join(ROOT, 'tasks', t, 'outputs', s, tag, 'env_history.json'), encoding='utf-8'))


for r in rows:
    if not (r['en'] and not r['bn']):
        continue
    t, s = r['id'].split('/')
    cfg = json.load(open(os.path.join(ROOT, 'tasks', t, 'subtasks', s + '.json'), encoding='utf-8'))
    en, bn = hist('gpt-oss_20b_en', t, s), hist('gpt-oss_20b_bn', t, s)
    print('=' * 90)
    print(r['id'], 'apps', r['apps'], '|', cfg['task'][:170])
    print('  checks:', '; '.join('%s %s' % (e['function'].replace('evaluate_', ''), json.dumps(e['args'], ensure_ascii=False)[:90]) for e in cfg['evaluation']))
    print('  EN(%d): %s' % (len(en), ' > '.join(tok(a, o) for a, o in en)[:520]))
    print('  BN(%d): %s' % (len(bn), ' > '.join(tok(a, o) for a, o in bn)[:620]))
    print('  BN last obs:', re.sub(r'\s+', ' ', str(bn[-1][1]))[:120] if bn else None)
