"""Generate the teaser figure: one subtask (1-2/0) carried through the whole pipeline.

Every string and time below is taken from the run itself:
  tasks/1-2/subtasks/0.json                     the task and its four checks
  tasks/1-2/testbed/calendar/{Bob,Tom}.ics      the busy blocks drawn in the strip
  tasks/1-2/outputs/0/gemma4_31b_think/         the English run (4 steps)
  tasks/1-2/outputs/0/gemma4_31b_bn/            the Bangla run (same answer, Bangla script)
  analysis/failure_codes_all_runs.json          the code: BM in all four cells

    python analysis/figures/make_fig0_teaser.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fig0_teaser.svg')

ACC = '#d97706'      # the path the paper argues about
OK = '#1a7f4b'
BAD = '#b3391f'
W, H = 1160, 848

# ---------------------------------------------------------------- the real data
TASK_EN = ['Find a common time for Bob and Tom to have',
           'an one hour zoom meeting on 5/1/2024']
TASK_BN = ['ফাইন্ড করুন: ৫/১/২০২৪ তারিখে বব এবং টমের জন্য',
           'এক ঘণ্টার একটি জুম মিটিং করার জন্য',
           'একটি সাধারণ সময় খুঁজে বের করুন।']

ANS_EN = '“A common time for Bob and Tom to have a one-hour zoom meeting on 5/1/2024 is from 14:30 to 15:30.”'
ANS_BN = '“বব এবং টমের জন্য ৫/১/২০২৪ তারিখে একটি সাধারণ সময় হলো দুপুর ১৪:৩০ থেকে ১৫:৩০ পর্যন্ত।”'

STEPS = [
    ('switch_app', 'to calendar', '{"app":"system","action":"switch_app","target_app":"calendar"}'),
    ('list_events', 'username: Bob', '{"app":"calendar","action":"list_events","username":"Bob"} → 5 events returned'),
    ('list_events', 'username: Tom', '{"app":"calendar","action":"list_events","username":"Tom"} → 5 events returned'),
    ('finish_task', 'answer: 14:30–15:30', 'The agent never writes a file. It answers, which is what the task asked for.'),
]

BUSY = {
    'Bob': [(8, 11, 'sleeping'), (12, 13, 'lunch'), (13, 14, 'nap'), (16, 18, 'class'), (18.5, 19.5, 'dinner')],
    'Tom': [(8, 11.833, 'class'), (12.5, 13.5, 'lunch with David'), (14, 14.5, 'report to Charlie'),
            (16, 18, 'class'), (18.5, 19.5, 'dinner')],
}

CHECKS = [
    (False, 'evaluate_contain', './calendar/Bob.ics  keywords: ["meeting"]',
     'Requires a calendar event named "meeting" in Bob.ics. The task never asks for one to be created.'),
    (False, 'evaluate_contain', './calendar/Tom.ics  keywords: ["meeting"]',
     'Same requirement on Tom.ics. These two checks alone decide the run.'),
    (True, 'evaluate_calendar_no_overlap', 'username: Bob',
     'Passes: the agent changed nothing, so nothing overlaps.'),
    (True, 'evaluate_calendar_no_overlap', 'username: Tom',
     'Passes: the agent changed nothing, so nothing overlaps.'),
]

SCALE = [('47', 'of gemma4:31b’s 149 English', 'failures are benchmark defects'),
         ('4 / 4', 'cells fail this subtask,', 'all coded BM'),
         ('44', 'subtasks fail for the', 'identical cause everywhere'),
         ('57', 'subtasks where a defect', 'decides at least one run')]

# ---------------------------------------------------------------- helpers
o = []
add = o.append
esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def text(x, y, s, size=11, weight=None, anchor=None, fill='currentColor', op=None, mono=False, extra=''):
    a = 'x="%g" y="%g" font-size="%g" fill="%s"' % (x, y, size, fill)
    if weight: a += ' font-weight="%s"' % weight
    if anchor: a += ' text-anchor="%s"' % anchor
    if op: a += ' fill-opacity="%s"' % op
    if mono: a += ' font-family="ui-monospace, Consolas, monospace"'
    add('  <text %s%s>%s</text>' % (a, extra, esc(s)))


def box(x, y, w, h, stroke='currentColor', op='.4', rx=6, fill='none', fop=None, dash=None, sw=1, extra=''):
    a = 'x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-opacity="%s" stroke-width="%g"' % (
        x, y, w, h, rx, fill, stroke, op, sw)
    if fop: a += ' fill-opacity="%s"' % fop
    if dash: a += ' stroke-dasharray="%s"' % dash
    add('  <rect %s%s/>' % (a, extra))


def arrow(x1, y1, x2, y2, color='currentColor', op='.75', mk='t0arrow', sw=1.5):
    add('  <line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-opacity="%s" stroke-width="%g" marker-end="url(#%s)"/>'
        % (x1, y1, x2, y2, color, op, sw, mk))


def chip(x, y, label, color=ACC):
    w = 9 + len(label) * 6.4
    add('  <rect x="%g" y="%g" width="%g" height="20" rx="10" fill="%s" fill-opacity=".14" stroke="%s" stroke-opacity=".5"/>'
        % (x, y, w, color, color))
    text(x + w / 2, y + 14, label, 11, '700', 'middle', color)
    return w


# ---------------------------------------------------------------- document
add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" color="#1b2330"' % (W, H))
add('     font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Noto Sans Bengali, Helvetica, Arial, sans-serif"')
add('     aria-label="One OfficeBench subtask carried through the study: the agent reads both calendars and answers '
    'that 14:30 to 15:30 is free, which is correct; two of the four checks nonetheless require a calendar event named '
    'meeting that the task never asks anyone to create, so the run is scored FAIL and coded as a benchmark defect in '
    'all four cells.">')
add('  <defs>')
for i, c in [('t0arrow', 'currentColor'), ('t0acc', ACC)]:
    add('    <marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M0 0 L10 5 L0 10 z" fill="%s"/></marker>' % (i, c))
add('  </defs>')

# ---- title
text(24, 30, 'One subtask, four cells, four failures — and the answer was right', 17, '700')
text(24, 50, 'subtask 1-2/0, single-app calendar task, run under both models in both languages', 11.5, None, None, op='.7')

# ================================================================ band A: the run
box(16, 64, 1128, 348, stroke='currentColor', op='.18', rx=10, fill='currentColor', fop='.035')
text(1128, 88, 'What the benchmark does', 14, '700', 'end', op='.45')

# -- stage 1: the task
cw = 250
add('  <g id="t0-stage1" class="t0-stage" data-stage="1">')
chip(36, 78, '1 · The task')
box(36, 106, cw, 128, extra=' id="t0-taskbox"')
add('  <text id="t0-task" x="50" y="130" font-size="11.5" fill="currentColor">'
    '<tspan x="50" dy="0">%s</tspan><tspan x="50" dy="17">%s</tspan><tspan x="50" dy="17"></tspan></text>'
    % (esc(TASK_EN[0]), esc(TASK_EN[1])))
text(50, 196, 'It says find. It does not say', 10.5, None, None, op='.7')
text(50, 210, 'add anything to a calendar.', 10.5, None, None, op='.7')
# language toggle
add('  <g id="t0-lang" class="t0-toggle">')
add('    <rect id="t0-en" class="t0-chip t0-on" x="36" y="244" width="46" height="22" rx="11" '
    'fill="%s" fill-opacity=".16" stroke="%s" stroke-opacity=".6" data-lang="en"/>' % (ACC, ACC))
text(59, 259, 'EN', 11, '700', 'middle', ACC, extra=' pointer-events="none"')
add('    <rect id="t0-bn" class="t0-chip" x="90" y="244" width="64" height="22" rx="11" '
    'fill="none" stroke="currentColor" stroke-opacity=".35" data-lang="bn"/>')
text(122, 260, 'বাংলা', 11, '700', 'middle', 'currentColor', extra=' pointer-events="none"')
add('  </g>')
text(36, 288, 'the same subtask runs in all four cells', 10, None, None, op='.6')
add('  </g>')

arrow(294, 170, 326, 170)

# -- stage 2: the run
add('  <g id="t0-stage2" class="t0-stage" data-stage="2">')
chip(336, 78, '2 · The run — 4 steps of the 20 allowed')
sx = [336, 530, 724, 918]
for i, (a, b, detail) in enumerate(STEPS):
    last = i == 3
    box(sx[i], 106, 170, 54, stroke=ACC if last else 'currentColor', op='.9' if last else '.4',
        sw=1.4 if last else 1,
        extra=' class="t0-hot" data-detail="%s"' % esc(detail))
    text(sx[i] + 85, 128, a, 12, '700', 'middle', extra=' pointer-events="none"')
    text(sx[i] + 85, 146, b, 10.5, None, 'middle', op='.78', extra=' pointer-events="none"')
    if i < 3:
        arrow(sx[i] + 172, 133, sx[i] + 190, 133)

# -- calendar strip
x0, PPH = 380, 56
X = lambda t: x0 + (t - 8) * PPH
box(X(14.5), 196, PPH, 96, stroke=ACC, op='.9', rx=4, fill=ACC, fop='.14', sw=1.4)
text(X(15), 190, 'free for both — 14:30–15:30', 10.5, '700', 'middle', ACC)
for row, (who, blocks) in enumerate(BUSY.items()):
    y = 204 + row * 44
    text(372, y + 22, who, 11.5, '700', 'end')
    add('  <line x1="%g" y1="%g" x2="%g" y2="%g" stroke="currentColor" stroke-opacity=".18"/>' % (x0, y + 16, X(20), y + 16))
    for s, e, name in blocks:
        box(X(s), y, (e - s) * PPH, 32, stroke='currentColor', op='.45', rx=3, fill='currentColor', fop='.14',
            extra=' class="t0-hot" data-detail="%s busy %02d:%02d–%02d:%02d — %s"'
                  % (who, int(s), round(s % 1 * 60), int(e), round(e % 1 * 60), esc(name)))
        if (e - s) * PPH > 60:
            text(X(s) + (e - s) * PPH / 2, y + 21, name, 10, None, 'middle', op='.8', extra=' pointer-events="none"')
add('  <line x1="%g" y1="296" x2="%g" y2="296" stroke="currentColor" stroke-opacity=".3"/>' % (x0, X(20)))
for t in range(8, 21, 2):
    add('  <line x1="%g" y1="296" x2="%g" y2="300" stroke="currentColor" stroke-opacity=".3"/>' % (X(t), X(t)))
    text(X(t), 312, '%02d:00' % t, 9.5, None, 'middle', op='.6')

# -- the answer
box(336, 326, 752, 70, stroke=OK, op='.65', fill=OK, fop='.06')
text(352, 348, 'The agent answers — and the answer is right', 12, '700', fill=OK)
add('  <text id="t0-answer" x="352" y="368" font-size="11" fill="currentColor" fill-opacity=".9">%s</text>' % esc(ANS_EN))
add('  <text id="t0-answernote" x="352" y="386" font-size="10.5" fill="currentColor" fill-opacity=".65">%s</text>'
    % esc('Bob is free 14:00–16:00, Tom from 14:30 — 14:30–15:30 is the only common hour.'))
add('  </g>')

# ================================================================ band B: our analysis
box(16, 428, 1128, 404, stroke=ACC, op='.25', rx=10, fill=ACC, fop='.05')
text(1128, 452, 'What we do', 14, '700', 'end', ACC, op='.75')

# -- stage 3: scoring
add('  <g id="t0-stage3" class="t0-stage" data-stage="3">')
chip(36, 442, '3 · Scoring — the benchmark’s own four checks')
for i, (ok, fn, args, detail) in enumerate(CHECKS):
    y = 476 + i * 38
    box(36, y, 520, 32, stroke=OK if ok else BAD, op='.55', rx=4, fill=OK if ok else BAD, fop='.07',
        extra=' class="t0-hot" data-detail="%s"' % esc(detail))
    text(54, y + 21, '✓' if ok else '✗', 14, '700', 'middle', OK if ok else BAD, extra=' pointer-events="none"')
    text(70, y + 21, fn, 11, '700', None, mono=True, extra=' pointer-events="none"')
    text(306, y + 21, args, 10.5, None, None, op='.78', mono=True, extra=' pointer-events="none"')
box(36, 636, 520, 62, stroke=ACC, op='.7', dash='5 4')
text(52, 658, 'Two of the four checks require a calendar event named “meeting”.', 11.5, '700', fill=ACC)
text(52, 678, 'The task asked the agent to find a time, not to create one. Nothing it could', 10.5, None, None, op='.8')
text(52, 692, 'have written would satisfy the task and the check at the same time.', 10.5, None, None, op='.8')
box(36, 714, 150, 40, stroke=BAD, op='.8', fill=BAD, fop='.1', sw=1.4)
text(111, 740, 'scored FAIL', 14, '700', 'middle', BAD)
text(200, 731, 'official score and corrected', 10.5, None, None, op='.7')
text(200, 745, 'score agree here — 2 of 4 checks false', 10.5, None, None, op='.7')
add('  </g>')

arrow(570, 560, 602, 560, ACC, '.9', 't0acc')

# -- stage 4: the code
add('  <g id="t0-stage4" class="t0-stage" data-stage="4">')
chip(606, 442, '4 · The code')
box(606, 476, 300, 76, stroke=ACC, op='.8', sw=1.4)
text(756, 500, 'Is the output correct for', 12, '700', 'middle')
text(756, 518, 'the task as written?', 12, '700', 'middle')
text(756, 540, 'meaning, not surface form', 10, None, 'middle', op='.65')
arrow(756, 554, 756, 580, ACC, '.9', 't0acc')
box(606, 584, 300, 54, stroke='currentColor', op='.45')
text(756, 606, 'Yes — and it still scored FAIL', 12, '700', 'middle', OK)
text(756, 626, 'so the run indicts the benchmark, not the agent', 10, None, 'middle', op='.75')
arrow(756, 640, 756, 666, ACC, '.9', 't0acc')
box(606, 670, 300, 84, stroke=ACC, op='.9', fill=ACC, fop='.12', sw=1.6)
text(648, 706, 'BM', 26, '700', 'middle', ACC)
text(686, 694, 'benchmark defect', 12, '700')
text(686, 712, 'the check asks for what', 10.5, None, None, op='.8')
text(686, 726, 'the task does not', 10.5, None, None, op='.8')
text(686, 744, '+ tag C-AMBIG', 10.5, '700', None, op='.9')
add('  </g>')

# -- stage 5: scale
add('  <g id="t0-stage5" class="t0-stage" data-stage="5">')
chip(930, 442, 'Not a one-off')
for i, (n, l1, l2) in enumerate(SCALE):
    y = 480 + i * 70
    text(930, y + 26, n, 24, '700', None, ACC)
    text(930, y + 44, l1, 10, None, None, op='.8')
    text(930, y + 57, l2, 10, None, None, op='.8')
add('  </g>')

add('</svg>')

open(OUT, 'w', encoding='utf-8').write('\n'.join(o) + '\n')
print('wrote', OUT)
