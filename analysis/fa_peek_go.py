"""Evidence helper: what the gpt-oss English and Bangla runs actually wrote, for selected cases."""
import json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WANT = sys.argv[1:] or ['1-6/4', '1-19/4', '2-2/0', '2-26/0', '2-27/0', '2-43/1', '3-21/0', '2-40/1', '1-18/1', '2-39/1', '2-37/1']


def hist(tag, t, s):
    return json.load(open(os.path.join(ROOT, 'tasks', t, 'outputs', s, tag, 'env_history.json'), encoding='utf-8'))


def writes(h):
    out = []
    for a, o in h:
        if not isinstance(a, dict):
            continue
        act = a.get('action')
        if act == 'set_cell':
            out.append('cell(%s,%s)=%s' % (a.get('row_idx'), a.get('column_idx'), str(a.get('text'))[:30]))
        elif act == 'create_event':
            out.append('event[%s] %s %s' % (a.get('user'), str(a.get('summary'))[:30], str(a.get('time_start'))[11:16]))
        elif act == 'send_email':
            out.append('mail->%s subj=%s body=%s' % (a.get('recipient'), str(a.get('subject'))[:25], re.sub(r'\s+', ' ', str(a.get('content')))[:90]))
        elif act in ('write_to_file',):
            out.append('write %s :: %s' % (os.path.basename(str(a.get('file_path'))), re.sub(r'\s+', ' ', str(a.get('contents')))[:110]))
        elif act == 'convert_to_word' or act == 'convert_to_pdf' or act == 'convert_to_image':
            out.append('%s %s' % (act, os.path.basename(str(a.get('pdf_file_path') or a.get('word_file_path')))))
        elif act == 'command':
            out.append('sh: %s' % re.sub(r'\s+', ' ', str(a.get('command')))[:100])
    return out


for cid in WANT:
    t, s = cid.split('/')
    print('==', cid)
    for tag, lab in (('gpt-oss_20b_en', 'EN'), ('gpt-oss_20b_bn', 'BN')):
        w = writes(hist(tag, t, s))
        print('  %s (%d writes):' % (lab, len(w)))
        for x in w[:9]:
            print('     ', x)
        if len(w) > 9:
            print('      ... +%d' % (len(w) - 9))
