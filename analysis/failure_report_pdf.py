"""Detailed "why the tasks fail" report for the gemma4:31b OfficeBench run (think tag).

The per-task diagnoses below were made by hand from each run's env_history.json,
llm_history.json (the ##Thought text), the final testbed files, the reference files and
the check code in utils/evaluate.py. Codes follow analysis/codebook.md.

    python analysis/failure_report_pdf.py [out.pdf]
"""
import os, sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether, PageBreak)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'analysis', 'OfficeBench_gemma4-31b_failure_analysis.pdf')

INK = colors.HexColor('#18202c')
MUTED = colors.HexColor('#5a6476')
ACCENT = colors.HexColor('#2d5a9b')
LINE = colors.HexColor('#dce1e8')
BAND = colors.HexColor('#eef1f5')
BENCH = colors.HexColor('#fbeee6')
AGENT = colors.HexColor('#e6eefb')
BOTH = colors.HexColor('#f1e8f7')
BOX = colors.HexColor('#f6f7f9')

SCORED, PASSED = 73, 52
FAILED = SCORED - PASSED

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], textColor=INK, fontSize=20, leading=24, spaceAfter=2, alignment=0)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], textColor=MUTED, fontSize=9.5, leading=13)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=INK, fontSize=14, leading=18, spaceBefore=14, spaceAfter=5)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], textColor=ACCENT, fontSize=11, leading=14, spaceBefore=10, spaceAfter=3)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], textColor=INK, fontSize=9.8, leading=14.2, spaceAfter=4)
BUL = ParagraphStyle('BUL', parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=2)
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], textColor=MUTED, fontSize=8.3, leading=11)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], textColor=INK, fontSize=8.2, leading=10.6)
CELLB = ParagraphStyle('CELLB', parent=CELL, fontName='Helvetica-Bold')
HEAD = ParagraphStyle('HEAD', parent=CELLB, textColor=colors.white)
MONO = ParagraphStyle('MONO', parent=styles['Code'], textColor=INK, fontSize=8, leading=10.5,
                      backColor=BOX, borderPadding=(4, 5, 4, 5), spaceBefore=3, spaceAfter=6)
QUOTE = ParagraphStyle('QUOTE', parent=BODY, textColor=MUTED, fontName='Helvetica-Oblique', leftIndent=12,
                       fontSize=9.2, leading=13)

story = []


def p(txt, st=BODY):
    story.append(Paragraph(txt, st))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText='•'))


def code(txt):
    story.append(Paragraph(txt.replace('&', '&amp;').replace('<', '&lt;').replace('\n', '<br/>')
                           .replace('  ', '&nbsp;&nbsp;'), MONO))


def rule():
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width='100%', thickness=0.6, color=LINE))
    story.append(Spacer(1, 3))


def table(rows, widths, header_bg=ACCENT, row_bgs=None, bold_first_col=False):
    data = [[Paragraph(str(c), HEAD) for c in rows[0]]]
    for r in rows[1:]:
        data.append([Paragraph(str(c), CELLB if (bold_first_col and j == 0) else CELL)
                     for j, c in enumerate(r)])
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    for i, bg in (row_bgs or {}).items():
        cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle(cmds))
    story.append(t)


# ------------------------------------------------------------------ title
p('Why the tasks fail', H1)
p('OfficeBench &middot; gemma4:31b (Ollama, Thought-then-Command prompt, run tag <i>think</i>) '
  f'&middot; snapshot 2026-10-02 &middot; {SCORED} of 300 subtasks scored, all single-app', SUB)
rule()

# ------------------------------------------------------------------ summary
p('Summary', H2)
p(f'Of the {SCORED} subtasks scored so far, <b>{PASSED} pass and {FAILED} fail ({100*PASSED/SCORED:.1f}% pass)</b>. '
  'I read every failed run step by step (the model&rsquo;s thought, the action, the observation), compared the '
  'final files with the task text and the reference files, and re-ran each check. The main finding is that '
  '<b>most failures are not the model&rsquo;s fault</b>:')
