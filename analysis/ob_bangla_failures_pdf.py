"""Why OfficeBench tasks fail when the agent works in Bangla (gemma4:31b, full 300-subtask run).

Sources: paired English (gemma4_31b_think) and Bangla (gemma4_31b_bn) runs; per-check results from the
paired-comparison script (scratchpad ob_bn/pairs.py, email checks with the host-path fix); every subtask
that passed in only one language was read in full; the 130 subtasks failing in both languages were
classified by root cause from their traces.

    python analysis/ob_bangla_failures_pdf.py [out.pdf]
"""
import os, sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether, CondPageBreak, PageBreak)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'analysis', 'officebench_bangla_failure_analysis.pdf')

INK = colors.HexColor('#18202c')
MUTED = colors.HexColor('#5a6476')
ACCENT = colors.HexColor('#2d5a9b')
LINE = colors.HexColor('#dce1e8')
BOX = colors.HexColor('#f6f7f9')
LANG = colors.HexColor('#fbeee6')
SHARED = colors.HexColor('#e6eefb')
WIN = colors.HexColor('#e7f4ec')

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], textColor=INK, fontSize=20, leading=24, alignment=0, spaceAfter=2)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], textColor=MUTED, fontSize=9.3, leading=13)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=INK, fontSize=14, leading=18, spaceBefore=12, spaceAfter=5)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], textColor=ACCENT, fontSize=10.8, leading=14, spaceBefore=9, spaceAfter=2)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], textColor=INK, fontSize=9.6, leading=13.8, spaceAfter=3)
BUL = ParagraphStyle('BUL', parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=1.5)
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], textColor=MUTED, fontSize=8.2, leading=11)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], textColor=INK, fontSize=8, leading=10.4)
HEAD = ParagraphStyle('HEAD', parent=CELL, fontName='Helvetica-Bold', textColor=colors.white)
QUOTE = ParagraphStyle('QUOTE', parent=BODY, textColor=MUTED, fontName='Helvetica-Oblique', leftIndent=12, fontSize=9)

story = []
p = lambda t, s=BODY: story.append(Paragraph(t, s))
bul = lambda x: Paragraph(x, BUL, bulletText='•')


def bullets(items):
    for it in items:
        story.append(bul(it))


