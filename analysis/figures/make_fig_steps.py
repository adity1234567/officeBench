"""General step diagram: what happens at each step of the study and how. No example, no counts.

    python analysis/figures/make_fig_steps.py
"""
import os
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fig_steps.svg')
ACC = '#d97706'
W, H = 1160, 470
esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
o = []
add = o.append


def text(x, y, s, size=11, weight=None, anchor=None, fill='currentColor', op=None, mono=False):
    a = 'x="%g" y="%g" font-size="%g" fill="%s"' % (x, y, size, fill)
    if weight: a += ' font-weight="%s"' % weight
    if anchor: a += ' text-anchor="%s"' % anchor
    if op: a += ' fill-opacity="%s"' % op
    if mono: a += ' font-family="ui-monospace, Consolas, monospace"'
    add('    <text %s pointer-events="none">%s</text>' % (a, esc(s)))


def shape(tag, attrs, op='.55', fill='none', fop=None, sw=1.2):
    a = ' '.join('%s="%s"' % kv for kv in attrs.items())
    f = ' fill-opacity="%s"' % fop if fop else ''
    add('    <%s %s fill="%s"%s stroke="currentColor" stroke-opacity="%s" stroke-width="%s"/>' % (tag, a, fill, f, op, sw))


STEPS = [
    ('Collect tasks', 'Office tasks that need one or more apps',
     ['A fixed benchmark of subtasks', 'in calendar, Excel, Word, PDF,', 'email, OCR and shell.'],
     'tasks + start files', 'The agent is always given the same tasks, so runs can be compared.'),
    ('Run agents', 'A model works the task inside a container',
     ['Loop: read prompt, write a', 'thought and one JSON action,', 'app executes it. Up to 20 steps.'],
     'trace + final files', 'Models and prompt languages are the only thing that changes between runs.'),
    ('Score runs', 'Decide pass or fail for every run',
     ['Run the benchmark’s own checks', 'on the final files, after fixing', 'defects in the scoring code.'],
     'pass / fail per run', 'Scoring is repaired first so a failure means the same thing in every run.'),
    ('Characterize failures', 'Find why each failed run failed',
     ['Read the trace against the task,', 'ask if the output was right, then', 'assign one primary root cause.'],
     'one code per failure', 'Two annotators coded a sample independently to check the codes are reliable.'),
    ('Compare and report', 'See what repeats across runs',
     ['Line up codes by subtask, model', 'and language to separate shared', 'causes from model-specific ones.'],
     'findings + fixes', 'The comparison says whether to fix the benchmark or the agent first.'),
]

CW, GAP, X0, Y0, CH = 200, 34, 12, 70, 340

add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" color="#1b2330"' % (W, H))
add('     font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"')
add('     aria-label="The pipeline in five steps. Collect tasks, run agents, score runs, characterize failures, compare and report. '
    'Each step takes the previous step\'s output: tasks and start files, then a trace and final files, then pass or fail per run, '
    'then one root-cause code per failure, then findings and fixes.">')
