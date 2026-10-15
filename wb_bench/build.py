"""Build OfficeBench tasks from the WorkBench templates that fit OfficeBench's apps.

Reads the translated templates (batch_*.csv), fills the slots with one fixed set of values
(same values for EN and BN, so each EN/BN pair differs only in language), writes one testbed
per template and an expected end state for wb_bench/evaluate.py.

    python wb_bench/build.py
"""
import csv
import glob
import json
import os
import re
import shutil
from datetime import datetime

from icalendar import Calendar, Event
from email.message import EmailMessage

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_GLOB = r'C:/Users/Lenovo/Music/batch_*.csv'
OUT = os.path.join(HERE, 'tasks')
USER = 'Alice'
# Wed 2024-05-15, 9:00 AM. "Thursday" / "tomorrow" = 2024-05-16.
CONTEXT = {'username': USER, 'date': '2024-05-15', 'weekday': 'Wednesday', 'time': '9:00 AM'}

TEMPLATES = ['T03', 'T10', 'T13', 'T15', 'T16', 'T17', 'T18', 'T19', 'T20', 'T54', 'T55']

# (summary, start, end). Summaries are unique except 'Team sync', whose two instances are both
# in the future and in chronological file order, because delete_event removes the first match.
BASE_EVENTS = [
    ('Sync with Carlos',         '2024-04-24 10:00', '2024-04-24 10:30'),
    ('Planning with Priya',      '2024-05-02 14:00', '2024-05-02 14:30'),
    ('Intro with Lee',           '2024-05-08 11:00', '2024-05-08 11:30'),
    ('Kickoff with Dana',        '2024-05-10 10:00', '2024-05-10 11:00'),
    ('Vendor call',              '2024-05-16 09:00', '2024-05-16 09:30'),
    ('Meeting with Dana',        '2024-05-16 11:00', '2024-05-16 12:00'),
    ('Lunch with Omar',          '2024-05-16 12:30', '2024-05-16 13:30'),
    ('Budget planning',          '2024-05-16 15:00', '2024-05-16 16:00'),
    ('1:1 with Lee',             '2024-05-16 16:30', '2024-05-16 17:00'),
    ('Team sync',                '2024-05-17 10:00', '2024-05-17 10:30'),
    ('Sprint retro',             '2024-05-17 15:00', '2024-05-17 16:00'),
    ('Project review with Dana', '2024-05-20 14:00', '2024-05-20 15:00'),
    ('Lunch with Lee',           '2024-05-21 12:30', '2024-05-21 13:30'),
    ('Team sync',                '2024-05-22 10:00', '2024-05-22 10:30'),
    ('Review with Priya',        '2024-05-28 11:00', '2024-05-28 11:30'),
]

BASE_EMAILS = [  # (sender, subject, body) in Alice's inbox; dates are not modelled by OfficeBench
    ('Dana', 'Roadmap draft', 'Hi Alice, the roadmap draft is attached for your comments.'),
    ('Omar', 'Lunch on Thursday', 'Still on for lunch on Thursday?'),
]

CATCHUP_BODY = "We haven't caught up in a while - can you send some availability over next week?"
CATCHUP_BODY_55 = 'We have not caught up in a while - can you send some availability over next week?'

# slot values per template: {'en': {...}, 'bn': {...}}; BN '!en' slots fall back to 'en'.
SLOTS = {
    'T03': {'en': {'name': 'Carlos', 'body': 'Can we move our call to Friday?', 'subject': 'Call reschedule'},
            'bn': {'name': 'Carlos'}},
    'T10': {'en': {'natural_language_date': 'May 16'}, 'bn': {'natural_language_date': '16 মে'}},
    'T13': {'en': {'event_name': 'Team sync'}, 'bn': {'event_name': 'Team sync'}},
    'T15': {'en': {'name': 'Dana'}, 'bn': {'name': 'Dana'}},
    'T16': {'en': {'name': 'Carlos', 'duration': '14'}, 'bn': {'name': 'Carlos', 'duration': '14'}},
    'T17': {'en': {'next_day': 'Thursday', 'before_or_after': 'after', 'natural_language_time': '14:00'},
            'bn': {'next_day': 'বৃহস্পতিবার', 'before_or_after': 'পরে', 'natural_language_time': '14:00'}},
    'T18': {'en': {'name': 'Lee'}, 'bn': {'name': 'Lee'}},
    'T19': {'en': {'event_name': 'Team sync'}, 'bn': {'event_name': 'Team sync'}},
    'T20': {'en': {'duration': '1.5 hour', 'event_name': 'Roadmap review', 'natural_language_date': 'May 22',
                   'natural_language_time': '14:00', 'name': 'Dana'},
            'bn': {'duration': '1.5 ঘণ্টা', 'event_name': 'Roadmap review', 'natural_language_date': '22 মে',
                   'natural_language_time': '14:00', 'name': 'Dana'}},
    'T54': {'en': {'name': 'Priya', 'days': '7'}, 'bn': {'name': 'Priya', 'days': '7'}},
    'T55': {'en': {'name': 'Priya', 'days': '7'}, 'bn': {'name': 'Priya', 'days': '7'}},
}


def drop(*summaries_starts):
    """Base calendar minus the given (summary, start) events."""
    gone = set(summaries_starts)
    return [e for e in BASE_EVENTS if (e[0], e[1]) not in gone]