bullets([
    '<b>10 failures are on the benchmark side.</b> The agent did what the task says, but a tool bug, a check that '
    'asks for something the task never mentions, or a formatting rule marked it wrong.',
    '<b>4 failures have a broken check <i>and</i> an agent error.</b> The agent made a mistake, but the check is '
    'also broken (a misspelled reference file, a wrong reference, a wrong expected number), so a perfect agent '
    'would still fail.',
    '<b>Only 7 failures are clean agent errors</b>, where the benchmark is sound and the model got it wrong.',
    f'In total, <b>at least 8 of the {SCORED} scored subtasks cannot be passed by an agent that does exactly what '
    'the task says</b> (1-3/4, 1-5/1, 1-6/0, 1-6/3, 1-8/0, 1-9/0, 1-14/2, 1-14/3).',
    'The agent&rsquo;s own errors fall into a few patterns: it does a different operation from the one asked '
    '(merging into an existing row, swapping only the labels, averaging the wrong thing), it ignores a conflict '
    'it noticed, it re-does arithmetic at the next step and gets it wrong, and it runs out of the 20-step budget '
    'because the Excel app writes only one cell per action.',
])
p('<b>Note on the dashboard count.</b> The dashboard shows 22 failures. The extra one, 1-16/0, is a false failure: the '
  'local evaluator reads the task JSON with the Windows default encoding (cp1252), so the expected keyword '
  '&ldquo;caf&eacute;&rdquo; becomes &ldquo;caf&Atilde;&copy;&rdquo; and never matches. With UTF-8 the check passes. '
  'This report uses the UTF-8 result (52 pass / 21 fail).', SMALL)

# ------------------------------------------------------------------ where failures come from
p('Where the 21 failures come from', H2)
rows = [
    ['Side', 'Cause', 'n', 'Subtasks'],
    ['Benchmark', 'Excel tool silently erases any cell written as "1"', '2', '1-5/1, 1-6/0'],
    ['Benchmark', 'Check requires something the task does not ask for, or reads a different file', '7',
     '1-2/0, 1-2/2, 1-6/3, 1-8/0, 1-8/2, 1-8/4, 1-10/4'],
    ['Benchmark', 'Check rejects an equivalent answer on surface form (sign convention)', '1', '1-6/4'],
    ['Both', 'Agent error, and the check is broken too (task is unpassable)', '4', '1-3/4, 1-9/0, 1-14/2, 1-14/3'],
    ['Agent', 'Wrong operation / misread goal', '3', '1-4/2, 1-5/2, 1-8/1 (+1-9/0, 1-14/2, 1-14/3 above)'],
    ['Agent', 'Changed a label the task states literally', '1', '1-4/3'],
    ['Agent', 'Ignored a conflict it had observed', '1', '1-2/1'],
    ['Agent', 'Arithmetic: correct value found, then recomputed wrongly', '1', '1-5/3'],
    ['Agent', 'Ran out of the 20-step budget (cell-by-cell writing)', '1', '1-11/1'],
]
bg = {i: (BENCH if r[0] == 'Benchmark' else BOTH if r[0] == 'Both' else AGENT) for i, r in enumerate(rows) if i}
table(rows, [20*mm, 85*mm, 8*mm, 65*mm], row_bgs=bg)
story.append(Spacer(1, 4))
p('Five of the seven &ldquo;check requires something else&rdquo; cases (1-2/0, 1-2/2, 1-8/2, 1-8/4, 1-10/4) depend on '
  'how the task wording is read; the reading the check uses is defensible but not the only one. The other two '
  '(1-6/3, 1-8/0) are plain check errors.', SMALL)

p('What this does to the score', H3)
table([
    ['How the 21 failures are counted', 'Pass rate on the 73 scored'],
    ['As scored by the benchmark', f'{PASSED}/73 = {100*PASSED/73:.1f}%'],
    ['Credit the agent for the 5 clear benchmark defects (1-5/1, 1-6/0, 1-6/3, 1-6/4, 1-8/0)',
     f'{PASSED+5}/73 = {100*(PASSED+5)/73:.1f}%'],
    ['Credit the agent for all 10 benchmark-side failures (adds the 5 wording-dependent cases)',
     f'{PASSED+10}/73 = {100*(PASSED+10)/73:.1f}%'],
], [125*mm, 53*mm])
story.append(Spacer(1, 4))
p('So the benchmark&rsquo;s own defects cost this run roughly 7 to 14 percentage points on the tasks scored so far. '
  'These are all single-app tasks; two- and three-app tasks have not started, so these numbers should not be '
  'compared with the paper&rsquo;s overall leaderboard yet.', BODY)

