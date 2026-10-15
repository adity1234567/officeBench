"""Grade a run by comparing the dumped end state with tasks/<variant>/expected.json.

Pass = Alice's calendar equals the expected multiset of (summary, start, end) exactly, and the
set of newly sent emails equals the expected one (recipient, subject, body phrase). Anything
extra (a wrong deletion, a stray email) fails, as in WorkBench's state-based grading.
"""
import json
import re

QUOTES = '\'"“”‘’`'


def norm(s):
    s = (s or '').strip().lower()
    for q in QUOTES:
        s = s.replace(q, '')
    return re.sub(r'\s+', ' ', s).strip()


def grade(state, expected, initial_email_ids):
    reasons = []
    got = sorted((norm(e['summary']), e['start'][:16], e['end'][:16]) for e in state['calendar'])
    want = [(None if s is None else norm(s), a, b) for s, a, b in expected['calendar']]
    remaining = list(got)
    for w in sorted(want, key=lambda x: x[0] is None):  # exact summaries first, wildcards last
        hit = next((g for g in remaining if (w[0] is None or g[0] == w[0]) and g[1:] == w[1:]), None)
        if hit is None:
            reasons.append(f'missing event {w}')
        else:
            remaining.remove(hit)
    for g in remaining:
        reasons.append(f'unexpected event {g}')

    # send_email also files a sent copy in the sender's own folder; only delivered copies count
    new = [m for m in state['emails'] if m['id'] not in initial_email_ids
           and norm(m['folder']) != norm(m['from'].split('@')[0])]
    left = list(new)
    for rcpt, subject, phrase in expected['emails']:
        hit = next((m for m in left if norm(m['folder']) == norm(rcpt) and norm(m['subject']) == norm(subject)
                    and norm(phrase) in norm(m['body'])), None)
        if hit is None:
            reasons.append(f'missing email to {rcpt} subject {subject!r}')
        else:
            left.remove(hit)
    for m in left:
        reasons.append(f"unexpected email to {m['folder']} subject {m['subject']!r}")
    return not reasons, reasons
