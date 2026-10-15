"""Generate a PDF snapshot report of the gemma4:31b OfficeBench run.

Reads analysis/dashboard/summary.json (rebuild it first for fresh numbers) and writes
analysis/OfficeBench_gemma4-31b_report.pdf.

    python analysis/report_pdf.py [summary.json] [out.pdf]
"""
import json, os, sys, glob, contextlib, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether)

SUMMARY = sys.argv[1] if len(sys.argv) > 1 else 'analysis/dashboard/summary.json'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'analysis/OfficeBench_gemma4-31b_report.pdf'

INK = colors.HexColor('#18202c')
MUTED = colors.HexColor('#5a6476')
ACCENT = colors.HexColor('#2d5a9b')
LINE = colors.HexColor('#dce1e8')
PASSC = colors.HexColor('#2b7d47')
FAILC = colors.HexColor('#b8392f')
BAND = colors.HexColor('#eef1f5')

LEADERBOARD = [
    ('GPT-4 Omni (2024-05-13)', 64.52, 60.00, 21.43, 47.00),
    ('GPT-4 Turbo (2024-04-09)', 56.99, 50.63, 11.61, 38.00),
    ('Llama 3 70B-Instruct', 39.79, 41.05, 5.36, 27.33),
    ('Gemini 1.5 Pro (May 2024)', 41.94, 32.63, 7.14, 26.00),
    ('Qwen 2 72B-Instruct', 30.23, 28.42, 8.04, 21.16),
    ('Gemini 1.5 Flash (May 2024)', 34.41, 24.21, 0.89, 18.67),
    ('Gemini 1.0 Pro (Feb 2024)', 24.73, 13.68, 0.89, 12.33),
    ('GPT-3.5 Turbo (0125)', 8.60, 7.45, 0.89, 5.35),
]

d = json.load(open(SUMMARY, encoding='utf-8'))
rows = d['rows']
done = [r for r in rows if r['status'] != 'pending']
npass = sum(r['status'] == 'pass' for r in done)
nfail = len(done) - npass


def split(n):
    a = [r for r in rows if r['apps'] == n]
    dd = [r for r in a if r['status'] != 'pending']
    p = sum(r['status'] == 'pass' for r in dd)
    return len(a), len(dd), p


# ---- categorize failures by signature ----
def categorize(r):
    end = r.get('end')
    if end == 'not saved' or any('harness' in s for s in r.get('signals', [])):
        return 'Output could not be saved on Windows (harness)', 'C-HARNESS'
    if end == 'stuck' or any(s.endswith('malformed') for s in r.get('signals', [])):
        return 'Stuck / invalid-action loop', 'A-ACTION'
    if 'llm app: no key' in r.get('signals', []):
        return 'In-container llm app had no key', 'C-LLMAPP'
    if end == 'max steps':
        return 'Ran out of steps (20)', 'A-ACTION'
    chk = (r.get('check') or '')
    if 'calendar_no_overlap' in chk:
        return 'Booked a slot that overlaps an existing event', 'A-STATE'
    if 'evaluate_contain' in chk and ('ics' in chk):
        return 'Check requires an event/keyword the task does not ask for', 'EVAL-MISMATCH'
    if 'excel_cell_value' in chk or 'excel_cell_comparator' in chk:
        return 'Wrong value written / operation not applied', 'A-REASON / A-INTENT'
    if 'file_exist' in chk:
        return 'Required file operation not performed', 'A-INTENT'
    return 'Other (answer did not match the check)', 'A-REASON'


buckets = {}
for r in done:
    if r['status'] != 'fail':
        continue
    label, code = categorize(r)
    buckets.setdefault((code, label), []).append(r['id'])

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], textColor=INK, fontSize=20, leading=24, spaceAfter=2)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], textColor=MUTED, fontSize=9.5, leading=13)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=INK, fontSize=13, leading=16, spaceBefore=14, spaceAfter=4)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], textColor=INK, fontSize=10, leading=15)
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], textColor=MUTED, fontSize=8.5, leading=12)
MONO = ParagraphStyle('MONO', parent=styles['Code'], textColor=INK, fontSize=8.5, leading=12)

story = []


def p(txt, st=BODY):
    story.append(Paragraph(txt, st))


def rule():
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width='100%', thickness=0.6, color=LINE))
    story.append(Spacer(1, 4))


state_txt = {'running': 'Run in progress', 'finished': 'Run complete',
             'stopped: usage limit': 'Stopped at Ollama usage limit'}.get(d['state'], d['state'])
p('OfficeBench — gemma4:31b Run Report', H1)
p(f"Snapshot {d['generated']} &nbsp;·&nbsp; {state_txt} &nbsp;·&nbsp; {len(done)} of {len(rows)} subtasks scored", SUB)
rule()