# ------------------------------------------------------------------ benchmark side
p('Part 1 &mdash; Failures caused by the benchmark', H2)
p('In these cases the agent&rsquo;s final files (or its answer) match what the task asks. The run is scored as a '
  'failure because of the tool or the check.')

p('B1. The Excel tool erases the value 1 (1-5/1, 1-6/0)', H3)
p('<b>What happened.</b> In 1-5/1 (&ldquo;reduce half amount of apple&rdquo;), the agent read apple = 2, wrote '
  '<b>1</b> to cell (2,2), and the tool replied &ldquo;Successfully write text&rdquo;. The saved file has that cell '
  '<b>empty</b>. In 1-6/0 (&ldquo;randomly assign each student to class 1 to 5&rdquo;) the agent wrote 3, 1, 5, 2, 4. '
  'Every value was saved except the 1, so Carol&rsquo;s class is blank and the check fails.')
p('<b>Why.</b> The action runs as a shell command, and the <i>fire</i> library turns the argument "1" into the '
  'integer 1. The first line of the tool then treats it as a boolean:')
code('# apps/excel_app/excel_set_cell.py, line 36\n'
     'def excel_set_cell(file_path, text, row_idx, column_idx, sheet_name=None):\n'
     '    if text == True:     # 1 == True in Python, so the value 1 becomes ""\n'
     '        text = \'\'')
p('<b>Effect.</b> No agent can store the number 1 with <i>set_cell</i>, and the tool reports success, so the agent '
  'has no signal that anything went wrong. The same bug was present in the earlier no-thinking runs. The agent '
  'could have caught it by reading the file back after writing (it never did in these two runs). '
  '<b>Fix:</b> change the test to <font face="Courier">text is True</font>.')

p('B2. The check requires something the task does not ask for (7 subtasks)', H3)
p('<b>1-2/0 and 1-2/2 &mdash; &ldquo;find a time&rdquo; is checked as &ldquo;add an event&rdquo;.</b> The tasks say '
  '&ldquo;Find a common time for Bob and Tom to have a one hour zoom meeting&rdquo; and &ldquo;help them find one '
  'hour&rdquo; for shopping. The agent listed both calendars, worked out that Bob is free 14:00&ndash;16:00 and Tom '
  'is free 14:30&ndash;16:00, and answered <b>14:30&ndash;15:30</b>, which is correct. The checks require an event '
  'containing &ldquo;meeting&rdquo; / &ldquo;shopping&rdquo; in both .ics files, which the task never asks for. '
  '(The sister task 1-2/1 says &ldquo;Add a common time on their calendar&rdquo; explicitly, which suggests the '
  'authors meant this but left it out of 1-2/0 and 1-2/2.)')
p('<b>1-6/3 &mdash; the check reads the wrong file.</b> The task says &ldquo;show this in <i>salary</i> excel file '
  'with new header &lsquo;amount after 1 year&rsquo;&rdquo;. The agent wrote the header and 210000 / 110000 / '
  '110000 into salary.xlsx (base +5%, stock +10%, bonus +10%), all correct. Both checks open '
  '<i>company_budget.xlsx</i> and expect 2,100,000 / 55,000 / 1,100.')
p('<b>1-8/0 &mdash; the reference deletes the student names.</b> Task: &ldquo;delete all students&rsquo; score and '
  'the header&rdquo;. The agent cleared the header row and every score and kept the names. The check compares the '
  'file cell by cell with <i>reference/score.xlsx</i>, which is completely empty; the only differences are the '
  'names Liam, Ivy, Alice. Note that the sister task 1-8/1 (&ldquo;remove all students&rsquo; class and the '
  'header&rdquo;) has a reference that <i>keeps</i> both the names and the &ldquo;Name&rdquo; header, so the two '
  'references read &ldquo;the header&rdquo; in opposite ways.')
p('<b>1-8/2 and 1-8/4 &mdash; &ldquo;delete all amounts&rdquo; is checked as &ldquo;delete the amount '
  'column&rdquo;.</b> The agent cleared the three amounts and kept the column header &ldquo;amount&rdquo;. The '
  'reference also removes the header, so the single difference is cell (1,2) = &ldquo;amount&rdquo;. A header is '
  'not an amount, so the agent&rsquo;s reading is at least as reasonable as the check&rsquo;s.')
