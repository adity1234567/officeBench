"""Evidence helper: does an English write_to_file append or overwrite? Compare initial and final docx length."""
import os, sys, docx
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for tid, sid, fn in [('1-15', '0', 'House_creak.docx'), ('1-15', '1', 'sample_syllabus.docx')]:
    init = os.path.join(ROOT, 'tasks', tid, 'testbed', 'data', fn)
    fin = os.path.join(ROOT, 'tasks', tid, 'outputs', sid, 'gemma4_31b_think', 'testbed', 'data', fn)
    for tag, p in (('initial', init), ('EN final', fin)):
        if not os.path.exists(p):
            print(tid + '/' + sid, tag, 'MISSING', p)
            continue
        text = '\n'.join(par.text for par in docx.Document(p).paragraphs)
        print('%s/%s %-9s %5d chars | head: %r | tail: %r' % (tid, sid, tag, len(text), text[:50], text[-60:]))
