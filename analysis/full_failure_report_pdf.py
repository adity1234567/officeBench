"""Long failure analysis of every OfficeBench run so far: why the agents fail.

Covers gemma4:31b (English and Bangla, 300 subtasks each), gpt-oss:20b (English, 300; Bangla, in progress),
the early gemma no-reasoning pilots and the qwen2.5-7b pilot. Per-subtask root-cause codes are in
analysis/failure_codes_all_runs.json (built from the trace-by-trace classification).

    python analysis/full_failure_report_pdf.py [out.pdf]
"""
import os, sys, json

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether, CondPageBreak, PageBreak)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'analysis', 'OfficeBench_full_failure_analysis.pdf')
CODES = json.load(open(os.path.join(ROOT, 'analysis', 'failure_codes_all_runs.json'), encoding='utf-8'))

INK = colors.HexColor('#18202c')
MUTED = colors.HexColor('#5a6476')
ACCENT = colors.HexColor('#2d5a9b')
LINE = colors.HexColor('#dce1e8')
BOX = colors.HexColor('#f6f7f9')
WARM = colors.HexColor('#fbeee6')

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], textColor=INK, fontSize=21, leading=25, alignment=0, spaceAfter=3)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], textColor=MUTED, fontSize=9.5, leading=13)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=INK, fontSize=14.5, leading=18, spaceBefore=13, spaceAfter=5)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], textColor=ACCENT, fontSize=11, leading=14, spaceBefore=9, spaceAfter=2)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], textColor=INK, fontSize=9.6, leading=13.8, spaceAfter=3)
BUL = ParagraphStyle('BUL', parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=1.5)
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], textColor=MUTED, fontSize=8.2, leading=11)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], textColor=INK, fontSize=8, leading=10.3)
TINY = ParagraphStyle('TINY', parent=CELL, fontSize=7.4, leading=9.2)
HEAD = ParagraphStyle('HEAD', parent=CELL, fontName='Helvetica-Bold', textColor=colors.white)
QUOTE = ParagraphStyle('QUOTE', parent=BODY, textColor=MUTED, fontName='Helvetica-Oblique', leftIndent=12, fontSize=9)

story = []
p = lambda t, s=BODY: story.append(Paragraph(t, s))
bul = lambda x: Paragraph(x, BUL, bulletText='•')


def bullets(items):
    for it in items:
        story.append(bul(it))