p('<b>1-10/4 &mdash; question asks for an amount, check wants a name.</b> &ldquo;What is the fewest amount of bought '
  'item in shopping list excel file?&rdquo; The agent read apple 2, cabbage 3, onion 4 and answered <b>2</b>. The '
  'check looks for the word &ldquo;apple&rdquo;. Read literally, the question asks for the amount. An answer such '
  'as &ldquo;apple (2)&rdquo; would have satisfied both readings, so the agent could have hedged better here.')

p('B3. A correct answer rejected on form (1-6/4)', H3)
p('Task: add a header &lsquo;Increase Percentage Per Year&rsquo;, &ldquo;increase base salaries by 5%/yr, '
  '<b>reduce</b> computer expenses 10%/yr, and increase entertainment expenses 10%/yr&rdquo;. The agent wrote '
  '<b>5%</b>, <b>-10%</b>, <b>10%</b>. The check expects 5, 10, 10. Because the cell checks are substring matches '
  '(see B5), the % sign is fine: &ldquo;(2, 3): 5&rdquo; is found inside &ldquo;(2, 3): 5%&rdquo;. The run fails '
  '<b>only because of the minus sign</b> on the computer row, which is the correct way to write a reduction '
  'under a header called &ldquo;Increase Percentage&rdquo;.')

p('B4. Checks that no correct answer can pass', H3)
p('Four further subtasks also involve an agent mistake (Part 2), but the check is broken as well, so they would '
  'fail even for a perfect agent:')
bullets([
    '<b>1-14/2</b> &mdash; the check points to <font face="Courier">reference/salery.xlsx</font> (misspelled). The '
    'file does not exist, so the check crashes with FileNotFoundError on every run.',
    '<b>1-14/3</b> &mdash; &ldquo;swap the <i>fewest</i> and <i>second fewest</i> shopping item&rdquo;. The '
    'reference swaps apple (2) with <i>onion (4)</i>, the fewest and the most, so a correct swap of apple and '
    'cabbage can never match.',
    '<b>1-9/0</b> &mdash; the expected midterm1 average is &ldquo;80.5&rdquo;, but the true mean of the 20 scores '
    'is <b>80.05</b>. Since &ldquo;(22, 2): 80.5&rdquo; is not a substring of &ldquo;(22, 2): 80.05&rdquo;, the '
    'correct value fails.',
    '<b>1-3/4</b> &mdash; &ldquo;move all docx, pdf, and image files&rdquo;, but one check also requires '
    '<font face="Courier">file3.xlsx</font> to be in new_dir. Moving the spreadsheet would break the instruction; '
    'not moving it fails the check.',
])

p('B5. How the checks work (why form and wording matter so much)', H3)
p('Most Excel checks (<font face="Courier">evaluate_excel_cell_value</font>) render the sheet as text and test '
  'whether the literal string <font face="Courier">"(row, col): value"</font> appears anywhere in it. This has '
  'three consequences: (1) the answer must sit in exactly the expected cell; (2) form matters in odd ways: '
  '&ldquo;08:00&rdquo; fails against &ldquo;8:00&rdquo;, &ldquo;-10%&rdquo; fails against &ldquo;10&rdquo;, but '
  '&ldquo;10%&rdquo; passes; (3) some wrong answers pass, e.g. &ldquo;80.55&rdquo; would match &ldquo;80.5&rdquo;. '
  'Answer checks (<font face="Courier">evaluate_contain</font>) only look for a keyword anywhere in answer.txt. '
  'The &ldquo;exact match&rdquo; checks compare every cell with a reference file, so any disagreement over what '
  'to keep (names, headers) is fatal.')

# ------------------------------------------------------------------ agent side
p('Part 2 &mdash; Failures caused by the agent', H2)
p('These 11 runs (7 agent-only plus the 4 from B4) contain a real model error. For each one the decisive step '
  'is the earliest step that, if corrected alone, would have made the output right.')

p('A1. Doing a different operation from the one asked (6 subtasks)', H3)
p('This is the largest agent-side group. The model reads the data correctly and does valid arithmetic, but on '
  'the wrong target.')