# Expected end state. calendar: Alice's events (summary None = any summary); emails: new emails.
EXPECTED = {
    'T03': {'calendar': BASE_EVENTS, 'emails': [('Carlos', 'Call reschedule', 'Can we move our call to Friday?')]},
    'T10': {'calendar': drop(('Vendor call', '2024-05-16 09:00')), 'emails': []},
    'T13': {'calendar': drop(('Team sync', '2024-05-17 10:00')), 'emails': []},
    'T15': {'calendar': drop(('Meeting with Dana', '2024-05-16 11:00')), 'emails': []},
    # last met Carlos 2024-04-24 (> 14 days ago); first free 30 min from tomorrow in a 9:00 workday
    'T16': {'calendar': BASE_EVENTS + [('catch-up', '2024-05-16 09:30', '2024-05-16 10:00')], 'emails': []},
    'T17': {'calendar': drop(('Budget planning', '2024-05-16 15:00'), ('1:1 with Lee', '2024-05-16 16:30')),
            'emails': []},
    'T18': {'calendar': drop(('1:1 with Lee', '2024-05-16 16:30'), ('Lunch with Lee', '2024-05-21 12:30')),
            'emails': []},
    'T19': {'calendar': drop(('Team sync', '2024-05-17 10:00'), ('Team sync', '2024-05-22 10:00')), 'emails': []},
    'T20': {'calendar': BASE_EVENTS + [('Roadmap review', '2024-05-22 14:00', '2024-05-22 15:30')], 'emails': []},
    # last met Priya 2024-05-02 (> 7 days ago)
    'T54': {'calendar': BASE_EVENTS, 'emails': [('Priya', 'Catch up soon?', CATCHUP_BODY)]},
    # next Priya meeting 2024-05-28 (> 7 days ahead)
    'T55': {'calendar': BASE_EVENTS, 'emails': [('Priya', 'Catch up soon?', CATCHUP_BODY_55)]},
}
# T16.v2 names no event, so any summary is accepted for the new event.
EXPECTED_OVERRIDE = {'T16.v2': {'calendar': BASE_EVENTS + [(None, '2024-05-16 09:30', '2024-05-16 10:00')],
                                'emails': []}}


def render(template, values, fallback):
    def sub(m):
        name, mod = m.group(1), m.group(2)
        src = fallback if mod == '!en' else values
        if name not in src:
            src = fallback
        return src[name]
    out = re.sub(r'\{(\w+)(!en)?\}', sub, template)
    assert '{' not in out and '}' not in out, out
    return out.strip()


def write_testbed(path):
    os.makedirs(os.path.join(path, 'calendar'), exist_ok=True)
    os.makedirs(os.path.join(path, 'emails', USER), exist_ok=True)
    os.makedirs(os.path.join(path, 'data'), exist_ok=True)
    cal = Calendar()
    cal.add('prodid', '-//My Calendar Product//mxm.dk//')
    cal.add('version', '2.0')
    for summary, start, end in BASE_EVENTS:
        ev = Event()
        ev.add('summary', summary)
        ev.add('dtstart', datetime.strptime(start, '%Y-%m-%d %H:%M'))
        ev.add('dtend', datetime.strptime(end, '%Y-%m-%d %H:%M'))
        ev.add('dtstamp', datetime(2024, 5, 1))
        ev.add('description', 'Meeting')
        ev.add('location', 'Online')
        cal.add_component(ev)
    with open(os.path.join(path, 'calendar', f'{USER}.ics'), 'wb') as f:
        f.write(cal.to_ical())
    for sender, subject, body in BASE_EMAILS:
        msg = EmailMessage()
        msg['From'] = f'{sender}@example.com'
        msg['To'] = f'{USER}@example.com'
        msg['Subject'] = subject
        msg.set_content(body)
        with open(os.path.join(path, 'emails', USER, f'{subject}.eml'), 'w', newline='\n') as f:
            f.write(msg.as_string())


def main():
    rows = [r for f in sorted(glob.glob(CSV_GLOB)) for r in csv.DictReader(open(f, encoding='utf-8'))]
    rows = [r for r in rows if r['template_id'] in TEMPLATES]
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    manifest = []
    for r in rows:
        vid, tid = r['variant_id'], r['template_id']
        en = render(r['template_en'], SLOTS[tid]['en'], SLOTS[tid]['en'])
        bn = render(r['template_bn'], SLOTS[tid]['bn'], SLOTS[tid]['en'])
        task_dir = os.path.join(OUT, vid)
        write_testbed(os.path.join(task_dir, 'testbed'))
        os.makedirs(os.path.join(task_dir, 'subtasks'), exist_ok=True)
        for lang, text in (('en', en), ('bn', bn)):
            with open(os.path.join(task_dir, 'subtasks', f'{lang}.json'), 'w', encoding='utf-8') as f:
                json.dump(CONTEXT | {'task': text}, f, ensure_ascii=False, indent=2)
        exp = EXPECTED_OVERRIDE.get(vid, EXPECTED[tid])
        with open(os.path.join(task_dir, 'expected.json'), 'w', encoding='utf-8') as f:
            json.dump(exp, f, ensure_ascii=False, indent=2)
        manifest.append({'variant_id': vid, 'en': en, 'bn': bn})
    with open(os.path.join(HERE, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f'built {len(manifest)} variants x 2 languages in {OUT}')


if __name__ == '__main__':
    main()