p('Run setup', H2)
for line in [
    '<b>Model:</b> gemma4:31b, served via Ollama (no OpenAI anywhere, including the in-container llm app).',
    '<b>Reasoning:</b> the agent writes a <b>##Thought</b> before every <b>##Command</b>; the reasoning is captured per step.',
    '<b>Guardrail:</b> must switch to an app before using its actions, and use only the exact action names shown.',
    '<b>Budget:</b> up to 20 steps per subtask; evaluation uses the benchmark&rsquo;s own checks.',
]:
    p('&bull;&nbsp; ' + line)

p('Results so far', H2)
pct = 100 * npass / len(done) if done else 0
p(f"<b>{npass} passed</b> and <b>{nfail} failed</b> of {len(done)} scored &mdash; <b>{pct:.1f}%</b>. "
  f"{len(rows) - len(done)} subtasks still to run.")

# by-app table vs leaderboard
tot1, run1, p1 = split(1); tot2, run2, p2 = split(2); tot3, run3, p3 = split(3)


def cell(run, passed, total):
    if run == 0:
        return 'not started'
    return f'{100*passed/run:.1f}%  ({passed}/{run})'


data = [['Agent', f'Single app ({tot1})', f'Two apps ({tot2})', f'Three apps ({tot3})', f'Overall ({len(rows)})']]
data.append(['gemma4:31b (this run)', cell(run1, p1, tot1), cell(run2, p2, tot2), cell(run3, p3, tot3),
             f'{pct:.1f}%  ({npass}/{len(done)})'])
for name, s1, s2, s3, ov in LEADERBOARD:
    data.append([name, f'{s1:.2f}', f'{s2:.2f}', f'{s3:.2f}', f'{ov:.2f}'])

t = Table(data, colWidths=[52*mm, 30*mm, 28*mm, 30*mm, 30*mm])
t.setStyle(TableStyle([
    ('FONTSIZE', (0, 0), (-1, -1), 8.5),
    ('TEXTCOLOR', (0, 0), (-1, -1), INK),
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#e3ebf6')),
    ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
    ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(Spacer(1, 6))
story.append(t)
story.append(Spacer(1, 4))
if run2 == 0 or run3 == 0:
    p('Tasks run in order, so only single-app tasks are scored so far; the overall figure is not yet '
      'comparable to the leaderboard. Leaderboard numbers are from the OfficeBench paper.', SMALL)
else:
    p('Leaderboard numbers are from the OfficeBench paper.', SMALL)

p('Why tasks fail', H2)
if buckets:
    p(f'Of {nfail} failures so far, grouped by cause (codebook code in brackets):')
    bdata = [['Cause', 'Code', 'Count', 'Example tasks']]
    for (code, label), ids in sorted(buckets.items(), key=lambda x: -len(x[1])):
        bdata.append([Paragraph(label, SMALL), Paragraph(code, SMALL), str(len(ids)),
                      Paragraph(', '.join(ids[:6]) + (' …' if len(ids) > 6 else ''), SMALL)])
    bt = Table(bdata, colWidths=[62*mm, 32*mm, 16*mm, 60*mm])
    bt.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BACKGROUND', (0, 0), (-1, 0), BAND),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), INK),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(Spacer(1, 4))
    story.append(bt)
    story.append(Spacer(1, 6))
    p('<b>Key change from the earlier no-reasoning run:</b> the stuck / invalid-action loops that '
      'dominated before are essentially gone. Remaining failures are mostly the model computing a '
      'slightly wrong value or not applying the operation, plus a few cases where the benchmark check '
      'asks for something the task text does not state.', BODY)
else:
    p('No failures recorded yet.')

# example reasoning trace
example = None
for r in done:
    tid, sid = r['id'].split('/')
    hp = f'tasks/{tid}/outputs/{sid}/gemma4_31b_think/llm_history.json'
    if os.path.exists(hp):
        from history_to_trace import split_thought
        llm = json.load(open(hp, encoding='utf-8'))
        steps = []
        for s, pr, resp in llm[:4]:
            th = split_thought(resp)
            cmd = resp.split('##Command:', 1)[1].strip() if '##Command:' in resp else ''
            if th:
                steps.append((th, cmd))
        if steps:
            example = (r['id'], r['goal'], r['status'], steps)
            break

if example:
    cid, goal, status, steps = example
    blk = [Paragraph('Example: reasoning captured per step', H2),
           Paragraph(f'Task {cid} ({status.upper()}): {goal}', SMALL), Spacer(1, 4)]
    for i, (th, cmd) in enumerate(steps):
        blk.append(Paragraph(f'<b>Step {i} &mdash; THINKING:</b> {th}', BODY))
        if cmd:
            blk.append(Paragraph(cmd[:160].replace('<', '&lt;'), MONO))
        blk.append(Spacer(1, 3))
    story.append(KeepTogether(blk))

story.append(Spacer(1, 10))
story.append(HRFlowable(width='100%', thickness=0.6, color=LINE))
p('Generated from the live run data. The interactive dashboard (progress, full per-task traces, '
  'filters) is the companion to this snapshot.', SMALL)

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=16*mm, bottomMargin=16*mm,
                        leftMargin=16*mm, rightMargin=16*mm,
                        title='OfficeBench gemma4:31b Report', author='OfficeBench run')
doc.build(story)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