bullets([
    '<b>1-4/2 &mdash; merged instead of added.</b> &ldquo;add annual bonus $50000 to salary excel file&rdquo;. The '
    'sheet already has a row &ldquo;bonus 100000&rdquo;. The agent reasoned &ldquo;the new bonus amount should be '
    '100,000 + 50,000 = 150,000&rdquo; and overwrote that cell. Expected: a new row 5, &ldquo;annual bonus&rdquo; / '
    '50000. (The same mistake appeared in the earlier run.)',
    '<b>1-5/2 &mdash; ignored &ldquo;for each day&rdquo;.</b> &ldquo;add &lsquo;average salary&rsquo; for each day '
    '... round down&rdquo;. The agent wrote 133333, the mean of the three salary lines (base, stock, bonus), saying '
    'the phrase &ldquo;in this context seems to be the average of the amounts listed&rdquo;. Expected: total '
    '400000 / 365 = 1095.',
    '<b>1-9/0 &mdash; row averages instead of a bottom row.</b> &ldquo;calculate the average of two midterm scores, '
    'write in the bottom row ... with header &lsquo;Average&rsquo;&rdquo;. The agent added a new <i>column</i> '
    'with each student&rsquo;s average of their two scores, one cell per step, and hit the 20-step limit at row 15. '
    'Expected: row 22 = &ldquo;Average&rdquo;, mean of midterm1, mean of midterm2. (The expected value is also '
    'wrong; see B4.)',
    '<b>1-14/2 and 1-14/3 &mdash; swapped the labels, not the items.</b> Asked to swap two items, the agent '
    'rewrote only the name cells and left the amounts in place. In 1-14/3 the sheet now says cabbage = 2 and '
    'apple = 3, which changes the data instead of moving it; in 1-14/2 &ldquo;stock&rdquo; is now 200000. The '
    'reference swaps whole rows. The model did swap whole rows in the passing sister task 1-14/4, so this is '
    'inconsistent behaviour rather than a fixed belief.',
    '<b>1-8/1 &mdash; deleted one header too many.</b> &ldquo;remove all students&rsquo; class and the '
    'header&rdquo;. The agent cleared the Class column and its header, read the file back, then decided '
    '&ldquo;the header&rdquo; also meant &ldquo;Name&rdquo; and deleted it too. The reference keeps '
    '&ldquo;Name&rdquo;. The wording is ambiguous, and the sister reference for 1-8/0 reads it the other way.',
])

p('A2. Changing a literal label (1-4/3)', H3)
p('&ldquo;add utilities fee $300 to budget excel file&rdquo;. The agent correctly added a new row 5 with 300, but '
  'in its thought shortened the label: &ldquo;I should add &lsquo;utilities&rsquo; to the first column&rdquo;. The '
  'check wants the task&rsquo;s exact words, &ldquo;utilities fee&rdquo;. Same error as in the earlier run.')

p('A3. Ignoring a conflict it had seen (1-2/1)', H3)
p('&ldquo;Can Bob and Tom have dinner together at 5/1/2024? Add a common time on their calendar.&rdquo; Both '
  'calendars already contain &ldquo;dinner 18:30&ndash;19:30&rdquo;. The agent noticed this:')
p('&ldquo;Bob&rsquo;s dinner is from 18:30 to 19:30. Tom&rsquo;s dinner is also from 18:30 to 19:30 ... they '
  'already have the same time slot occupied by &lsquo;dinner&rsquo;. To be explicit and ensure it&rsquo;s a shared '
  'event, I ...&rdquo; (step 3)', QUOTE)
p('It then added a second event, &ldquo;Dinner with Tom/Bob 18:30&ndash;19:30&rdquo;, to each calendar, so the '
  'no-overlap check fails for both. Answering &ldquo;yes&rdquo; without adding anything, or booking a free slot, '
  'would have passed.')

p('A4. Correct arithmetic, then recomputed wrongly (1-5/3)', H3)
p('&ldquo;if budget grow 10% per year, add &lsquo;predicted budget&rsquo; for 3 years later&rdquo;. At step 4 the '
  'model worked it out year by year and got the right answer:')
p('&ldquo;Year 1: 2,051,000 &times; 1.1 = 2,256,100. Year 2: 2,481,710. Year 3: 2,481,710 &times; 1.1 = '
  '<b>2,729,881</b>.&rdquo; (step 4, while writing the label)', QUOTE)