def table(rows, widths, add=True, style=CELL, zebra=True):
    data = [[Paragraph(str(c), HEAD) for c in rows[0]]] + [[Paragraph(str(c), style) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    cmds = [('BACKGROUND', (0, 0), (-1, 0), ACCENT), ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 2.6), ('BOTTOMPADDING', (0, 0), (-1, -1), 2.6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')]
    if zebra:
        cmds.append(('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BOX]))
    t.setStyle(TableStyle(cmds))
    if add:
        story.append(t)
    return t


def boxed(text, bg=BOX):
    t = Table([[Paragraph(text, BODY)]], colWidths=[178*mm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), bg), ('BOX', (0, 0), (-1, -1), 0.6, LINE),
                           ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                           ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(t)


def cause(title, what, evidence, why=None, keep=True):
    blk = [Paragraph(title, H3), Paragraph(what, BODY)] + [bul(e) for e in evidence]
    if why:
        blk.append(Paragraph(f'<b>Why:</b> {why}', BODY))
    story.append(KeepTogether(blk) if keep else blk[0])
    if not keep:
        for b in blk[1:]:
            story.append(b)


# ====================================================================== title page
p('Why the agents fail on OfficeBench', H1)
p('A failure analysis of every OfficeBench run so far: gemma4:31b in English and Bangla (300 subtasks each), '
  'gpt-oss:20b in English (300 subtasks) and in Bangla (first 51 subtasks, run in progress), and the early pilot '
  'runs &middot; 2026-10-04', SUB)
story.append(Spacer(1, 3))
story.append(HRFlowable(width='100%', thickness=0.6, color=LINE))

p('Contents', H3)
for line in ['1. Summary', '2. What was run, and how the harness works', '3. Scores, and the fixes needed to score correctly',
             '4. How failures were classified', '5. gemma4:31b in English: why its 149 failures happen',
             '6. gemma4:31b in Bangla: why its 173 failures happen', '7. gpt-oss:20b in English: why its 214 failures happen', '8. gpt-oss:20b in Bangla: the first 51 subtasks',
             '9. The pilot runs: no written reasoning, and Qwen2.5-7B', '10. Across all runs: what fails everywhere and what is model-specific',
             '11. Benchmark and harness defects (catalogue)', '12. What to fix, and what to test next',
             'Appendix A. Agent behaviour statistics by run', 'Appendix B. Root cause of every failed subtask, all four runs']:
    p(line, BUL)

# ====================================================================== 1 summary
p('1. Summary', H2)
p('Across 951 scored runs of four main configurations, the agents fail for four broad reasons, in roughly this '
  'order of importance: <b>defects in the benchmark itself</b>, <b>errors in the content the agent writes</b>, '
  '<b>running out of the 20-step budget</b>, and <b>problems producing a valid action at all</b>. Which of these '
  'dominates depends on the model and the language:')
bullets([
    '<b>gemma4:31b, English: 151 of 300 pass (50.3%).</b> Its failures are mostly not reasoning errors. A third '
    '(47) are decided by benchmark defects: checks that expect something the task never asks for, wrong reference '
    'files, or tools that silently corrupt output. The rest are wrong content (37: OCR misreads copied, labels '
    'dropped, arithmetic slips), running out of steps (28, mostly writing one spreadsheet cell per action), and long '
    'outputs cut off at the 512-token response limit (14).',
    '<b>gemma4:31b, Bangla: 127 of 300 pass (42.3%).</b> 130 of its 173 failures also happen in English, and 89 of '
    'those for exactly the same reason. The 40 Bangla-only failures are mostly about writing the result back in '
    'English: correct answers written in Bangla script (15), names in the wrong case (4), different English words '
    '(3), and translation errors (5). Only 6 come from the agent reading or reasoning differently.',
    '<b>gpt-oss:20b, English: 86 of 300 pass (28.7%), and only 8 of 112 three-app tasks.</b> Its largest problem is '
    'that it often cannot produce an action in the benchmark&rsquo;s format (54 failures; malformed steps in 282 of '
    '299 runs). It falls back on its own built-in tools ("container.exec", "repo_browser.print_tree"), writes a '
    'second "##Thought" where the command should be, or returns empty replies. Harness behaviours make this worse: '
    'native tool calls become invalid actions, list-form shell commands lose their quoting, and the in-container llm '
    'app returns nothing because gpt-oss spends its 50 tokens on hidden reasoning (most of its 24 "empty result" '
    'failures). It also finishes early more often (24).',
    '<b>gpt-oss:20b, Bangla (first 51 single-app subtasks): 30 pass, against 23 in English on the same subtasks.</b> '
    'The Bangla prompt almost removed gpt-oss&rsquo;s English-specific format failures (container.exec 89 to 1 calls, '
    'empty replies 21 to 0, malformed steps 212 to 74). Unlike gemma, it did not answer in Bangla and made no '
    'name-case errors; its reasoning stays in English. One run each, so this needs repeating.',
    '<b>Pilots.</b> Writing the reasoning before each action barely helps gemma on single-app tasks (58 vs 60 of 87). '
    'Qwen2.5-7B passed 3 of 12, and 7 of its runs ended stuck after repeated malformed actions.',
    '<b>Shared failure core.</b> Of the 300 subtasks, 119 fail in all three full runs and 55 pass in all three; 44 '
    'fail for the identical cause in all three. A benchmark defect decides at least one run on 57 subtasks.',
    '<b>The agents almost never check their work.</b> gemma read back what it wrote in about 2% of writing runs (3 of '
    '203 in English, 4 of 197 in Bangla); gpt-oss in 18 of 126.',
])
boxed('<b>Scores in this report are corrected.</b> The repository&rsquo;s email check fails on the host machine for every '
      'run, so the official result files undercount (gemma English 132, gemma Bangla 103, gpt-oss English 80). All numbers here use the email check '
      'fixed and mailboxes matched by exact name. Details in Section 3.', WARM)

# ====================================================================== 2 setup
story.append(PageBreak())
p('2. What was run, and how the harness works', H2)
table([
    ['Run tag', 'Model', 'Prompt', 'Written reasoning', 'Subtasks', 'Pass (corrected)', 'Dates'],
    ['gemma4_31b_think', 'gemma4:31b', 'English', 'yes', '300', '151 (50.3%)', 'Oct 2'],
    ['gemma4_31b_bn', 'gemma4:31b', 'Bangla', 'yes', '300', '127 (42.3%)', 'Oct 2 &ndash; Oct 3'],
    ['gpt-oss_20b_en', 'gpt-oss:20b', 'English', 'yes (own reasoning channel)', '300', '86 (28.7%)', 'Oct 3 &ndash; Oct 4'],
    ['gpt-oss_20b_bn', 'gpt-oss:20b', 'Bangla', 'yes (own reasoning channel)', '51 of 300', '30 (58.8%)', 'Oct 4, in progress'],
    ['gemma4_31b_first10 / next20 / probe / rest / gemmatest', 'gemma4:31b', 'English', 'no', '91', '61', 'Sep 27 &ndash; Oct 2'],
    ['qwen2.5-7b_test / batch10', 'qwen2.5-7b', 'English', 'no', '12', '3', 'Sep 27'],
], [44*mm, 21*mm, 15*mm, 26*mm, 18*mm, 24*mm, 30*mm])
story.append(Spacer(1, 5))
p('<b>The benchmark.</b> OfficeBench has 300 subtasks: 93 single-app, 95 two-app and 112 three-app. In each, an agent '
  'works inside a Docker container with eight apps (calendar, excel, ocr, pdf, shell, word, email, llm). At each step '
  'it sees the task, the history of previous actions and their results, and the instructions for the current app, '
  'and must output one JSON action. A run ends when the agent calls finish_task, after 20 steps, or when the harness '
  'detects that it is stuck (repeated invalid actions). The result is scored by checks on the final files and answer.')
p('<b>Details of this harness that matter for the failures:</b>')
bullets([
    '<b>Response format:</b> the agent writes "##Thought: ..." then "##Command: {json}". The prompt carries earlier '
    'actions and results, but not earlier thoughts, so the agent has to rebuild its working state at every step.',
    '<b>Response length:</b> capped at 512 tokens for the gemma runs and 2048 for gpt-oss (raised on Oct 3 at 15:02, '
    'just before the gpt-oss run). A long command is cut off and rejected as "Malformed action!".',
    '<b>One cell per action:</b> the Excel app writes a single cell per action, so copying a table of more than about '
    '15 values cannot fit in 20 steps.',
    '<b>The llm app</b> calls the agent&rsquo;s own model, with a 50-token answer limit.',
    '<b>The shell</b> starts in "/" (not /testbed/data) and wraps every command in <font face="Courier">bash -c """...'
    '"""</font>, so a command containing double quotes breaks. A command given as a list is joined with spaces, so '
    '<font face="Courier">["bash","-lc","ls -R /testbed/data"]</font> runs plain <font face="Courier">ls</font> in "/".',
    '<b>Decoding:</b> temperature 0, one run per subtask and configuration.',
    '<b>Bangla condition:</b> system prompt, task text and instructions translated into Bangla by gemma4:31b; JSON '
    'actions, app names and all files stay English; no instruction about the language of answers.',
])

# ====================================================================== 3 scores
p('3. Scores, and the fixes needed to score correctly', H2)
table([
    ['Run', 'Official result file', 'Corrected', 'Single-app', 'Two-app', 'Three-app'],
    ['gemma4:31b English', '132 / 300', '151 / 300', '63 / 93', '60 / 95', '28 / 112'],
    ['gemma4:31b Bangla', '103 / 300', '127 / 300', '48 / 93', '51 / 95', '28 / 112'],
    ['gpt-oss:20b English', '80 / 300', '86 / 300', '41 / 93', '37 / 95', '8 / 112'],
    ['gpt-oss:20b Bangla (so far)', 'not written yet', '30 / 51', '30 / 51', '-', '-'],
], [52*mm, 32*mm, 26*mm, 23*mm, 23*mm, 22*mm])
story.append(Spacer(1, 4))
p('Three scoring problems were fixed for every run in this report:')
bullets([
    '<b>Email checks:</b> <font face="Courier">apps/email_app/email_list_emails.py</font> reads the hard-coded path '
    '/testbed/emails, which exists only inside the container, and the fallback loop in '
    '<font face="Courier">utils/evaluate.py</font> raises a NameError. Every email check therefore fails on the host. '
    'Fixed by reading the run&rsquo;s own testbed folder.',
    '<b>Mailbox matching:</b> when a mailbox is not found by exact name, the check picks the first folder whose name '
    'contains the username; a failed send to "Bob, Tom" created an empty folder that the check read instead of Bob&rsquo;s '
    '(3-12/0). Fixed by matching exact names first.',
    '<b>Text encoding:</b> the local evaluation read task files with the Windows default encoding, which garbles '
    'non-ASCII keywords such as "caf&eacute;" (1-16/0). All scoring here uses UTF-8.',
])
p('These fixes change only how runs are scored, not what the agents did. Runs that crashed or got empty replies from '
  'the model API are counted as failures and labelled as infrastructure (INF).', SMALL)

# ====================================================================== 4 method
p('4. How failures were classified', H2)
p('Every failed run of the three main configurations was given one primary root cause by reading its trace step by '
  'step (thought, action, observation) and comparing the final files with the task and the checks. The primary cause '
  'is the earliest thing that, if fixed alone, would most likely have made the run pass. A benchmark defect is '
  'primary only when the agent&rsquo;s own work would otherwise have passed; otherwise it is noted as secondary. '
  'Runs were classified by several analysis passes; the main claims about code were verified directly against the '
  'repository.')
table([
    ['Code', 'Root cause', 'Meaning'],
    ['BM', 'Benchmark defect', 'A check, reference file or tool is wrong, or the check asks for something the task does not'],
    ['WC', 'Wrong content', 'The output exists but a value is wrong: reasoning or arithmetic error, OCR misread copied, label dropped, wrong format'],
    ['SB', 'Out of steps', 'Hit the 20-step limit, usually writing one cell per action or re-asking the llm app'],
    ['TL', 'Cut-off output loop', 'A long command exceeds the response limit, is rejected, and is retried'],
    ['ER', 'Empty result, gave up', 'An empty listing (often a wrong-case username) or empty llm-app reply taken as "nothing exists"'],
    ['TR', 'Task read differently', 'Did a different operation from the one asked (wrong target, scope or interpretation)'],
    ['PF', 'Premature finish', 'Declared the task done with a required output missing'],
    ['CAP', 'Capability claim', 'Said the output was impossible (e.g. "no image tool") and skipped it'],
    ['FMT', 'Action format', 'Could not produce a valid action: invented tools, missing command, empty replies'],
    ['DL', 'Deliberation loop', 'Reasoning circles until the response limit without producing an action'],
    ['AL', 'Answer language (Bangla only)', 'Correct answer written in Bangla script; English check fails'],
    ['NC', 'Name case (Bangla only)', 'A name given only in Bangla script rewritten in Latin with the wrong case'],
    ['WD', 'Word choice (Bangla only)', 'A different English word or format chosen when translating back'],
    ['TX', 'Translation (Bangla only)', 'The machine translation changed the task or translated a literal'],
    ['OTH / INF', 'Other / infrastructure', 'Other causes; crashed runs and empty API replies'],
], [16*mm, 40*mm, 122*mm])

# ====================================================================== 5 gemma EN
story.append(PageBreak())
p('5. gemma4:31b in English: why its 149 failures happen', H2)
table([
    ['Root cause', 'Single-app', 'Two-app', 'Three-app', 'Total'],
    ['Benchmark defect (BM)', '12', '11', '24', '47'],
    ['Wrong content (WC)', '6', '11', '20', '37'],
    ['Out of steps (SB)', '1', '2', '25', '28'],
    ['Cut-off output loop (TL)', '1', '4', '9', '14'],
    ['Empty result, gave up (ER)', '5', '2', '3', '10'],
    ['Task read differently (TR)', '4', '0', '2', '6'],
    ['Other (OTH)', '1', '3', '0', '4'],
    ['Premature finish (PF)', '0', '2', '0', '2'],
    ['Infrastructure (INF)', '0', '0', '1', '1'],
    ['<b>Failures</b>', '<b>30</b>', '<b>35</b>', '<b>84</b>', '<b>149</b>'],
], [70*mm, 26*mm, 26*mm, 26*mm, 26*mm])
story.append(Spacer(1, 4))
p('The picture changes with task size. Single-app failures are mostly benchmark defects and small content or '
  'interpretation errors. On three-app tasks the agent mostly runs out of steps or writes incomplete content, because '
  'a chain of three apps with one-cell-per-action writing does not fit in 20 steps.')

cause('5.1 Benchmark defects (47)',
      'Nearly a third of English failures cannot be passed by an agent that does exactly what the task says, or depend '
      'on an ambiguous reading. Examples (full catalogue in Section 10):',
      ['1-2/0 "find a common time for Bob and Tom": the agent correctly answered 14:30&ndash;15:30, but the check requires '
       'a calendar event the task never asks for.',
       '1-5/1 "reduce half amount of apple": the agent wrote 1; the Excel tool erases the value 1 (<font face="Courier">if '
       'text == True</font>), so the cell is saved empty while the tool reports success.',
       '1-6/3: the agent updated salary.xlsx as the task says; the check reads company_budget.xlsx.',
       '1-9/0: the expected average is 80.5; the true mean of the 20 scores is 80.05.',
       '3-20/0: the check needs DTSTART:...T130000Z, but the calendar tool never writes the "Z".',
       '3-4/0: convert_to_pdf ignores the requested PDF name and keeps the source file&rsquo;s name.'])

cause('5.2 Wrong content (37)',
      'The output exists but a value is wrong. Three sub-patterns dominate:',
      ['<b>OCR errors copied without checking:</b> 2-10/0 wrote the OCR misreads "Mice", "ob" and "avid" as student names; '
       '3-11/0 emailed "Ton" instead of Tom.',
       '<b>Labels and format lost:</b> 2-23/0 wrote 104.98 without the label "total due"; 2-50/0 wrote "$1,200,000" where '
       'the check expects 1200000; 1-4/3 wrote "utilities" for "utilities fee".',
       '<b>Reasoning and arithmetic:</b> 1-5/3 computed the correct 2,729,881 in one step, then recomputed it at the next '
       'step as 2,730,381 and wrote that (earlier thoughts are not in the prompt); 3-8/4 used the wrong pair of years.'],
      why='the agent never re-reads what it wrote and treats tool output (especially OCR) as reliable.')

cause('5.3 Out of steps (28)',
      'Almost all are three-app tasks. The agent&rsquo;s plan is usually right but cannot fit in 20 steps.',
      ['Copying a table cell by cell: 1-11/1 needed about 26 actions to write two 4-row files; 3-35/0 to 3-41/0 run out '
       'while filling a spreadsheet and never reach the email or calendar step.',
       'Re-asking the 50-token llm app for a "complete" text: 3-26/0 made 15 llm attempts and never wrote the document.',
       'Bulk methods exist (copy a file in the shell, or one Python command), but the agent used shell Python in 1 of '
       '291 runs.'])

cause('5.4 Cut-off output loops (14)',
      'A whole document, a long prompt, or reasoning that re-lists all the data fills the 512-token response, so the '
      'command is cut off and rejected. The agent then retries the same action.',
      ['1-19/1 put the whole abstract into one write_to_file call; it was rejected at every step from 5 to 19.',
       '2-43/0 re-listed all 20 yearly revenues in its reasoning before each send_email; the command was cut off 15 times '
       'in a row.',
       'Across the run, 171 of 273 malformed steps were commands cut off mid-JSON; in 167 of 177 back-to-back malformed '
       'pairs the agent repeated the same action.'])

cause('5.5 Empty result, gave up (10)',
      'An empty listing is taken as proof that nothing exists.',
      ['1-22/2 "is my rent due?": listed the mailbox "alice" (the folder is "Alice"), got "No emails found", answered '
       '"no".',
       '3-90/0: listed only Bob&rsquo;s calendar, got "No events found" and stopped; the data was in Alice.ics.',
       'Of 18 runs that hit an empty listing in the earlier analysis, only 2 passed; in 14 the data existed under another '
       'name or capitalisation.'])

cause('5.6 Task read differently, premature finish, other (12)',
      'Smaller groups:',
      ['<b>Task read differently (6):</b> 1-4/2 "add annual bonus $50000" added 50000 to the existing bonus row instead of '
       'adding a new row; 1-5/2 ignored "for each day"; 1-8/1 deleted one header too many.',
       '<b>Premature finish (2):</b> 2-24/0 put the computed average only in its answer, not in score.xlsx.',
       '<b>Other (4):</b> files written with a relative path while the shell is in "/" (2-34/0: '
       '<font face="Courier">echo ... &gt; lowest.txt</font>), so the output lands outside /testbed/data.'])

cause('5.7 Behaviour behind these failures',
      'Measured across all English runs:',
      ['<b>No checking:</b> read back what it wrote in 3 of 203 writing runs.',
       '<b>Finishing early:</b> 24 of 116 finished runs whose task names an output file never created it (0 of 14 '
       'single-app, 9 of 47 two-app, 15 of 55 three-app).',
       '<b>Rebuilding state:</b> 24% of steps re-copy five or more numbers from earlier results into the thought.',
       '<b>Underestimating tools:</b> in 10 of 21 tasks needing an image, the reasoning says there is no image tool, '
       'though Word to PDF to image works; 5 runs created an empty placeholder image instead, which passes '
       '"file exists" checks.',
       '<b>Invented details:</b> 28 of 68 emails went to addresses never seen in the task, 27 of them @example.com.',
       '<b>What does not fail:</b> stated intention and action agree (app switch 390 of 390; "task complete" and a '
       'finish 154 of 155), and quoted text in the task is copied exactly (17 of 17).'])

# ====================================================================== 6 gemma BN
story.append(PageBreak())
p('6. gemma4:31b in Bangla: why its 173 failures happen', H2)
p('The same model on the same 300 subtasks, with the prompt in Bangla. Comparing it with the English run separates '
  'what the language causes from what the agent and benchmark cause anyway.')
table([
    ['Group', 'Failures', 'What it means'],
    ['Fail in both languages, same cause', '89', 'Not a language effect'],
    ['Fail in both languages, different cause', '41', 'Both fail, but differently; a few are language effects'],
    ['Fail only in Bangla', '40', 'Candidates for language effects'],
    ['Infrastructure (2 empty API replies, 1 crash)', '3', 'Not agent behaviour'],
    ['<b>All Bangla failures</b>', '<b>173</b>', ''],
    ['For comparison: fail only in English', '18', 'Subtasks Bangla passes and English fails'],
], [76*mm, 22*mm, 80*mm])
story.append(Spacer(1, 4))
table([
    ['Root cause (Bangla)', 'Single-app', 'Two-app', 'Three-app', 'Total'],
    ['Benchmark defect (BM)', '12', '6', '21', '39'],
    ['Wrong content (WC)', '9', '11', '18', '38'],
    ['Out of steps (SB)', '1', '0', '19', '20'],
    ['Task read differently (TR)', '4', '6', '6', '16'],
    ['<b>Answer in Bangla script (AL)</b>', '8', '7', '0', '15'],
    ['Cut-off output loop (TL)', '3', '5', '5', '13'],
    ['Empty result, gave up (ER)', '1', '4', '4', '9'],
    ['<b>Translation changed the task (TX)</b>', '0', '1', '4', '5'],
    ['<b>Name in the wrong case (NC)</b>', '4', '0', '0', '4'],
    ['Capability claim (CAP)', '0', '0', '4', '4'],
    ['<b>Different English word (WD)</b>', '3', '0', '0', '3'],
    ['Infrastructure (INF)', '0', '2', '1', '3'],
    ['Other (OTH)', '0', '0', '2', '2'],
    ['Premature finish (PF)', '0', '2', '0', '2'],
    ['<b>Failures</b>', '<b>45</b>', '<b>44</b>', '<b>84</b>', '<b>173</b>'],
], [70*mm, 26*mm, 26*mm, 26*mm, 26*mm])
p('Bold rows are causes that exist only because of the Bangla prompt.', SMALL)

cause('6.1 Failures caused by the language (27 of the 40 Bangla-only failures)',
      'Most language-caused failures happen when the result has to be written back in English, not when the task is '
      'understood:',
      ['<b>Answer in Bangla script (15):</b> nothing tells the agent which language to answer in, so it answers in '
       'Bangla, with Bangla digits; the checks look for English words or ASCII digits. The content matched the English '
       'run every time (e.g. 1-10/0: "the difference is 40" in Bangla). Three more correct Bangla answers are hidden '
       'among subtasks both languages fail (1-22/2, 1-22/3, 1-22/4), where English got the answer wrong.',
       '<b>Name in the wrong case (4):</b> the Bangla task writes "Bob" only in Bangla script, which has no capital '
       'letters; rewritten for the tool it becomes "bob", the case-sensitive mailbox lookup is empty, and the agent '
       'answers "no emails". Names given in Latin letters in the prompt kept their case in 49 of 49 tool calls; names '
       'given only in Bangla script in 26 of 37.',
       '<b>Different English word (3):</b> "travelling" became the event "Trip to Florida", "yogurt" became "curd", '
       '"8:00" became "08:00 AM". Words the agent could copy from a file ("onion", "stock") were never lost.',
       '<b>Translation errors (5):</b> the translator translated the quoted homework text, which the agent then copied '
       'into the file in Bangla (3-56/0); "make a post reward.jpg" became "make a post <i>for</i> reward.jpg" (3-55/0); '
       '"sum all the costs" became a verb that also means "add" (3-68/0); an output file was described as already '
       'existing (3-17/0); "except sleeping" lost its event-name sense (2-40/2).'])

cause('6.2 Failures not clearly caused by the language (13 of the 40)',
      'With a faithful translation, the Bangla agent still failed differently from English in a few runs:',
      ['<b>Task read differently (4):</b> dropped a column (1-11/0), put meetings in the user&rsquo;s calendar instead '
       'of the students&rsquo; (2-17/0), listed only CS majors for "taking CS161" (2-20/0), looked for '
       'notification.eml as an existing file (2-38/2).',
       '<b>Reasoning (2):</b> used the budget as income (2-32/1); recounted 11 qualifying terms as 10 (3-87/0).',
       '<b>Execution (7):</b> rewrote whole documents and was cut off (4), ran out of steps re-asking the llm app (2), '
       'and said there was no image tool (1).',
       'A recurring Bangla pattern is treating a file the task asks it to <i>create</i> as one that should already exist '
       '(7 runs). The translations phrase these files with the Bangla definite marker ("send <i>the</i> email '
       'notification.eml"), which presents them as existing.'])

cause('6.3 Where Bangla does better (18 subtasks)',
      'Bangla passes 18 subtasks that English fails:',
      ['<b>English stepped into environment traps (7):</b> double quotes breaking shell commands (2-36/3, 3-89/0), a '
       'relative path (2-34/0), one email to two addresses (2-45/0), .png instead of .jpg (3-70/0), an unsupported '
       'attachment field (3-61/0), a lower-case mailbox name that Bangla retried as "Bob" (2-39/0).',
       '<b>Shorter Bangla reasoning (7):</b> on three-app tasks Bangla reasoning averages 336 characters per step against '
       '422 in English, and it calls the llm app less (151 vs 256 calls). English more often fills the 512-token '
       'response before reaching the command (62 vs 19 responses cut off before the command). Runs with a malformed step: '
       '69 English vs 30 Bangla.',
       '<b>Translation settled an ambiguity (2), avoided a duplicate event (1), chose the expected word (1).</b>',
       'Net effect: the gap is 15 subtasks on single-app tasks, 9 on two-app tasks, and 0 on three-app tasks.'])

cause('6.4 What Bangla does not change',
      'For the paper, the important negative results:',
      ['The written reasoning is about 83% Bangla script; 94% of the English words in it are copied names, file names and '
       'data. Only the reasoning the model writes is visible; this does not show how it reasons internally.',
       'No wrong number, date or path was traced to reading Bangla.',
       'The agent&rsquo;s habits are the same in both languages: no checking of its work (4 of 197 Bangla writing runs), '
       'one cell per action, retry loops, giving up on empty results.',
       'Values passed to tools stay English (no Bangla in cells, events or emails, except 3 runs: two copied the '
       'translated homework text and one wrote a congratulation letter to a student in Bangla).'])

# ====================================================================== 7 gpt-oss
story.append(PageBreak())
p('7. gpt-oss:20b in English: why its 214 failures happen', H2)
p('gpt-oss passes 86 of 300: 41 of 93 single-app, 37 of 95 two-app and only 8 of 112 three-app. On the same 300 '
  'subtasks gemma4:31b English passes 151; gemma passes 82 of the subtasks gpt-oss fails, and gpt-oss passes 17 that '
  'gemma fails.')
table([
    ['Root cause (gpt-oss)', 'Single-app', 'Two-app', 'Three-app', 'Total'],
    ['<b>Action format (FMT)</b>', '17', '24', '13', '54'],
    ['Wrong content (WC)', '9', '14', '12', '35'],
    ['Premature finish (PF)', '7', '3', '14', '24'],
    ['Empty result / empty llm-app reply (ER)', '3', '3', '18', '24'],
    ['Benchmark defect (BM)', '8', '2', '9', '19'],
    ['Out of steps (SB)', '2', '2', '13', '17'],
    ['Other (OTH: list-form commands, quoting)', '1', '5', '8', '14'],
    ['Task read differently (TR)', '3', '2', '9', '14'],
    ['Capability claim (CAP)', '1', '2', '2', '5'],
    ['Cut-off output loop (TL)', '1', '0', '4', '5'],
    ['Deliberation loop (DL)', '0', '0', '2', '2'],
    ['Infrastructure (INF)', '0', '1', '0', '1'],
    ['<b>Failures</b>', '<b>52</b>', '<b>58</b>', '<b>104</b>', '<b>214</b>'],
], [70*mm, 26*mm, 26*mm, 26*mm, 26*mm])
story.append(Spacer(1, 4))

cause('7.1 It often cannot produce a valid action (54 failures; malformed steps in 282 of 299 runs)',
      'gpt-oss produced 1,671 malformed steps (gemma English: 273). The failure has a few distinct forms:',
      ['<b>Its own built-in tools:</b> instead of the benchmark&rsquo;s actions it calls the tools it was trained with, '
       'such as <font face="Courier">{"app": "container.exec", "cmd": ["bash","-lc","ls -R /testbed/data"]}</font> or '
       '<font face="Courier">repo_browser.print_tree</font>. These arrive through Ollama&rsquo;s native tool-call channel; '
       'the harness turns the tool name into the "app" field and leaves "action" empty, so they are always rejected. '
       'Some form of this appears in 89 of 109 failed single- and two-app runs, and also in 29 of 78 passing runs.',
       '<b>Invented action names:</b> list_dir, exec, pdf.create_pdf, pdf.list_actions, llm.generate_text, '
       'excel.read_excel, excel.write_file.',
       '<b>A second "##Thought" where the command should be:</b> "##Command: ##Thought: I need to write the first 5 '
       'student scores..." Usually a one-step slip, but it recurs in almost every failed run.',
       '<b>Empty replies:</b> "None" replies in 26 runs; four in a row end the run as stuck.',
       '<b>Recovery is local:</b> after a malformed step the next action is valid about half the time, but the same '
       'error returns later in the run. 31 runs ended stuck and 95 hit the 20-step limit.'],
      why='the model mixes the benchmark&rsquo;s text format with the native tool-calling format it was trained on, and '
          'the harness does not translate between them.')

cause('7.2 Harness behaviours that hit gpt-oss hardest',
      'Several harness details that rarely affect gemma decide many gpt-oss runs:',
      ['<b>List-form shell commands:</b> carried over from container.exec, gpt-oss often sends commands as lists. The '
       'harness joins them with spaces, so <font face="Courier">bash -lc ls -R /testbed/data</font> runs plain ls in "/". '
       'The model sees the root folder instead of the data folder and concludes the data is missing (3-35/0: '
       '"/testbed/data might not exist"; 3-63/0 and 3-77/0 never find it). In 2-34/0 and 3-8/3 the computed value was '
       'correct but <font face="Courier">echo</font> wrote an empty file for the same reason.',
       '<b>The llm app returns nothing:</b> it calls gpt-oss itself with a 50-token limit, which gpt-oss spends on hidden '
       'reasoning, so almost every call returns an empty string. The agent then waits ("I need to wait for the llm&rsquo;s '
       'response") or re-asks (3-7/0 sent the same prompt 8 times; 3-42/0 10 times). About 13 of the 18 three-app '
       '"empty result" failures are this. It even used the llm app to ask the user for missing data (3-52/0).',
       '<b>Apostrophes break the llm app:</b> llm_query.py passes the prompt as <font face="Courier">--prompt '
       '&#39;&#39;&#39;...&#39;&#39;&#39;</font>, so a prompt containing "Bob&#39;s" fails with a shell error (3-90/0).',
       '<b>Every here-document prints a warning:</b> the <font face="Courier">bash -c &quot;&quot;&quot; ... '
       '&quot;&quot;&quot;</font> wrapper leaves a space after the closing marker, so bash warns "here-document '
       'delimited by end-of-file" even though the file is written. gpt-oss reads this as failure and rewrites the file; '
       'in 3-44/0 the rewrite destroyed correct content.',
       '<b>Finishing through the tool-call channel:</b> finish_task calls that arrive as native tool calls carry no '
       'reasoning; most premature finishes are a bare finish right after a listing or an invalid call (e.g. 3-15/0, '
       '3-46/0, 3-66/0).'])

cause('7.3 Other gpt-oss failure patterns',
      'Beyond format and harness issues, gpt-oss fails in the same ways as gemma, plus a few of its own:',
      ['<b>Wrong content (35):</b> OCR errors copied (2-10/0, 2-45/1 "nesting", "ton"), half swaps (1-14/0 swapped the '
       'scores but not the names), one email to several comma-separated addresses (2-38/2), incomplete lists (3-45/0 '
       'left out one of six people), paraphrasing a literal (3-56/0 "Read the assigned book and write an essay").',
       '<b>Avoiding apps (task read differently):</b> it wrote calendar and email files with the shell instead of using '
       'the calendar and email apps (3-48/0, 3-54/0, 3-96/0; 3-61/0 even base64-encoded a document into a hand-built '
       'email). These files are never "sent", so the checks fail.',
       '<b>Out of steps (17):</b> the same cell-by-cell writing as gemma on three-app tasks (3-29/0, 3-37/0 to 3-41/0, '
       '3-99/0, 3-100/0).',
       '<b>Inventing data after an empty result:</b> 3-50/0 created a made-up "Team Sync" event; 3-73/0 wrote a fake '
       'image file as text, which passes "file exists".',
       '<b>Deliberation loops:</b> responses that repeat a sentence until the length limit (3-12/0: "We can try to list '
       '/usr/lib/python3.9? But not." 64 times; 3-2/0 one sentence 103 times).',
       '<b>What it does better:</b> it reads back what it wrote more often (18 of 126 writing runs vs about 2% for '
       'gemma).'])

# ====================================================================== 8 gpt-oss Bangla
p('8. gpt-oss:20b in Bangla: the first 51 subtasks', H2)
p('The gpt-oss Bangla run had completed 51 single-app subtasks (1-1/0 to 1-10/4) when this report was written. It '
  'uses the same harness code as the gpt-oss English run. Paired with English on the same subtasks:')
table([
    ['', 'Bangla passes', 'Bangla fails'],
    ['English passes', '20', '3 (1-1/4, 1-2/3, 1-6/4)'],
    ['English fails', '10', '18'],
], [50*mm, 50*mm, 78*mm])
story.append(Spacer(1, 4))
p('Bangla passes 30 against 23 for English. With 10 subtasks favouring Bangla and 3 favouring English, the '
  'difference is not statistically significant (two-sided sign test, p about 0.09), and one Bangla pass (1-2/4) is a '
  'keyword accident.')
cause('8.1 The Bangla prompt removed most format failures',
      'On the same 51 subtasks, the habits that sink gpt-oss in English almost disappeared in Bangla:',
      ['Invented native-tool calls: 97 steps in 27 runs in English, 9 steps in 8 runs in Bangla (container.exec 87 to 1).',
       '<font face="Courier">bash -lc</font> list commands: 144 steps to 4; empty replies: 21 to 0; runs ended stuck: '
       '3 to 0; malformed steps: 38.6% to 16.1% of steps.',
       'The nested "##Thought" slip barely changed (63 to 48 steps), so the effect is specific to the native-tool habit.',
       '6 of the 10 Bangla-only passes are subtasks English lost to format or tool-call failures (e.g. 1-4/0, 1-4/1, '
       '1-5/0, 1-6/0, 1-9/3, 1-10/0).'],
      why='not established. The Bangla prompt may move the model away from its English tool-use habits; server state '
          'and run-to-run variation cannot be ruled out with one run each.')
cause('8.2 Why the Bangla run still fails (21 failures)',
      'Most Bangla failures are not caused by the language:',
      ['<b>Shared with English (10):</b> benchmark defects (1-2/0, 1-5/1, 1-8/2, 1-10/4) and the same task readings and '
       'content errors (1-4/2 merging the bonus, 1-5/2, 1-8/1, 1-2/1, 1-2/2, 1-4/3).',
       '<b>Premature finish (5):</b> unfinished multi-cell writes (1-6/3, 1-6/4, 1-6/5) and giving up without reading the '
       'calendar (1-2/3: "there is no information about their wake-up times").',
       '<b>Task read differently (5),</b> e.g. 1-9/0 averaged per student instead of a bottom row.',
       '<b>Language-related (3):</b> "travelling" became the event "Trip to Florida" (1-1/4) and "8:00" became "08:00" '
       '(1-6/2), the same slips gemma made; "duplicate the line at bottom" was translated as "duplicate the line '
       'below" (1-9/1).'])
cause('8.3 How gpt-oss differs from gemma in Bangla',
      'gpt-oss does not show gemma&rsquo;s main Bangla failure, the output boundary:',
      ['It wrote no answers in Bangla script (0 of 8 free-text answers) and no Bangla into tool arguments.',
       'Names given only in Bangla script were always written "Bob" and "Tom" with the right case (9 subtasks).',
       'Its reasoning stays in English: only 1.9% of the letters in its reasoning are Bangla, mostly short plans at the '
       'first steps and quotes of the task.',
       'So for gpt-oss the Bangla prompt changes how it acts (fewer format failures) rather than what it writes.'])

# ====================================================================== 8 pilots
p('9. The pilot runs: no written reasoning, and Qwen2.5-7B', H2)
p('Before the main runs, gemma4:31b was run on 91 subtasks (mostly single-app) with the original OfficeBench prompt, '
  'which asks for the JSON action only, with no written reasoning.')
bullets([
    '<b>Reasoning barely helps on simple tasks:</b> on the 87 subtasks run both ways, the no-reasoning pilot passed 58 '
    'and the reasoning run 60. Each wins a few the other loses (pilot only: 1-19/1, 1-20/0, 1-8/0, 2-39/0; reasoning '
    'only: 1-14/4, 1-19/2, 1-20/2, 1-20/4, 1-6/2, 1-9/1).',
    '<b>The pilots fail in the same ways:</b> the same benchmark defects (1-5/1, 1-6/0, 1-6/3), the same task readings '
    '(1-4/2 merging the bonus, 1-5/2 ignoring "for each day"), and few malformed actions (19 steps).',
    '<b>Qwen2.5-7B</b> (12 subtasks): 3 passed. In 7 of the 9 failures it produced malformed actions until the harness '
    'declared it stuck, usually after four in a row. At this size the action format itself is the main obstacle.',
])

# ====================================================================== 9 synthesis
story.append(PageBreak())
p('10. Across all runs: what fails everywhere and what is model-specific', H2)
table([
    ['', 'gemma4:31b English', 'gemma4:31b Bangla', 'gpt-oss:20b English'],
    ['Pass rate', '151 / 300 (50.3%)', '127 / 300 (42.3%)', '86 / 300 (28.7%)'],
    ['Three-app pass', '28 / 112', '28 / 112', '8 / 112'],
    ['Largest cause of failure', 'Benchmark defects (47)', 'Benchmark defects (39)', 'Action format (54)'],
    ['Runs with a malformed step', '69', '30', '282'],
    ['Malformed steps', '273', '194', '1,671'],
    ['Runs ended stuck', '3', '5', '31'],
    ['Runs hitting 20 steps', '52', '44', '95'],
    ['Read back what it wrote', '3 / 203', '4 / 197', '18 / 126'],
    ['llm app: runs / calls', '53 / 237', '51 / 168', '24 / 111 (mostly empty replies)'],
    ['Empty placeholder images created', '5', '0', '3'],
    ['Share of steps spent switching apps', '26%', '30%', '17%'],
], [52*mm, 42*mm, 42*mm, 42*mm])
story.append(Spacer(1, 6))

cause('10.1 What fails everywhere',
      'Of the 300 subtasks, 119 fail in all three full runs and 55 pass in all three. 44 fail for the identical cause '
      'in all three runs: benchmark defect 14, wrong content 13, out of steps 8, task read differently 3, empty result '
      '3, cut-off loop 2, premature finish 1. These are the failures no model or language change fixes:',
      ['<b>Benchmark defects:</b> 57 subtasks have a defect that decides at least one run.',
       '<b>One cell per action:</b> three-app tasks that require building a spreadsheet run out of steps for every '
       'model.',
       '<b>OCR noise:</b> all models copy OCR misreads into outputs without correction.',
       '<b>Empty listings:</b> all models sometimes query a mailbox in the wrong case or the wrong user and conclude '
       'nothing exists.',
       '<b>No checking:</b> no model reliably reads back its output before finishing.'])

cause('10.2 What is model- or language-specific',
      'Each configuration adds its own failure layer on top of the shared core:',
      ['<b>gemma4:31b English:</b> long reasoning that pushes commands past the 512-token limit (cut-off loops), and '
       'placeholder files that game existence checks.',
       '<b>gemma4:31b Bangla:</b> the output boundary (answers in Bangla, names in the wrong case, words changed), '
       'translation errors, and treating output files as existing inputs. It has fewer cut-off loops than English.',
       '<b>gpt-oss:20b English:</b> the action format (its own tool schema, empty replies, nested thoughts), harness '
       'interactions (list-form commands, empty llm-app replies, apostrophes, here-document warnings), premature '
       'finishes through native tool calls, and doing email and calendar work with the shell.',
       '<b>gpt-oss:20b Bangla (partial):</b> far fewer format failures than in English; otherwise the shared failures.',
       '<b>Qwen2.5-7B:</b> the action format, in a more basic form.'])

# ====================================================================== 10 defects
p('11. Benchmark and harness defects (catalogue)', H2)
p('All verified against the code or reference files. Defects that decided at least one run in this analysis:')
table([
    ['Where', 'Defect', 'Subtasks affected'],
    ['apps/email_app/email_list_emails.py; utils/evaluate.py', 'Email check reads a hard-coded /testbed path; fallback loop raises NameError (scoring only)', 'every email check'],
    ['utils/evaluate.py (email)', 'Mailbox matched by substring before exact name', '3-12/0'],
    ['apps/excel_app/excel_set_cell.py:36', '<font face="Courier">if text == True</font> erases the value 1', '1-5/1, 1-6/0, 3-95/0'],
    ['apps/calendar_app/calendar_create_event.py', 'Times written without "Z"; checks require it', '3-20, 3-24, 3-28, 3-73, 3-74'],
    ['apps/word_app/word_convert_to_pdf.py (Linux)', 'LibreOffice --outdir keeps the source name; requested name ignored', '3-4, 3-67, 3-86, 3-25, 2-39/2, 2-1/1'],
    ['utils/env.py clean_cmd', 'Commands wrapped in bash -c """..."""; double quotes break them', '2-33, 2-36/3, 3-44, 3-72, 3-89, 2-12'],
    ['utils/env.py exec_action (line 126)', 'List-form shell commands joined with spaces; quoting lost', 'many gpt-oss runs; 2-34/0, 3-8/3'],
    ['apps/llm_app/llm_query.py', 'llm app limited to 50 tokens and calls the agent&rsquo;s own model; reasoning models return nothing', 'most gpt-oss llm calls'],
    ['apps/llm_app/llm_query.py:81', 'Prompt passed as --prompt &#39;&#39;&#39;...&#39;&#39;&#39;; an apostrophe in the prompt breaks the command', '3-90/0'],
    ['utils/env.py clean_cmd (here-documents)', 'Space after the closing marker makes bash warn on every here-document; the file is written but looks failed', '3-43, 3-44, 3-61, 3-96'],
    ['Task data', '3-98: the source email is outside any mailbox; 3-75: task says rename a PDF but only a .docx exists', '3-98/0, 3-75/0'],
    ['apps/email_app (send_email)', 'Comma-separated recipients accepted but stored for the first only; sender keeps a copy', '2-45/0, 2-38/2, 3-8/6'],
    ['utils/evaluate.py (pdf exact match)', 'Compares page objects; can never pass', '3-62/0'],
    ['Task checks: wrong file or value', 'Check reads another file or expects a wrong value', '1-6/3, 1-9/0, 1-14/2 (salery.xlsx), 1-14/3, 2-26/3, 3-99 (revenuse.docx), 3-82, 3-80, 3-8/5, 3-58, 3-1 ("Activaty"), 2-2/0 and 2-2/1 (swapped), 2-48/0'],
    ['Task checks: ask for more than the task', 'Check requires outputs the task never mentions', '1-2/0, 1-2/2, 1-3/4, 1-8/0, 1-8/2, 1-8/4, 2-14, 2-45/2, 2-39/3, 3-43, 3-13/1'],
    ['Debatable checks', 'Depend on one reading of ambiguous wording or format', '1-6/4, 1-10/4, 3-22, 3-30, 3-49, 3-76, 3-70'],
    ['Weak checks', 'Substring and existence checks pass wrong or empty outputs', '1-2/4, 1-11/3, 3-55/0 (empty image passes)'],
], [52*mm, 72*mm, 54*mm], style=TINY)

# ====================================================================== 11 recommendations
p('12. What to fix, and what to test next', H2)
p('Benchmark and harness fixes (change the score of a correct agent)', H3)
bullets([
    'Fix the email evaluator path and exact-name mailbox matching; fix <font face="Courier">text is True</font> in '
    'excel_set_cell; write "Z" times or relax the checks; rename the converted PDF to the requested name.',
    'Pass shell commands to bash without the triple-quote wrapper, and join list-form commands with proper quoting '
    '(<font face="Courier">shlex.join</font>).',
    'Fix the wrong reference files and checks listed in Section 11; report ambiguous ones separately.',
    'Give the llm app a non-reasoning model or a larger token limit, report empty replies as errors, and pass the '
    'prompt without shell quoting.',
])
p('Agent and harness changes worth testing', H3)
bullets([
    'Carry the previous thought (or a short notes field) into the next prompt, so values are not recomputed.',
    'Add a bulk write action for Excel, or tell the agent it may use one shell command for bulk work, and tell it the '
    'step budget.',
    'Add a verification rule: read the output back before finish_task.',
    'For reasoning models such as gpt-oss: translate native tool calls into benchmark actions, or disable native tools.',
    'For the Bangla condition: require English answers, keep names, file names and keywords in Latin script, and have '
    'the translations checked by a Bangla speaker. Finish the gpt-oss Bangla run and repeat both gpt-oss runs to test '
    'whether the drop in format failures is real.',
    'Repeat the runs that pass in only one configuration at least once more, to separate real effects from chance.',
])

# ====================================================================== appendix A
story.append(PageBreak())
p('Appendix A. Agent behaviour statistics by run', H2)
table([
    ['Measure', 'gemma EN', 'gemma BN', 'gpt-oss EN', 'gpt-oss BN (51)', 'gemma pilots', 'Qwen2.5-7B'],
    ['Runs analysed', '299', '299', '299', '51', '91', '12'],
    ['Passed', '151', '127', '86', '30', '61', '3'],
    ['Total steps', '3,257', '3,145', '3,982', '459', '701', '95'],
    ['Malformed steps', '273', '194', '1,671', '74', '20', '40'],
    ['Runs with a malformed step', '69', '30', '282', '38', '9', '8'],
    ['Runs with empty model replies', '1', '2', '26', '0', '2', '1'],
    ['Runs ended stuck', '3', '5', '31', '0', '2', '7'],
    ['Runs hitting 20 steps', '52', '44', '95', '2', '4', '1'],
    ['Runs that called finish_task', '248', '254', '182', '49', '85', '4'],
    ['Reasoning characters per step', '367', '319', '394', '268', 'n/a', 'n/a'],
], [50*mm, 19*mm, 19*mm, 21*mm, 24*mm, 22*mm, 23*mm])
p('One run per subtask and configuration; "runs analysed" excludes runs with no history (one crashed run in each '
  'full run). The gemma pilots wrote no reasoning.', SMALL)

# ====================================================================== appendix B
story.append(PageBreak())
p('Appendix B. Root cause of every failed subtask, all four runs', H2)
p('Codes as in Section 4. "pass" = passed; "-" = not yet run (gpt-oss Bangla covers 1-1/0 to 1-10/4 only). Only '
  'subtasks failing in at least one run are listed.', SMALL)
P, C = CODES['pass'], CODES['cat']


def key(i):
    t, s = i.split('/')
    return tuple(int(x) for x in t.split('-')) + (int(s),)


ids = sorted({i for k in ('EN', 'BN', 'GO', 'GB') for i, ok in P[k].items() if not ok}, key=key)


def val(k, i):
    if i not in P[k]:
        return '-'
    return 'pass' if P[k][i] else C[k].get(i, '?')


rows = [['Subtask', 'gemma EN', 'gemma BN', 'gpt-oss EN', 'gpt-oss BN'] * 2]
half = (len(ids) + 1) // 2
left, right = ids[:half], ids[half:]
for j in range(half):
    r = [left[j]] + [val(k, left[j]) for k in ('EN', 'BN', 'GO', 'GB')]
    if j < len(right):
        r += [right[j]] + [val(k, right[j]) for k in ('EN', 'BN', 'GO', 'GB')]
    else:
        r += [''] * 5
    rows.append(r)
table(rows, [16*mm, 17*mm, 17*mm, 19*mm, 19*mm] * 2, style=TINY)


def footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16*mm, 9*mm, 'Why the agents fail on OfficeBench - all runs to 2026-10-04')
    canvas.drawRightString(A4[0] - 16*mm, 9*mm, f'page {doc_.page}')
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=16*mm, rightMargin=16*mm,
                        title='Why the agents fail on OfficeBench', author='analysis')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB', len(ids), 'failed subtasks in appendix')
