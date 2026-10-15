"""Whole-pipeline overview figure: six stage panels, benchmark to findings.

Numbers are from analysis/full_failure_report_pdf.py, analysis/failure_codes_all_runs.json and agreement.py.

    python analysis/figures/make_fig_pipeline.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'fig_pipeline.svg')
ACC, OK, BAD = '#d97706', '#1a7f4b', '#b3391f'
W, H = 1160, 800
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


def rect(x, y, w, h, stroke='currentColor', op='.4', fill='none', fop=None, rx=5, sw=1, detail=None, dash=None):
    a = 'x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s" stroke="%s" stroke-opacity="%s" stroke-width="%g"' % (
        x, y, w, h, rx, fill, stroke, op, sw)
    if fop: a += ' fill-opacity="%s"' % fop
    if dash: a += ' stroke-dasharray="%s"' % dash
    if detail: a += ' class="p-hot" data-detail="%s"' % esc(detail)
    add('    <rect %s/>' % a)


# stage: (n, title, x, y, subtitle)
PW, PH = 360, 310
STAGES = [
    (1, 'Benchmark', 20, 78, 'what is asked'),
    (2, 'Four cells', 400, 78, 'who is asked, in what language'),
    (3, 'One run', 780, 78, 'what the agent does'),
    (4, 'Score', 20, 440, 'did it pass'),
    (5, 'Code', 400, 440, 'why it failed'),
    (6, 'Compare', 780, 440, 'what repeats'),
]

add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" color="#1b2330"' % (W, H))
add('     font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Helvetica, Arial, sans-serif"')
add('     aria-label="The whole pipeline in six stages: the 300-subtask benchmark; four cells of two models by two prompt '
    'languages; one 20-step run inside a container; scoring with three defects repaired, giving 394 passes and 557 '
    'failures; coding each failure with one primary root cause; and comparing codes across cells to find what fails '
    'everywhere.">')
add('  <defs><marker id="pparrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
    'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs>')

text(20, 34, 'The whole pipeline: 300 subtasks in, one root cause per failure out', 17, '700')
text(20, 54, 'click a stage, hover any detail, or press Play', 11.5, None, None, op='.65')

# connectors (drawn first, under the panels)
CONN = [
    (1, 'M380 233 H 400'), (2, 'M760 233 H 780'),
    (3, 'M960 388 V 414 H 200 V 440'),
    (4, 'M380 595 H 400'), (5, 'M760 595 H 780'),
]
for i, d in CONN:
    add('  <path id="p-c%d" class="p-conn" d="%s" fill="none" stroke="currentColor" stroke-opacity=".45" '
        'stroke-width="1.6" marker-end="url(#pparrow)"/>' % (i, d))

for n, title, x, y, sub in STAGES:
    add('  <g id="p-s%d" class="p-stage" data-stage="%d" transform="translate(%d,%d)">' % (n, n, x, y))
    rect(0, 0, PW, PH, op='.3', fill='currentColor', fop='.035', rx=8)
    add('    <rect class="p-head" x="0" y="0" width="%d" height="34" rx="8" fill="%s" fill-opacity=".16"/>' % (PW, ACC))
    add('    <rect x="0" y="22" width="%d" height="12" fill="%s" fill-opacity=".16"/>' % (PW, ACC))
    add('    <circle cx="22" cy="17" r="11" fill="%s"/>' % ACC)
    add('    <text x="22" y="21.5" font-size="13" font-weight="700" text-anchor="middle" fill="#ffffff" '
        'pointer-events="none">%d</text>' % n)
    text(42, 22, title, 14, '700')
    text(PW - 14, 22, sub, 10.5, None, 'end', op='.65')

    if n == 1:
        text(20, 66, '300 subtasks', 22, '700', None, ACC)
        text(20, 84, 'each ends in checks on the final files', 10.5, None, None, op='.7')
        x0, wtot = 20, 320
        segs = [(93, 'single-app'), (95, 'two-app'), (112, 'three-app')]
        cx = x0
        for k, (c, lab) in enumerate(segs):
            w = wtot * c / 300
            rect(cx, 104, w - 2, 34, op='.55', fill='currentColor', fop=str(.08 + .07 * k), rx=3,
                 detail='%d %s subtasks (%.0f%% of 300)' % (c, lab, 100 * c / 300))
            text(cx + w / 2 - 1, 126, str(c), 14, '700', 'middle')
            text(cx + w / 2 - 1, 154, lab, 10, None, 'middle', op='.7')
            cx += w
        text(20, 192, 'Eight apps in a Docker container', 11, '700')
        apps = ['calendar', 'excel', 'ocr', 'pdf', 'shell', 'word', 'email', 'llm']
        for k, a in enumerate(apps):
            ax, ay = 20 + (k % 4) * 82, 204 + (k // 4) * 32
            rect(ax, ay, 76, 24, op='.45', rx=12, detail='the %s app: the agent switches to it, then issues its actions' % a)
            text(ax + 38, ay + 16, a, 10.5, None, 'middle', mono=True)
        text(20, 292, 'A task such as: “Find a common time for Bob and Tom”', 10, None, None, op='.65')

    if n == 2:
        text(20, 62, '2 models × 2 prompt languages', 13, '700')
        text(20, 80, 'same 300 subtasks, temperature 0, one run each', 10.5, None, None, op='.7')
        text(223, 108, 'English', 11, '700', 'middle')
        text(309, 108, 'Bangla', 11, '700', 'middle')
        cells = [('gemma4:31b', '151', '50.3%', '127', '42.3%', 'think', 'bn'),
                 ('gpt-oss:20b', '86', '28.7%', '30', '51 of 300', 'en', 'bn')]
        for r, (mdl, a, ap, b, bp, _, __) in enumerate(cells):
            y = 118 + r * 84
            text(20, y + 38, mdl, 11.5, '700')
            for c, (v, p) in enumerate([(a, ap), (b, bp)]):
                cx0 = 182 + c * 86
                part = (r == 1 and c == 1)
                rect(cx0, y, 80, 70, stroke=ACC if (r == 0 and c == 0) else 'currentColor',
                     op='.8' if (r == 0 and c == 0) else '.45', fill='currentColor', fop='.05',
                     dash='4 3' if part else None,
                     detail='%s, %s prompt: %s pass (%s)%s' % (mdl, 'English' if c == 0 else 'Bangla', v, p,
                                                                ' — run still in progress' if part else ''))
                text(cx0 + 40, y + 34, v, 22, '700', 'middle', ACC if (r == 0 and c == 0) else 'currentColor')
                text(cx0 + 40, y + 54, p, 10, None, 'middle', op='.7')
        text(20, 292, 'Bangla: prompt and task machine-translated; files and JSON stay English', 10, None, None, op='.65')

    if n == 3:
        text(20, 62, 'At most 20 steps', 13, '700')
        for k, (lab, xx) in enumerate([('Prompt', 20), ('Thought + JSON', 130), ('App acts', 262)]):
            ww = 90 if k != 1 else 120
            rect(xx, 78, ww, 40, op='.5', rx=5,
                 detail=['Task, past actions and results, and the current app’s instructions — earlier thoughts are not included',
                         '##Thought: … then ##Command: {json}, capped at 512 tokens (gemma) or 2048 (gpt-oss)',
                         'The app executes the action; the observation comes back and files on disk change'][k])
            text(xx + ww / 2, 103, lab, 11, '700', 'middle')
        for xa, xb in [(112, 128), (252, 260)]:
            add('    <line x1="%d" y1="98" x2="%d" y2="98" stroke="currentColor" stroke-opacity=".7" '
                'stroke-width="1.4" marker-end="url(#pparrow)"/>' % (xa, xb))
        add('    <path d="M307 120 V 140 H 65 V 122" fill="none" stroke="currentColor" stroke-opacity=".5" '
            'stroke-width="1.3" marker-end="url(#pparrow)"/>')
        text(186, 156, 'history grows, thoughts do not', 10, None, 'middle', op='.7')
        text(20, 190, 'Step budget', 11, '700')
        for k in range(20):
            used = k < 4
            rect(20 + k * 16.5, 200, 13, 22, stroke=ACC if used else 'currentColor', op='.9' if used else '.35',
                 fill=ACC if used else 'none', fop='.35' if used else None, rx=2,
                 detail='step %d%s' % (k + 1, ' — subtask 1-2/0 used four steps and finished' if used else ''))
        text(20, 244, 'Ends at finish_task, step 20, or when stuck', 10.5, None, None, op='.75')
        text(20, 262, 'Limits that cause failures:', 10.5, '700')
        text(20, 278, 'one Excel cell per action  ·  50-token llm app', 10, None, None, op='.75')
        text(20, 292, 'shell wraps commands in bash -c', 10, None, None, op='.75')

    if n == 4:
        text(20, 62, '951 scored runs', 22, '700', None, ACC)
        pw, fw = 320 * 394 / 951, 320 * 557 / 951
        rect(20, 80, pw - 2, 40, stroke=OK, op='.7', fill=OK, fop='.12', rx=3,
             detail='394 runs pass (151 + 127 + 86 + 30)')
        rect(20 + pw, 80, fw, 40, stroke=BAD, op='.7', fill=BAD, fop='.12', rx=3,
             detail='557 runs fail: 149 + 173 + 214 + 21 — these need explaining')
        text(20 + pw / 2, 106, '394 pass', 13, '700', 'middle', OK)
        text(20 + pw + fw / 2, 106, '557 fail', 13, '700', 'middle', BAD)
        text(20, 148, 'Three scoring defects repaired first', 11, '700')
        fx = [('Email check', 'read the run’s own testbed, not a path that only exists in the container'),
              ('Mailbox match', 'exact name first, so an empty look-alike folder is not read'),
              ('Text encoding', 'task files read as UTF-8, not the Windows default')]
        for k, (a, b) in enumerate(fx):
            rect(20, 160 + k * 38, 320, 32, op='.4', rx=4, detail=b)
            text(32, 181 + k * 38, a, 11, '700')
            text(142, 181 + k * 38, 'hover for the fix', 10, None, None, op='.55')
        text(20, 292, 'official → corrected:  132→151 · 103→127 · 80→+6', 10, None, None, op='.7', mono=True)

    if n == 5:
        text(20, 62, 'One question per failed run', 13, '700')
        rect(20, 74, 320, 52, stroke=ACC, op='.8', sw=1.4, rx=5,
             detail='Is the final output correct for the task as written? Meaning, not surface form.')
        text(180, 96, 'Is the output correct for', 11.5, '700', 'middle')
        text(180, 112, 'the task as written?', 11.5, '700', 'middle')
        add('    <line x1="100" y1="128" x2="100" y2="148" stroke="currentColor" stroke-opacity=".7" stroke-width="1.4" marker-end="url(#pparrow)"/>')
        add('    <line x1="260" y1="128" x2="260" y2="148" stroke="currentColor" stroke-opacity=".7" stroke-width="1.4" marker-end="url(#pparrow)"/>')
        text(108, 142, 'yes, still FAIL', 9.5, None, None, op='.7')
        text(268, 142, 'no', 9.5, None, None, op='.7')
        rect(20, 152, 160, 54, stroke=ACC, op='.8', fill=ACC, fop='.12', rx=5,
             detail='Benchmark defect (BM): the check, a reference file or a tool is wrong. 47 of gemma English’s 149 failures.')
        text(100, 175, 'BM', 20, '700', 'middle', ACC)
        text(100, 195, 'benchmark defect', 10, None, 'middle', op='.8')
        rect(190, 152, 150, 54, op='.5', rx=5,
             detail='Find the decisive step: the earliest step that, corrected alone, would most likely have passed. Then code that step.')
        text(265, 175, 'decisive step', 12, '700', 'middle')
        text(265, 195, 'the agent’s own error', 10, None, 'middle', op='.8')
        text(20, 228, 'One primary code + any tags', 11, '700')
        text(20, 244, 'C-AMBIG · C-WEAKCHECK · C-HARNESS · C-LLMAPP', 10, None, None, op='.75', mono=True)
        rect(20, 256, 320, 40, stroke=OK, op='.55', fill=OK, fop='.07', rx=4,
             detail='Two annotators coded 16 cases independently: kappa 0.78 on the primary code, 0.64 on benchmark-versus-agent.')
        text(180, 273, 'agreement on 16 double-coded cases', 10.5, None, 'middle', op='.8')
        text(180, 288, 'κ = 0.78', 13, '700', 'middle', OK)

    if n == 6:
        text(20, 62, 'Same subtask, three runs', 13, '700')
        text(20, 80, 'gemma English, gemma Bangla, gpt-oss English', 10.5, None, None, op='.7')
        items = [('119', 'fail in all three', 'the shared core', BAD),
                 ('44', 'fail for the identical cause', 'in all three', BAD),
                 ('55', 'pass in all three', 'the easy subtasks', OK),
                 ('57', 'a benchmark defect decides', 'at least one run', ACC)]
        for k, (num, l1, l2, col) in enumerate(items):
            iy = 98 + k * 46
            rect(20, iy, 320, 40, stroke=col, op='.55', fill=col, fop='.06', rx=4,
                 detail={'119': '119 of 300 subtasks fail in every full run', '44': '44 subtasks fail for exactly the same coded cause in all three runs',
                         '55': '55 subtasks pass in every full run',
                         '57': 'A benchmark defect decides at least one run on 57 subtasks — the fixes that pay off most'}[num])
            text(60, iy + 28, num, 22, '700', 'middle', col)
            text(92, iy + 18, l1, 11, '700')
            text(92, iy + 32, l2, 10, None, None, op='.75')
        text(20, 292, 'what fails everywhere vs what is specific to a model', 10, None, None, op='.65')

    add('  </g>')

add('</svg>')
open(OUT, 'w', encoding='utf-8').write('\n'.join(o) + '\n')
print('wrote', OUT)