p('At step 5, writing the number, it worked it out again a different way and slipped:')
p('&ldquo;2,051,000 &times; 1.331 = <b>2,730,381</b>.&rdquo; (step 5)', QUOTE)
p('It wrote 2730381. <b>The root cause is in the harness:</b> each prompt carries the history of actions and '
  'observations but <i>not</i> the model&rsquo;s earlier thoughts, so a value worked out in one step is lost and '
  'must be recomputed at the next. Every multi-step write in this run starts its thought by re-deriving the '
  'plan (&ldquo;I have already ...&rdquo;), which costs tokens and gives the model a fresh chance to make an '
  'arithmetic mistake.')

p('A5. Running out of steps (1-11/1, and 1-9/0)', H3)
p('&ldquo;split midterm1 and midterm2 scores ... into two excel files&rdquo;. The agent built both files cell by '
  'cell: create file, two headers, then name + score for each of 4 students. That is 11 actions per file plus '
  '4 actions of setup, about 26 in total, against a hard limit of 20. midterm1.xlsx came out exactly right; '
  'midterm2.xlsx had only its header and Liam when the run was cut off. The plan was correct but could not fit. '
  'Copying score.xlsx in the shell and deleting one column, or a single shell command that writes both files, '
  'would have fit. The same budget limit stopped 1-9/0 at row 15 of 21.')

p('A6. Blind shell commands (1-3/4)', H3)
p('&ldquo;move all docx, pdf, and image files to a new subdirectory named new_dir&rdquo;. The thought says '
  '&ldquo;First, I will list the files&rdquo;, but it never did. It ran <font face="Courier">mkdir -p new_dir</font> '
  'and <font face="Courier">mv *.docx *.pdf *.jpg ... new_dir/ 2&gt;/dev/null || true</font> with relative paths. '
  'The shell starts in <font face="Courier">/</font> (WORKDIR in docker/Dockerfile), not /testbed/data, so the '
  'directory was made at the root, nothing matched, and the error output was thrown away by the agent&rsquo;s own '
  '<font face="Courier">2&gt;/dev/null || true</font>. The tool reported success and the agent finished. In every '
  'other task this run used absolute /testbed/data paths, and the earlier run solved this task correctly, so '
  'this is a regression and a matter of luck rather than a capability gap.')

# ------------------------------------------------------------------ patterns
p('Part 3 &mdash; Patterns across the failures', H2)
bullets([
    '<b>The agent never checks its writes.</b> It almost never reads a file back after writing to it (only in '
    'the 1-8 delete tasks). One read after writing would have revealed the erased &ldquo;1&rdquo; in 1-5/1 and '
    '1-6/0, the empty folder in 1-3/4, and the double booking in 1-2/1.',
    '<b>Earlier thoughts are not carried forward.</b> Because the prompt keeps only actions and observations, '
    'the model re-plans at every step. This caused the arithmetic error in 1-5/3 and uses up tokens on every '
    'long task.',
    '<b>Excel actions are one cell at a time, with a 20-step budget.</b> Any task that writes more than about '
    '14 cells cannot finish with <i>set_cell</i> alone. The model does not switch to a bulk method on its own.',
    '<b>Loose reading of the instruction.</b> The model tends to choose the nearest easy operation: updating an '
    'existing row instead of adding one, averaging what is in front of it, shortening a label, renaming instead '
    'of moving. The thinking prompt did not remove this; the same errors on 1-4/2, 1-4/3 and 1-5/2 appear in '
    'the earlier no-thinking run.',
    '<b>What thinking did fix.</b> Compared with the earlier run, malformed or looping actions have almost '
    'disappeared (3 malformed steps in all 73 runs, in 1-9/0 and 1-9/1, and the agent recovered from each), and 1-6/2 now passes. The '
    'failures that remain are about meaning, not format.',
])

