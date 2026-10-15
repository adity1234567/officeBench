"""Corrected re-scoring of an OfficeBench run, with the three repairs described in the failure report:

  1. email checks read the run's own testbed (email_list_emails hard-codes /testbed/emails, which only exists in the container),
  2. mailbox matching tries the exact name first, then lower case, then a case-insensitive substring match among folders
     that actually hold mail (the repo's fallback loop raises NameError, and list_emails creates empty look-alike folders),
  3. text files are read as UTF-8.

All other checks are the repository's own functions, unchanged.

    python analysis/fa_rescore.py --validate        # reproduce the corrected scores already used in the report
    python analysis/fa_rescore.py gpt-oss_20b_bn    # score one run tag -> analysis/rescored_<tag>.json
"""
import contextlib, glob, io, json, os, sys
from email import policy
from email.parser import BytesParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from utils import evaluate as ev  # noqa: E402

TAGS = {'EN': 'gemma4_31b_think', 'BN': 'gemma4_31b_bn', 'GO': 'gpt-oss_20b_en', 'GB': 'gpt-oss_20b_bn'}


def _body(msg):
    if msg.is_multipart():
        parts = []
        for part in msg.iter_parts():
            if part.get_content_type() in ('text/plain', 'text/html'):
                parts.append(part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace'))
        return '\n'.join(parts)
    return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')


def _mailbox_text(testbed, account):
    out = ''
    for f in sorted(glob.glob(os.path.join(testbed, 'emails', account, '*.eml'))):
        m = BytesParser(policy=policy.default).parsebytes(open(f, 'rb').read())
        out += 'Email ID: %s\nFrom: %s\nTo: %s\nSubject: %s\nContent: %s\n%s\n' % (
            os.path.basename(f), m['From'], m['To'], m['Subject'], _body(m), '-' * 50)
    return out or 'No emails found.'


def _find_mailbox(testbed, username):
    root = os.path.join(testbed, 'emails')
    names = [n for n in os.listdir(root)] if os.path.isdir(root) else []
    if username in names:
        return username
    if username.lower() in names:
        return username.lower()
    for n in names:
        if username.lower() in n.lower() and glob.glob(os.path.join(root, n, '*.eml')):
            return n
    return username


def evaluate_contain(testbed_dir, args):
    t = args['doc_type']
    if t == 'email':
        return ev._evaluate_contain_text(_mailbox_text(testbed_dir, _find_mailbox(testbed_dir, args['username'])), args)
    if t in ('txt', 'ics'):
        p = os.path.join(testbed_dir, args['file'])
        if not os.path.isfile(p):
            return False
        return ev._evaluate_contain_text(open(p, encoding='utf-8', errors='replace').read(), args)
    return orig_contain(testbed_dir, args)


orig_contain = ev.evaluate_contain
ev.evaluate_contain = evaluate_contain
ev.evaluate_not_contain = lambda d, a: not evaluate_contain(d, a)


def score_one(tid, sid, tag):
    d = os.path.join('tasks', tid, 'outputs', sid, tag, 'testbed')
    if not os.path.isdir(d):
        return None
    cfg = json.load(open(os.path.join('tasks', tid, 'subtasks', sid + '.json'), encoding='utf-8'))
    for e in cfg['evaluation']:
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ok = getattr(ev, e['function'])(d, e['args'])
        except Exception:
            ok = False
        if not ok:
            return False
    return True


def all_ids():
    ids = []
    for p in glob.glob('tasks/*/subtasks/*.json'):
        parts = p.replace(os.sep, '/').split('/')
        ids.append((parts[1], parts[3][:-5]))
    return sorted(ids, key=lambda x: (int(x[0].split('-')[0]), int(x[0].split('-')[1]), int(x[1])))


def score_tag(tag, only=None):
    res = {}
    for tid, sid in all_ids():
        key = '%s/%s' % (tid, sid)
        if only is not None and key not in only:
            continue
        r = score_one(tid, sid, tag)
        res[key] = r
    return res


if __name__ == '__main__':
    if '--validate' in sys.argv:
        ref = json.load(open(os.path.join(HERE, 'failure_codes_all_runs.json'), encoding='utf-8'))['pass']
        for k, tag in TAGS.items():
            got = score_tag(tag, set(ref[k]))
            miss = [i for i in ref[k] if bool(got.get(i)) != bool(ref[k][i])]
            none = [i for i in ref[k] if got.get(i) is None]
            print('%s %-18s n=%3d  reference pass=%3d  rescored pass=%3d  mismatches=%d %s  missing-output=%d'
                  % (k, tag, len(ref[k]), sum(map(bool, ref[k].values())), sum(bool(got.get(i)) for i in ref[k]), len(miss), miss[:8], len(none)))
    else:
        tag = sys.argv[1]
        res = score_tag(tag)
        json.dump(res, open(os.path.join(HERE, 'rescored_%s.json' % tag), 'w', encoding='utf-8'), indent=0)
        n = len(res)
        print(tag, 'scored', n, 'pass', sum(bool(v) for v in res.values()), 'missing output', sum(v is None for v in res.values()))