add('  <defs><marker id="sparrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    '<path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>')
text(12, 32, 'How the study works, step by step', 17, '700')
text(12, 52, 'each step hands its output to the next', 11.5, None, None, op='.65')

for i, (title, what, how, out, why) in enumerate(STEPS):
    x = X0 + i * (CW + GAP)
    add('  <g id="s-%d" class="s-step" data-step="%d" transform="translate(%d,%d)">' % (i + 1, i + 1, x, Y0))
    add('    <rect class="s-card" x="0" y="0" width="%d" height="%d" rx="8" fill="currentColor" fill-opacity=".035" '
        'stroke="currentColor" stroke-opacity=".3"/>' % (CW, CH))
    add('    <rect x="0" y="0" width="%d" height="34" rx="8" fill="%s" fill-opacity=".16"/>' % (CW, ACC))
    add('    <rect x="0" y="22" width="%d" height="12" fill="%s" fill-opacity=".16"/>' % (CW, ACC))
    add('    <circle cx="20" cy="17" r="11" fill="%s"/>' % ACC)
    add('    <text x="20" y="21.5" font-size="13" font-weight="700" text-anchor="middle" fill="#ffffff" pointer-events="none">%d</text>' % (i + 1))
    text(38, 22, title, 13, '700')

    # pictogram, drawn in a 160x74 area starting at (20,48)
    g = lambda dx, dy: (20 + dx, 48 + dy)
    if i == 0:
        for k in range(3):
            shape('rect', {'x': 30 + k * 40, 'y': 56 + (k % 2) * 6, 'width': 32, 'height': 44, 'rx': 3})
            for l in range(3):
                shape('line', {'x1': 36 + k * 40, 'y1': 68 + (k % 2) * 6 + l * 9, 'x2': 56 + k * 40, 'y2': 68 + (k % 2) * 6 + l * 9}, op='.35', sw=1)
    if i == 1:
        for k, lab in enumerate(['prompt', 'action', 'result']):
            shape('rect', {'x': 24 + k * 56, 'y': 62, 'width': 48, 'height': 26, 'rx': 4})
            text(48 + k * 56, 79, lab, 9.5, None, 'middle', op='.8')
            if k < 2:
                add('    <line x1="%d" y1="75" x2="%d" y2="75" stroke="currentColor" stroke-opacity=".7" stroke-width="1.3" marker-end="url(#sparrow)"/>' % (73 + k * 56, 79 + k * 56))
        add('    <path d="M140 90 V 104 H 48 V 92" fill="none" stroke="currentColor" stroke-opacity=".5" stroke-width="1.2" marker-end="url(#sparrow)"/>')
        text(94, 118, 'repeat', 9.5, None, 'middle', op='.6')
    if i == 2:
        for k in range(4):
            ok = k != 2
            shape('rect', {'x': 24 + k * 42, 'y': 60, 'width': 34, 'height': 34, 'rx': 4}, op='.5')
            text(41 + k * 42, 84, '✓' if ok else '✗', 17, '700', 'middle', ACC if not ok else 'currentColor', op='.9' if not ok else '.75')
        text(96, 114, 'one check per file', 9.5, None, 'middle', op='.6')
    if i == 3:
        shape('rect', {'x': 24, 'y': 56, 'width': 56, 'height': 42, 'rx': 4})
        text(52, 72, 'trace', 9.5, None, 'middle', op='.8')
        for l in range(2):
            shape('line', {'x1': 32, 'y1': 82 + l * 8, 'x2': 72, 'y2': 82 + l * 8}, op='.35', sw=1)
        add('    <line x1="84" y1="77" x2="104" y2="77" stroke="currentColor" stroke-opacity=".7" stroke-width="1.3" marker-end="url(#sparrow)"/>')
        shape('rect', {'x': 108, 'y': 62, 'width': 56, 'height': 30, 'rx': 15}, op='.9', fill=ACC, fop='.14')
        text(136, 82, 'one code', 10, '700', 'middle', ACC)
    if i == 4:
        for k, h in enumerate([20, 38, 28, 44, 16]):
            shape('rect', {'x': 30 + k * 28, 'y': 98 - h, 'width': 20, 'height': h, 'rx': 2}, op='.6', fill='currentColor', fop='.1' if k != 3 else '.28')
        shape('rect', {'x': 114, 'y': 54, 'width': 20, 'height': 44, 'rx': 2}, op='.95', fill=ACC, fop='.22')
        add('    <line x1="24" y1="98" x2="168" y2="98" stroke="currentColor" stroke-opacity=".35"/>')

    # what / how / output
    text(14, 150, 'WHAT', 9.5, '700', None, ACC, op=None)
    for l, line in enumerate(textwrap.wrap(what, 26)):
        text(14, 168 + l * 15, line, 11, '700')
    text(14, 214, 'HOW', 9.5, '700', None, ACC)
    for l, line in enumerate(how):
        text(14, 231 + l * 16, line, 10.5, None, None, op='.82')
    add('    <rect class="s-out" x="14" y="%d" width="%d" height="26" rx="13" fill="%s" fill-opacity=".1" stroke="%s" stroke-opacity=".5" '
        'data-detail="%s"/>' % (CH - 54, CW - 28, ACC, ACC, esc(why)))
    text(CW / 2, CH - 37, out, 10.5, '700', 'middle', ACC)
    add('  </g>')
    if i < 4:
        ax = x + CW
        add('  <line id="s-a%d" class="s-arrow" x1="%d" y1="%d" x2="%d" y2="%d" stroke="currentColor" stroke-opacity=".55" stroke-width="1.8" marker-end="url(#sparrow)"/>'
            % (i + 1, ax + 3, Y0 + CH // 2, ax + GAP - 3, Y0 + CH // 2))

add('</svg>')
open(OUT, 'w', encoding='utf-8').write('\n'.join(o) + '\n')
print('wrote', OUT)