# ------------------------------------------------------------------ recommendations
p('Part 4 &mdash; What to fix', H2)
p('Benchmark fixes (each one changes the score of a correct agent)', H3)
table([
    ['Where', 'Problem', 'Fix', 'Affects'],
    ['apps/excel_app/excel_set_cell.py:36', '<font face="Courier">text == True</font> erases the value 1',
     '<font face="Courier">text is True</font>', '1-5/1, 1-6/0 and any task writing 1'],
    ['tasks/1-14/subtasks/2.json', 'expected_file is "salery.xlsx"', 'rename to salary.xlsx', '1-14/2'],
    ['tasks/1-14/reference/shopping_list.xlsx', 'swaps fewest with most', 'swap apple and cabbage rows', '1-14/3'],
    ['tasks/1-9/subtasks/0.json', 'expects 80.5; true mean is 80.05', 'expect 80.05', '1-9/0'],
    ['tasks/1-6/subtasks/3.json', 'checks company_budget.xlsx', 'check salary.xlsx, 210000 / 110000 / 110000', '1-6/3'],
    ['tasks/1-3/subtasks/4.json', 'requires file3.xlsx in new_dir', 'drop that check (or check it stayed)', '1-3/4'],
    ['tasks/1-8/reference/score.xlsx', 'names deleted', 'keep the Name column', '1-8/0'],
    ['tasks/1-2/subtasks/0.json, 2.json', '"find" checked as "add event"', 'add "and add it to their calendars" to the task, or check the answer', '1-2/0, 1-2/2'],
    ['history_to_trace.py evaluate()', 'reads task JSON as cp1252', "open(..., encoding='utf-8')", '1-16/0 (dashboard only)'],
], [46*mm, 44*mm, 50*mm, 38*mm])
story.append(Spacer(1, 4))
p('The wording-dependent cases (1-8/2, 1-8/4, 1-10/4, and 1-8/1 on the agent side) are better reported as '
  'ambiguous than fixed one way; if they are changed, the two 1-8 references should at least agree on what '
  '&ldquo;the header&rdquo; means.', SMALL)

p('Agent / harness changes worth testing', H3)
bullets([
    '<b>Carry the last thought (or a short &ldquo;notes&rdquo; field) into the next prompt</b>, so computed values '
    'and plans survive between steps. Targets 1-5/3 and reduces re-planning on every long task.',
    '<b>Add a verify rule to the prompt:</b> after writing, read the file back before finish_task. Targets '
    '1-5/1, 1-6/0, 1-3/4, 1-2/1.',
    '<b>Tell the agent about bulk options</b> (copy a file in the shell, or one shell command that writes many '
    'cells) and that the step budget is 20. Targets 1-11/1, 1-9/0.',
    '<b>Prompt rules for literal reading:</b> use labels exactly as written in the task; &ldquo;add X&rdquo; means a '
    'new row; a swap moves whole rows; for a question, give both the item and the value. Targets 1-4/2, 1-4/3, '
    '1-14/2, 1-14/3, 1-10/4.',
    '<b>Use absolute paths in the shell and never silence errors</b> with <font face="Courier">2&gt;/dev/null || '
    'true</font>. Targets 1-3/4.',
])

# ------------------------------------------------------------------ appendix
story.append(PageBreak())
p('Appendix &mdash; all 21 failures', H2)
p('Code = primary code from analysis/codebook.md. Side: B = benchmark, A = agent, A+B = agent error on a broken '
  'check. &ldquo;(ambig.)&rdquo; marks a task whose wording supports more than one reading.', SMALL)