def table(rows, widths, bgs=None, add=True):
    data = [[Paragraph(str(c), HEAD) for c in rows[0]]] + [[Paragraph(str(c), CELL) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    cmds = [('BACKGROUND', (0, 0), (-1, 0), ACCENT),
            ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
            ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')]
    if bgs:
        cmds += [('BACKGROUND', (0, i), (-1, i), c) for i, c in bgs.items()]
    else:
        cmds.append(('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BOX]))
    t.setStyle(TableStyle(cmds))
    if add:
        story.append(t)
    return t


def section(title, intro, items, quote=None, why=None, fix=None):
    blk = [Paragraph(title, H3), Paragraph(intro, BODY)] + [bul(i) for i in items]
    if quote:
        blk.append(Paragraph(quote, QUOTE))
    if why:
        blk.append(Paragraph(f'<b>Why it happens:</b> {why}', BODY))
    if fix:
        blk.append(Paragraph(f'<b>How to fix or test it:</b> {fix}', BODY))
    story.append(KeepTogether(blk))


# ================================================================== title
p('Why OfficeBench tasks fail in Bangla', H1)
p('gemma4:31b (Ollama), temperature 0, 20-step limit &middot; full run: 300 subtasks in each language, '
  '297 compared pair by pair &middot; 2026-10-03', SUB)
story.append(Spacer(1, 3))
story.append(HRFlowable(width='100%', thickness=0.6, color=LINE))

# ================================================================== summary
p('Summary', H2)
p('The same model ran every OfficeBench subtask twice: once with the original English prompt and once with the '
  'system prompt, task and instructions translated into Bangla. Files, calendars and emails stayed in English in '
  'both runs. I compared the two runs subtask by subtask, read every subtask that passed in only one language, and '
  'classified the root cause of every Bangla failure.')
bullets([
    '<b>Score.</b> Officially, English passes 132 of 300 (44.0%) and Bangla 103 of 300 (34.3%). With the email '
    'checks scored correctly (see the box below), on the 297 subtasks that can be compared, English passes '
    '<b>149 (50.2%)</b> and Bangla <b>127 (42.8%)</b>.',
    '<b>Most Bangla failures are not caused by Bangla.</b> Of the 170 Bangla failures, 130 also fail in English, '
    'and 89 of those fail for exactly the same reason: benchmark defects, running out of steps, cut-off output, '
    'wrong content.',
    '<b>40 failures are Bangla-only.</b> Over half of them (23) are the agent writing its result back in English the '
    'wrong way: answers in Bangla script (15), names in the wrong case (4), a different English word (3), a '
    'translated quoted phrase copied into a file (1). Another 4 come from the translation changing the meaning of '
    'the task. Only 6 are the agent reading or reasoning differently from a faithful translation, and 7 are '
    'execution problems.',
    '<b>Bangla also wins 18 subtasks</b> that English fails, mostly because English stepped into environment traps '
    'or wrote reasoning so long that its commands were cut off.',
    '<b>The gap closes with task difficulty:</b> single-app 63 vs 48, two-app 58 vs 51, three-app 28 vs 28.',
])

box = Table([[Paragraph(
    '<b>About the scores.</b> The repository&rsquo;s email check fails on the host machine for every run '
    '(apps/email_app/email_list_emails.py reads a hard-coded /testbed path), so the official result files undercount '
    'both languages. All numbers in this report use that check fixed and the mailbox matched by exact name; this also '
    'turns 3-12/0 into a pass in both languages. Excluded pairs: 2-1/0 and 2-1/1 (the model API returned empty '
    'replies in the Bangla run) and 3-52/0 (no English history).', SMALL)]], colWidths=[178*mm])
box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), BOX), ('BOX', (0, 0), (-1, -1), 0.6, LINE),
                         ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                         ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
story.append(Spacer(1, 3))
story.append(box)

# ================================================================== numbers
p('The numbers', H2)
table([
    ['', 'Subtasks', 'English passes', 'Bangla passes', 'Gap'],
    ['Single-app', '93', '63 (67.7%)', '48 (51.6%)', '15'],
    ['Two-app', '93', '58 (62.4%)', '51 (54.8%)', '7'],
    ['Three-app', '111', '28 (25.2%)', '28 (25.2%)', '0'],
    ['<b>All</b>', '<b>297</b>', '<b>149 (50.2%)</b>', '<b>127 (42.8%)</b>', '<b>22</b>'],
], [44*mm, 26*mm, 38*mm, 38*mm, 32*mm])
story.append(Spacer(1, 6))
p('Where the 170 Bangla failures come from', H3)
table([
    ['Group', 'Subtasks', 'What it means'],
    ['Fail in both languages, same cause', '89', 'Not a language effect: the agent or the benchmark fails the same way'],
    ['Fail in both languages, different cause', '41', 'Both fail, but Bangla fails differently (some of these are language effects, see Part 3)'],
    ['Fail only in Bangla', '40', 'Candidates for language effects (Part 1)'],
    ['<b>All Bangla failures</b>', '<b>170</b>', ''],
    ['For comparison: fail only in English', '18', 'Subtasks Bangla passes and English fails (Part 2)'],
], [62*mm, 22*mm, 94*mm], bgs={1: SHARED, 2: SHARED, 3: LANG, 5: WIN})

# ================================================================== Part 1
story.append(CondPageBreak(80*mm))
p('Part 1 &mdash; The 40 failures that happen only in Bangla', H2)
table([
    ['Cause', 'Subtasks', 'Language-related?'],
    ['A. Result written back in English the wrong way', '23', 'Yes'],
    ['&nbsp;&nbsp;&nbsp;A1. Correct answer written in Bangla script', '15', 'Yes'],
    ['&nbsp;&nbsp;&nbsp;A2. Person&rsquo;s name in the wrong case, or the wrong mailbox', '4', 'Yes'],
    ['&nbsp;&nbsp;&nbsp;A3. A different English word or format in the file', '3', 'Yes'],
    ['&nbsp;&nbsp;&nbsp;A4. A translated quoted phrase copied into the file', '1', 'Yes (translation)'],
    ['B. The translation changed what the task means', '4', 'Yes (translation)'],
    ['C. Faithful translation, but the task was read or reasoned about differently', '6', 'Unclear'],
    ['D. Execution: cut-off output, out of steps, "no tool"', '7', 'Mostly no'],
    ['<b>Total</b>', '<b>40</b>', ''],
], [112*mm, 22*mm, 44*mm])

section('A1. Correct answer written in Bangla script (15 subtasks)',
        'The prompt never says which language to answer in, so the agent answers questions in Bangla, with Bangla '
        'digits. The checks look for English words or ASCII digits, so a correct answer is marked wrong. In all 15 '
        'cases the content matches the English run.',
        ['1-10/0 "what is the difference between the lowest and highest midterm-1 score?": "the highest is 100, the '
         'lowest is 60, the difference is 40", written in Bangla with Bangla digits.',
         '1-13/2: answered "na" (Bangla for "no"); the check looks for "No".',
         '2-31/0: answered "$20,000" with Bangla digits; the check looks for "20000".',
         'Others: 1-2/3, 1-2/4, 1-11/2, 1-12/0, 1-12/1, 1-23/1, 2-5/0, 2-32/0, 2-33/1, 2-34/1, 2-36/1, 2-36/2.',
         'Three more correct Bangla answers are hidden among the subtasks that fail in both languages (1-22/2, '
         '1-22/3 "yes"; 1-22/4 "93"), where English got the answer wrong.'],
        why='the agent writes to the user in the user&rsquo;s language, but writes everything it passes to tools in '
            'English (no Bangla in the values written into cells, events and emails, apart from 3 runs: two copied '
            'the translated homework text (A4) and one wrote a congratulation letter to a student in Bangla). The benchmark only accepts English answers.',
        fix='add "write the final answer in English" to the Bangla prompt, or score answers by meaning.')

section('A2. Person&rsquo;s name in the wrong case, or the wrong mailbox (4 subtasks)',
        'In the email tasks about Bob, the Bangla task writes the name only in Bangla script, which has no capital '
        'letters. When the agent writes it back in Latin letters for the tool, it often writes "bob". Mailbox names '
        'are case-sensitive, so the listing is empty and the agent concludes there are no emails.',
        ['1-21/2 "does Bob receive emails in last month?": queried "bob", got "No emails found", answered "no" (in '
         'Bangla); the correct answer is "yes".',
         '1-20/2 and 1-21/1: queried the user&rsquo;s own mailbox ("Alice") instead of Bob&rsquo;s and gave up.',
         'Others: 1-20/3.',
         'Measured over all runs: when a name appears in Latin letters in the prompt, the Bangla agent uses the exact '
         'case every time (49 of 49 tool calls; English 93 of 100). When the name appears only in Bangla script, it '
         'gets the case right in 26 of 37.'],
        why='the agent has to rebuild an identifier from a script that has no case information.',
        fix='keep person names in Latin script inside the Bangla task text; or make mailbox lookup case-insensitive.')

section('A3. A different English word or format in the file (3 subtasks)',
        'When the agent has to produce an English word itself, it sometimes picks a synonym or a different format '
        'from the one in the English task.',
        ['1-1/4 "Bob has a travelling ... set as a calendar event": event named "Trip to Florida"; the check looks for '
         '"travel".',
         '1-4/1 "buy two yogurt": wrote "curd" (the Bangla word "doi" means both).',
         '1-6/2 meetings "start from 8:00": wrote "08:00 AM"; the check looks for "8:00".',
         'Words the agent can copy from a file are never lost: "onion", "stock", "computer" and "dinner" all came '
         'back exactly, even when the Bangla prompt used a native word.'],
        why='the Bangla prompt replaced the English word; the agent translates it back and may choose another word.',
        fix='keep check keywords in Latin script inside the translation, or accept synonyms and equivalent formats.')

section('A4. A translated quoted phrase copied into the file (1 subtask, plus 1 among shared failures)',
        'The agent copies quoted text from the task exactly (17 of 17 quoted phrases in English were copied verbatim). '
        'Here the translator had translated the quoted text, so the agent faithfully copied the Bangla.',
        ['3-56/0 assign homework "read book and write essay": the Bangla task quotes it in Bangla, and the agent wrote '
         'the Bangla phrase into hw1.docx. The check looks for the English text.',
         'The same happens in 3-57/0, which also fails in English for another reason.'],
        why='machine translation of a literal that should have stayed in English.',
        fix='never translate quoted strings, file names or keywords.')

section('B. The translation changed what the task means (4 subtasks)',
        'In these cases the Bangla text says something different from the English, and the agent followed the '
        'Bangla correctly.',
        ['3-17/0 "make an image post welcome.jpg, email ... with welcome image in welcome.eml": the Bangla says "email '
         'the welcome image <i>that is contained in</i> welcome.eml". The agent searched for the files as if they '
         'already existed, then reported they could not be found.',
         '3-55/0 "make a post reward.jpg": the Bangla says "make a post <i>for</i> reward.jpg". The agent wrote a '
         'social-media caption and never created the image. (English passed only by creating an empty file.)',
         '3-68/0 "sum all the costs in costs.xlsx": the Bangla verb "jog korun" means both "add" and "sum". The agent '
         'added each cost as a row and never wrote the total.',
         '2-40/2 "every event except sleeping": the Bangla says "except the act of sleeping". The agent also left out '
         '"nap" as a kind of sleep; the check needs "nap".'],
        why='the task text was machine-translated by the same model, and several English tasks are terse or '
            'ungrammatical.',
        fix='have the translations checked by a Bangla speaker before running.')

section('C. Faithful translation, task read or reasoned about differently (6 subtasks)',
        'The Bangla text means the same as the English, but the agent did something else. These are the closest '
        'thing to "reasoning in Bangla is worse", and they are few.',
        ['1-11/0 sort students by midterm1: wrote only the Name and midterm1 columns and dropped midterm2.',
         '2-17/0 schedule meetings for each class: created the events in the user&rsquo;s own calendar instead of the '
         'students&rsquo; calendars.',
         '2-20/0 find students taking CS161: decided this meant "students whose Major is CS" and listed 3 of them.',
         '2-38/2 send notification.eml to people: treated notification.eml as an existing file and switched between '
         'apps for 15 steps without sending anything (see the note on output files below).',
         '2-32/1 compare income and expenditure: used the budget file as income and answered "larger"; English '
         'answered "smaller" for a wrong reason.',
         '3-87/0 count qualifying terms: counted 11 at one step, then recounted at the next step and wrote 10.'],
        why='no single cause. 3-87/0 is the known problem that earlier reasoning is not carried to the next step.')

section('D. Execution problems (7 subtasks)',
        'Problems that also happen in English, but happened here only in the Bangla run.',
        ['<b>Cut-off output (4):</b> 1-15/0, 1-15/1, 2-6/0, 2-22/1. In 1-15/0 ("add a sentence to the end of the '
         'document") the Bangla agent assumed write_to_file overwrites the file and tried to rewrite the whole story; '
         'the response hit the 512-token limit and was retried 14 times. English wrote only the sentence (the tool '
         'appends) and passed.',
         '<b>Out of steps (2):</b> 3-64/0 and 3-9/0 spent 8 and 13 steps re-asking the in-container llm app, which '
         'answers in at most 50 tokens, for a complete text.',
         '<b>"No image tool" (1):</b> 3-15/0: "since I have no image-generation tool, I go straight to sending the '
         'email". English tried the shell&rsquo;s image converter and succeeded.'])

story.append(KeepTogether([Paragraph('A pattern across groups B, C and the shared failures: output files read as inputs', H3),
    Paragraph('In 7 Bangla runs the agent treated a file the task asks it to <i>create</i> as one that should already '
              'exist, and went looking for it: 2-38/2, 3-17/0, 2-44/0, 2-45/1, 3-12/2, 3-19/0, and 2-45/0 (which '
              'recovered and passed). The translations phrase these files with the Bangla definite marker, e.g. '
              '"notification.eml imel-ti pathan", meaning "send <i>the</i> email notification.eml", which presents '
              'the file as something that already exists. On the same tasks English either passed or failed for other reasons.', BODY)]))

# ================================================================== Part 2
story.append(CondPageBreak(70*mm))
p('Part 2 &mdash; The 18 subtasks only Bangla passes', H2)
p('These explain why the gap is smaller than Part 1 suggests, and why it disappears on three-app tasks.')
table([
    ['Why English failed and Bangla did not', 'Subtasks', 'Which'],
    ['English stepped into an environment or check trap', '7', '2-34/0 (relative path), 2-36/3 and 3-89/0 (double quotes broke the shell command), 2-45/0 (one email to two addresses), 3-70/0 (.png instead of .jpg), 3-61/0 (unsupported attachment field), 2-39/0 (lower-case "bob"; Bangla retried "Bob")'],
    ['English wrote long reasoning that pushed its command past the token limit, or wasted steps', '7', '2-43/0, 3-21/0, 3-59/0, 2-22/0 (cut-off), 3-26/0, 3-65/0, 2-8/0 (re-asking the llm app)'],
    ['The translation settled an ambiguity the right way', '2', '1-8/0, 1-8/1 ("the header")'],
    ['Bangla avoided an unnecessary action', '1', '1-2/1 (did not add a duplicate dinner event)'],
    ['Bangla chose the expected word', '1', '3-92/0 (subject "Party Invitation")'],
], [62*mm, 18*mm, 98*mm])
story.append(Spacer(1, 4))
p('<b>Shorter reasoning in Bangla.</b> On three-app tasks, Bangla reasoning averages 336 characters per step against '
  '422 in English, and Bangla calls the 50-token llm app less often (151 vs 256 calls). English more often fills the '
  '512-token response with reasoning before reaching the command (62 vs 19 responses cut off before the command). '
  'Runs with a malformed step: English 69, Bangla 28. This is why Bangla catches up on the hardest tasks.')
p('<b>No fake files in Bangla.</b> On tasks that ask for an image, English created an empty placeholder image in 5 '
  'runs (e.g. 3-55/0 <font face="Courier">touch reward.jpg</font>), which passes "file exists" checks. Bangla did '
  'this 0 times; when it could not make the image it said so. Both languages sometimes claim there is no image '
  'tool (14 English runs, 10 Bangla).')

# ================================================================== Part 3
story.append(PageBreak())
p('Part 3 &mdash; The 130 failures shared with English', H2)
p('These are the agent&rsquo;s and the benchmark&rsquo;s general problems. 89 fail for the same reason in both '
  'languages.')
table([
    ['Root cause of the Bangla failure', '1-app', '2-app', '3-app', 'Total', 'Same cause in English', 'English total'],
    ['Benchmark defect decides the result', '12', '6', '21', '39', '33', '42'],
    ['Wrong content (bad value, OCR misread, information dropped)', '9', '10', '17', '36', '24', '34'],
    ['Out of steps (cell-by-cell writing, llm re-asking)', '1', '0', '17', '18', '14', '25'],
    ['Task read differently', '3', '3', '6', '12', '4', '5'],
    ['Cut-off output, retried', '1', '3', '5', '9', '7', '10'],
    ['Empty result treated as "nothing exists"', '1', '4', '4', '9', '5', '9'],
    ['Says the output is impossible ("no tool")', '0', '0', '3', '3', '0', '0'],
    ['Finished with an output missing', '0', '2', '0', '2', '2', '2'],
    ['Other', '0', '0', '2', '2', '0', '3'],
    ['<b>Total</b>', '<b>27</b>', '<b>28</b>', '<b>75</b>', '<b>130</b>', '<b>89</b>', '<b>130</b>'],
], [64*mm, 13*mm, 13*mm, 13*mm, 15*mm, 30*mm, 30*mm])
p('3-12/0 is excluded from this table: it passes in both languages once the email check matches mailboxes by exact '
  'name.', SMALL)

section('Benchmark defects (39 Bangla failures)',
        'A third of the shared failures cannot be passed by a correct agent, or depend on how ambiguous wording is '
        'read. Defects checked against the code:',
        ['<b>Calendar times:</b> the calendar tool writes times without the "Z" suffix (DTSTART:20240531T130000), '
         'but several checks require it (3-20, 3-24, 3-28, 3-73, 3-74).',
         '<b>PDF names:</b> on Linux, convert_to_pdf calls LibreOffice with only an output folder, so the PDF keeps the '
         'source file&rsquo;s name while the tool reports the requested name (3-4, 3-67, 3-86, 3-25, 2-39/2).',
         '<b>Shell quoting:</b> every shell command is wrapped in <font face="Courier">bash -c """..."""</font>, so a '
         'command containing double quotes silently writes nothing (2-33, 3-44, 3-72, 2-12).',
         '<b>Excel:</b> set_cell erases the value 1 (1-5/1, 1-6/0).',
         '<b>Wrong check targets or values:</b> 1-6/3 (wrong file), 1-14/2 (misspelled salery.xlsx), 1-14/3 (wrong '
         'reference), 3-1 (misspelled "Activaty"), 3-58 ("banana" not in the data), 3-8/5 (expects 7 and 4; the data '
         'gives 2 and 2), 2-2/0 and 2-2/1 (checks swapped), 3-62 (a PDF comparison that can never pass), 3-8/6 (the '
         'sender keeps a copy, so "Alice must not receive it" fails), 3-82 (docx opened as xlsx), 3-80 (wrong image '
         'name), 2-26/3, 3-99.',
         '<b>Checks asking for things the task does not:</b> 1-2/0, 1-2/2 (calendar events for a "find a time" task), '
         '1-8/2, 1-8/4, 2-14, 2-45/2, 2-39/3, 3-43, 3-13/1; debatable: 1-6/4, 1-10/4, 3-22, 3-30, 3-49, 3-76.'])

section('Agent problems that appear in both languages',
        'The rest are the agent&rsquo;s own habits, the same in English and Bangla:',
        ['<b>Wrong content (36):</b> OCR misreads copied without checking (2-10/0: "Mice", "ob", "avid" written as '
         'names), labels dropped (2-23/0 wrote 104.98 without "total due"), numbers reformatted ("$1,200,000" for '
         '1200000).',
         '<b>Out of steps (18):</b> the Excel tool writes one cell per action, so copying a table takes more than 20 '
         'steps (1-11/1, 3-35 to 3-41); or the agent keeps re-asking the 50-token llm app for a "complete" answer.',
         '<b>Cut-off output (9):</b> a whole document or long prompt in one action exceeds 512 tokens (1-19/1 retried '
         'from step 5 to 19).',
         '<b>Empty result read as "nothing exists" (9):</b> 3-90/0 lists only Bob&rsquo;s calendar, gets "No events '
         'found" and stops; the data is in Alice.ics.',
         '<b>Task read differently (12 Bangla vs 5 English):</b> Bangla has more of these, mostly the "output file '
         'read as input" pattern (2-12/0, 2-44/0, 2-45/1, 3-11/0, 3-12/2, 3-19/0) and 3-42/0, where the Bangla run '
         'never listed the data folder and made up a stock table.',
         '<b>"No image tool" (3, Bangla only):</b> 3-18/0, 3-85/0, 3-94/0. English failed these for other reasons, '
         'sometimes after creating an empty placeholder image.'])

section('Language effects hidden among the shared failures',
        'Some subtasks fail in both languages, but the Bangla failure is still a language effect:',
        ['1-22/2, 1-22/3, 1-22/4: Bangla answered correctly ("yes", "yes", "93") in Bangla script; English answered '
         'wrongly after querying the mailbox "alice" in lower case.',
         '3-57/0: the translated homework phrase was copied into the file (as in 3-56/0).',
         '1-4/3: Bangla wrote "utility fee" (back from the Bangla "iutiliti fi"); English wrote "utilities"; the check '
         'wants "utilities fee".'])

# ================================================================== Part 4
story.append(CondPageBreak(60*mm))
p('Part 4 &mdash; What this means', H2)
bullets([
    '<b>Bangla does not break the agent&rsquo;s reasoning much.</b> Only 6 of 297 subtasks fail in Bangla because '
    'the agent read or reasoned differently from a faithful translation, and Bangla wins 18 subtasks back.',
    '<b>The cost of Bangla is at the boundaries.</b> 23 Bangla-only failures happen when the result has to be '
    'written back in English (answer language, name case, word choice, a translated literal), and 4 come from the '
    'translation itself. Over half of the gap would close with an English-answer instruction and better '
    'translations.',
    '<b>Most failures are shared.</b> Benchmark defects and the agent&rsquo;s general habits (one cell per action, '
    'long outputs cut off, no checking of its own work, giving up on empty results) cause most failures in both '
    'languages.',
    '<b>Bangla reasoning is shorter.</b> That costs nothing on easy tasks and helps on the hardest ones, where long '
    'English reasoning pushes commands past the 512-token limit.',
])
p('Experiments that would confirm these causes', H3)
bullets([
    'Add "write the final answer in English" to the Bangla prompt (tests A1).',
    'Keep names, file names and check keywords in Latin script inside the Bangla tasks (tests A2, A3, A4 and the '
    'output-file pattern).',
    'Have the 300 translations checked by a Bangla speaker (tests B).',
    'Re-run the 58 subtasks that pass in only one language once more to confirm they are stable.',
    'Fix the benchmark defects in Part 3 and re-score both runs.',
])

# ================================================================== appendix
story.append(PageBreak())
p('Appendix &mdash; every subtask that passes in only one language', H2)
A = [
    ['ID', 'Task (short)', 'What went wrong in Bangla', 'Cause'],
    ['1-2/3', 'Who gets up earlier?', 'Answered "Tom gets up earlier" in Bangla', 'A1'],
    ['1-2/4', 'Who has more commitments?', 'Same answer as English, in Bangla', 'A1'],
    ['1-10/0', 'Difference of lowest and highest score', '"40" etc. in Bangla', 'A1'],
    ['1-11/2', 'Monthly income', '"35,000" in Bangla digits', 'A1'],
    ['1-12/0', 'Students in CS161, how many seniors', '"9 ... 2" in Bangla', 'A1'],
    ['1-12/1', 'Students with 60 or more', '"5" in Bangla', 'A1'],
    ['1-13/2', 'Graduation requirement met?', '"na" for "No"', 'A1'],
    ['1-23/1', 'Freshmen in CS161', '"4" in Bangla', 'A1'],
    ['2-5/0', 'Application satisfies policy?', '"yes" in Bangla', 'A1'],
    ['2-31/0', 'Maximum car price in March', '"$20,000" in Bangla digits', 'A1'],
    ['2-32/0', 'Reimbursement over budget?', '"yes" in Bangla', 'A1'],
    ['2-33/1', 'Class with fewest students', '"class 4" in Bangla', 'A1'],
    ['2-34/1', 'Age with highest score', '"26" in Bangla', 'A1'],
    ['2-36/1', 'Dean&rsquo;s list terms', '"11" in Bangla', 'A1'],
    ['2-36/2', 'Maximum sales entry', '"78,002" in Bangla', 'A1'],
    ['1-20/2', 'Latest email to Bob', 'Queried "Alice", gave up', 'A2'],
    ['1-20/3', 'Did Bob receive emails?', 'Queried "bob", empty, "no, 0"', 'A2'],
    ['1-21/1', 'Earliest email to Bob', 'Queried "Alice" then "bob"', 'A2'],
    ['1-21/2', 'Did Bob receive emails?', 'Queried "bob", answered "no"', 'A2'],
    ['1-1/4', 'Travel event', '"Trip to Florida" (needs "travel")', 'A3'],
    ['1-4/1', 'Buy two yogurt', '"curd"', 'A3'],
    ['1-6/2', 'Meetings from 8:00', '"08:00 AM"', 'A3'],
    ['3-56/0', 'Assign homework "read book..."', 'Homework text written in Bangla', 'A4'],
    ['2-40/2', 'Email events except sleeping', 'Also left out "nap"', 'B'],
    ['3-17/0', 'Image post welcome.jpg and email', 'Looked for the files as existing; none made', 'B'],
    ['3-55/0', 'Statement and post reward.jpg', 'Wrote a caption "for" the image', 'B'],
    ['3-68/0', 'Sum costs into costs.xlsx', 'Added rows, no total', 'B'],
    ['1-11/0', 'Sort scores by midterm1', 'Dropped the midterm2 column', 'C'],
    ['2-17/0', 'Meetings for each class', 'Events in the user&rsquo;s calendar', 'C'],
    ['2-20/0', 'Students taking CS161', 'Listed CS majors only', 'C'],
    ['2-38/2', 'Send notification.eml', 'Looked for the .eml; sent nothing', 'C'],
    ['2-32/1', 'Income vs expenditure', 'Used the budget as income', 'C'],
    ['3-87/0', 'Dean&rsquo;s list terms, email', 'Recounted 11 as 10', 'C'],
    ['1-15/0', 'Add a sentence to a document', 'Rewrote the whole document; cut off', 'D'],
    ['1-15/1', 'Append a section to the syllabus', 'Cut-off writes retried', 'D'],
    ['2-6/0', 'Scan homework to docx', 'Cut-off writes retried', 'D'],
    ['2-22/1', 'Instructions from price index', 'Cut-off writes retried', 'D'],
    ['3-64/0', 'House price report with image', 'Out of steps (llm re-asking)', 'D'],
    ['3-9/0', 'Revenue report as image', 'Out of steps (llm re-asking)', 'D'],
    ['3-15/0', 'Contact card image from resume', '"No image tool"', 'D'],
]
table(A, [14*mm, 52*mm, 86*mm, 26*mm])
story.append(CondPageBreak(90*mm))
p('Subtasks only Bangla passes', H3)
table([
    ['ID', 'Bangla passes, English fails because ...'],
    ['1-2/1', 'English added a duplicate dinner event that clashes with the existing one'],
    ['1-8/0, 1-8/1', 'The Bangla wording of "the header" matched the reference'],
    ['2-8/0', 'English re-asked the llm app 8 times and ran out of steps'],
    ['2-22/0, 2-43/0, 3-21/0, 3-59/0', 'English reasoning re-listed long data and its command was cut off repeatedly'],
    ['3-26/0, 3-65/0', 'English spent its steps re-asking the llm app'],
    ['2-34/0', 'English wrote the file with a relative path, outside /testbed/data'],
    ['2-36/3, 3-89/0', 'English used double quotes in a shell command, which the harness breaks'],
    ['2-39/0', 'Both queried "bob"; Bangla retried "Bob" and found the emails'],
    ['2-45/0', 'English sent one email to two addresses; the tool stored it for Bob only'],
    ['3-61/0', 'English put the file name in an unsupported attachment field'],
    ['3-70/0', 'English saved a .png; the check wants .jpg (the task does not say)'],
    ['3-92/0', 'Bangla used the subject "Party Invitation"; English did not use the word "invitation"'],
], [46*mm, 132*mm])


def footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16*mm, 9*mm, 'Why OfficeBench tasks fail in Bangla - gemma4:31b, full run')
    canvas.drawRightString(A4[0] - 16*mm, 9*mm, f'page {doc_.page}')
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=16*mm, rightMargin=16*mm,
                        title='Why OfficeBench tasks fail in Bangla', author='analysis')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