story.append(Spacer(1, 3))
APP = [
    ['ID', 'Task (short)', 'What the agent did', 'What the check wanted', 'Code', 'Side'],
    ['1-2/0', 'Find a common 1-hour zoom slot for Bob and Tom', 'Answered 14:30-15:30 (correct); added no event',
     '"meeting" event in both calendars', 'EVAL-MISMATCH (ambig.)', 'B'],
    ['1-2/1', 'Can they have dinner together? Add a common time', 'Saw both already have dinner 18:30-19:30; added another at the same time',
     'No overlapping events', 'A-STATE', 'A'],
    ['1-2/2', 'Help Bob and Tom find one hour to shop', 'Answered 14:30-15:30 (correct); added no event',
     '"shopping" event in both calendars', 'EVAL-MISMATCH (ambig.)', 'B'],
    ['1-3/4', 'Move docx, pdf, image files to new_dir', 'Relative-path mkdir/mv in "/" with errors hidden; nothing moved',
     'docx, pdf, jpg <i>and xlsx</i> in new_dir', 'A-REASON + broken check', 'A+B'],
    ['1-4/2', 'Add annual bonus $50000', 'Overwrote bonus 100000 to 150000', 'New row "annual bonus" / 50000', 'A-INTENT', 'A'],
    ['1-4/3', 'Add utilities fee $300', 'New row "utilities" / 300', '"utilities fee" / 300', 'A-DEVIATION', 'A'],
    ['1-5/1', 'Halve the apples', 'Wrote 1; tool saved an empty cell', '(2,2) = 1', 'ENV-TOOL', 'B'],
    ['1-5/2', 'Average salary for each day, round down', '133333 (mean of 3 rows)', '1095 (400000 / 365)', 'A-INTENT', 'A'],
    ['1-5/3', 'Budget after 3 years at 10%', 'Found 2729881, then rewrote it as 2730381', '2729881', 'A-REASON', 'A'],
    ['1-6/0', 'Add Class header, random class 1-5', 'Wrote 3,1,5,2,4; the 1 was erased', 'Each row in 1-5', 'ENV-TOOL', 'B'],
    ['1-6/3', 'Raises shown in salary file', 'Correct values in salary.xlsx', 'Values in company_budget.xlsx', 'EVAL-MISMATCH', 'B'],
    ['1-6/4', 'Increase % per year header', '5%, -10%, 10%', '5, 10, 10 (minus sign rejected)', 'EVAL-FORM', 'B'],
    ['1-8/0', 'Delete scores and the header', 'Cleared header row and scores; kept names', 'Empty sheet (names deleted too)', 'EVAL-MISMATCH', 'B'],
    ['1-8/1', 'Remove classes and the header', 'Cleared Class column, then also deleted "Name"', 'Keep "Name"', 'A-INTENT (ambig.)', 'A'],
    ['1-8/2', 'Delete all amounts (salary)', 'Cleared amounts; kept "amount" header', 'Header deleted too', 'EVAL-MISMATCH (ambig.)', 'B'],
    ['1-8/4', 'Delete all amounts (shopping)', 'Cleared amounts; kept "amount" header', 'Header deleted too', 'EVAL-MISMATCH (ambig.)', 'B'],
    ['1-9/0', 'Average of two midterms in bottom row', 'Per-student average column; hit 20 steps at row 15',
     'Row 22: Average / 80.5 / 78.3 (80.5 is wrong; true 80.05)', 'A-INTENT + broken check', 'A+B'],
    ['1-10/4', 'What is the fewest amount of bought item?', 'Answered "2"', 'Answer contains "apple"', 'EVAL-MISMATCH (ambig.)', 'B'],
    ['1-11/1', 'Split scores into midterm1/2.xlsx', 'midterm1 correct; midterm2 cut off at 20 steps', 'Both files exact', 'A-ACTION (budget)', 'A'],
    ['1-14/2', 'Swap lowest and highest salary item', 'Swapped names only; amounts left in place',
     'reference "salery.xlsx" does not exist (crash)', 'A-INTENT + broken check', 'A+B'],
    ['1-14/3', 'Swap fewest and second fewest item', 'Swapped names only (cabbage 2, apple 3)',
     'Reference swaps apple with onion', 'A-INTENT + broken check', 'A+B'],
]
bg = {i: (BENCH if r[5] == 'B' else BOTH if r[5] == 'A+B' else AGENT) for i, r in enumerate(APP) if i}
table(APP, [12*mm, 33*mm, 42*mm, 40*mm, 34*mm, 11*mm], row_bgs=bg, bold_first_col=True)

story.append(Spacer(1, 10))
method = [Paragraph('Method', H3), Paragraph('Source data: tasks/&lt;task&gt;/outputs/&lt;sub&gt;/gemma4_31b_think/ (env_history.json, llm_history.json, '
  'final testbed), the reference files under tasks/&lt;task&gt;/reference/, and the check code in '
  'utils/evaluate.py. Every check was re-run with UTF-8 file reading. Each failure was given one primary code '
  'following the decision procedure in analysis/codebook.md (judge the output against the task as written; if '
  'it is right, the cause is on the benchmark side; if it is wrong, code the decisive agent step). These codes '
  'were assigned by one annotator from the traces. Unlike the earlier 16-case set (two annotators, '
  '&kappa; = 0.78 on primary code), they have not been double-coded, and the wording-dependent cases are the '
  'ones most likely to be coded differently by a second annotator.', SMALL)]
story.append(KeepTogether(method))

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm,
                        leftMargin=16*mm, rightMargin=16*mm,
                        title='Why the tasks fail - OfficeBench gemma4:31b', author='OfficeBench analysis')


def footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16*mm, 9*mm, 'OfficeBench gemma4:31b - failure analysis')
    canvas.drawRightString(A4[0] - 16*mm, 9*mm, f'page {doc_.page}')
    canvas.restoreState()


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
