"""Findings brief: Bangla vs English on OfficeBench (gemma4:31b), paired by subtask.

Snapshot: 106 completed Bangla runs (tag gemma4_31b_bn: 93 single-app, 13 two-app), each paired
with the English run of the same subtask (tag gemma4_31b_think); 2 pairs excluded because the
model API returned empty replies. Numbers were produced by the paired-comparison script
(scratchpad ob_bn/pairs.py) and every differing pair was read in full.

    python analysis/ob_bangla_findings_pdf.py [out.pdf]
"""
import os, sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether, CondPageBreak)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'analysis', 'officebench_bangla_findings.pdf')

INK = colors.HexColor('#18202c')
MUTED = colors.HexColor('#5a6476')
ACCENT = colors.HexColor('#2d5a9b')
LINE = colors.HexColor('#dce1e8')
BOX = colors.HexColor('#f6f7f9')
TAG = {'NEW': '#1f7a46', 'PARTLY KNOWN': '#a86a00', 'KNOWN': '#6b7280'}

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], textColor=INK, fontSize=19, leading=23, alignment=0, spaceAfter=2)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], textColor=MUTED, fontSize=9.3, leading=13)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=INK, fontSize=14, leading=18, spaceBefore=12, spaceAfter=5)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], textColor=ACCENT, fontSize=10.8, leading=14, spaceBefore=9, spaceAfter=2)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], textColor=INK, fontSize=9.6, leading=13.8, spaceAfter=3)
BUL = ParagraphStyle('BUL', parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=1.5)
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], textColor=MUTED, fontSize=8.2, leading=11)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], textColor=INK, fontSize=8, leading=10.4)
HEAD = ParagraphStyle('HEAD', parent=CELL, fontName='Helvetica-Bold', textColor=colors.white)
META = ParagraphStyle('META', parent=BODY, fontSize=8.8, leading=12.4, textColor=MUTED, spaceAfter=2)
QUOTE = ParagraphStyle('QUOTE', parent=BODY, textColor=MUTED, fontName='Helvetica-Oblique', leftIndent=12, fontSize=9)

story = []
p = lambda t, s=BODY: story.append(Paragraph(t, s))
tag = lambda t: f'<font color="{TAG[t]}"><b>[{t}]</b></font>'
bul = lambda x: Paragraph(x, BUL, bulletText='•')


def bullets(items):
    for it in items:
        story.append(bul(it))


def table(rows, widths, add=True):
    data = [[Paragraph(str(c), HEAD) for c in rows[0]]] + [[Paragraph(str(c), CELL) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BOX]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    if add:
        story.append(t)
    return t


def finding(fid, title, novelty, strength, claim, evidence=(), prior=None, caveat=None, quote=None, extra=None):
    blk = [Paragraph(f'{fid}. {title} &nbsp;{tag(novelty)}', H3), Paragraph(claim, BODY)]
    blk += [bul(e) for e in evidence]
    if quote:
        blk.append(Paragraph(quote, QUOTE))
    if extra:
        blk += extra
    blk.append(Paragraph(f'<b>Strength:</b> {strength}', META))
    if prior:
        blk.append(Paragraph(f'<b>Prior work:</b> {prior}', META))
    if caveat:
        blk.append(Paragraph(f'<b>Caveat:</b> {caveat}', META))
    story.append(KeepTogether(blk))


# ------------------------------------------------------------------ title
p('OfficeBench in Bangla vs English: findings for the paper', H1)
p('gemma4:31b (Ollama), temperature 0, 20-step limit &middot; 104 subtasks run in both languages '
  '(93 single-app, 11 two-app) &middot; snapshot 2026-10-02, Bangla run still in progress', SUB)
story.append(Spacer(1, 3))
story.append(HRFlowable(width='100%', thickness=0.6, color=LINE))

p('Setup', H2)
bullets([
    '<b>Bangla condition</b> (run tag <i>gemma4_31b_bn</i>): the system prompt, the task text and all instructions are '
    'in Bangla. Only the JSON action format and the app names stay English. The task text is a machine translation '
    'of the English task made by gemma4:31b (analysis/bn_cache.json).',
    '<b>English condition</b> (run tag <i>gemma4_31b_think</i>): the original prompt.',
    '<b>Held constant:</b> the model, temperature 0, the 20-step limit, the request to reason before each action, '
    'and all files, calendars and emails, which stay in English.',
    '<b>Not specified:</b> the prompt never says which language to write answers or files in.',
    '<b>Pairs analysed:</b> 106 Bangla runs were complete; 2 pairs (2-1/0, 2-1/1) are excluded because the model '
    'API returned empty replies, leaving 104. Every pair that passed in only one language was read in full.',
])
p('<b>Novelty tags.</b> ' + tag('NEW') + ' no prior report found in targeted web searches; ' + tag('PARTLY KNOWN') +
  ' the phenomenon is known but this setting or angle is not; ' + tag('KNOWN') + ' already reported, so cite it as a '
  'confirmation. Recheck the NEW items before submission. Scores use the email-check fix described in the earlier '
  'findings brief.', SMALL)

box = Table([[Paragraph(
    '<b>What changed since the 45-pair version of this brief.</b> With more question-answering and email tasks, the gap '
    'grew from 28 vs 26 to <b>70 vs 54</b> passes. One earlier claim is corrected: Bangla digits <i>do</i> appear in '
    'final answers (89 of them); they never appear in tool arguments. Two new mechanisms appear: lower-cased names '
    'when a person&rsquo;s name is given only in Bangla script (O4), and whole-document rewrites cut off by the token '
    'cap (O7).', BODY)]], colWidths=[178*mm])
box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fbeee6')),
                         ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#e2b49a')),
                         ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                         ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
story.append(Spacer(1, 4))
story.append(box)

# ------------------------------------------------------------------ headline
p('Headline numbers (104 matched subtasks)', H2)
table([
    ['', 'English', 'Bangla'],
    ['Passed', '70 (67.3%)', '54 (51.9%)'],
    ['&nbsp;&nbsp;single-app (93)', '63', '48'],
    ['&nbsp;&nbsp;two-app (11)', '7', '6'],
    ['Passed in only this language', '20', '4'],
    ['Same action sequence in both languages', '67 of 104 (64%); single-app 63/93, two-app 4/11', ''],
    ['Same first two actions', '99 of 104', ''],
    ['Total steps', '825', '849'],
    ['Runs that hit the 20-step limit', '5', '7'],
    ['Runs with a malformed step (malformed steps)', '8 (29)', '6 (62)'],
    ['Runs that read back what they wrote', '3 of 63', '4 of 59'],
    ['Free-text answers (non-"None")', '32', '38, of which 34 in Bangla'],
    ['Reasoning characters per step', '315', '334'],
    ['Bangla-script share of reasoning letters', '0%', 'mean 82% (range 19&ndash;99%)'],
], [78*mm, 50*mm, 50*mm])

p('Where the 16-subtask gap comes from', H3)
table([
    ['Cause of a Bangla-only failure', 'Subtasks', 'Which'],
    ['Answer written in Bangla script; content correct', '9', '1-2/3, 1-2/4, 1-10/0, 1-11/2, 1-12/0, 1-12/1, 1-13/2, 1-23/1, 2-5/0'],
    ['Person&rsquo;s name lower-cased or wrong mailbox queried, then "no emails"', '4', '1-20/2, 1-20/3, 1-21/1, 1-21/2'],
    ['Different English word or format written into a file', '3', '1-1/4, 1-4/1, 1-6/2'],
    ['Whole-document rewrite cut off by the token cap, then retry loop', '3', '1-15/0, 1-15/1, 2-6/0'],
    ['Narrower reading of the task after translation', '1', '1-11/0'],
    ['<b>Bangla-only failures</b>', '<b>20</b>', ''],
    ['Bangla-only passes (see O6, O8)', '&minus;4', '1-2/1, 1-8/0, 1-8/1, 2-8/0'],
    ['<b>Net gap</b>', '<b>16</b>', ''],
], [88*mm, 18*mm, 72*mm])
story.append(Spacer(1, 3))
p('If answers were scored on content regardless of script (the 9 answer-script cases) and the 3 word and format '
  'variants were accepted, Bangla would score 66 vs 70: about three quarters of the gap is at the output, not in '
  'understanding the task.', BODY)

p('All findings at a glance', H3)
table([
    ['ID', 'Finding', 'Strength', 'Novelty'],
    ['O1', 'Most of the gap is at the output, not in understanding (54 to 66 with content scoring)', 'Moderate to strong', 'NEW'],
    ['O2', 'Answers follow the prompt language; tool arguments never do (34/38 vs 0/283)', 'Strong', 'NEW'],
    ['O3', 'Translated keywords come back as different English words; Latin-script keywords survive', 'Moderate', 'NEW'],
    ['O4', 'Names given only in Bangla script come back lower-cased (6/8 vs 2/8)', 'Suggestive', 'NEW'],
    ['O5', 'The strategy barely changes (99/104 same opening, 64% identical runs)', 'Strong', 'NEW'],
    ['O6', 'Translation changes how ambiguous instructions are read, in both directions', 'Suggestive', 'PARTLY KNOWN'],
    ['O7', 'Whole-document rewrites cut off by the token cap, then retried', 'Suggestive', 'PARTLY KNOWN'],
    ['O8', 'Anecdotes: avoided a double booking; skipped an llm-app loop; narrated answers', 'Anecdotal', 'NEW (hypotheses)'],
    ['L1', 'Language-independent: verification, giving up, lower-casing, loops, arithmetic', 'Strong', 'KNOWN'],
], [11*mm, 107*mm, 32*mm, 28*mm])

# ------------------------------------------------------------------ Part 1
story.append(CondPageBreak(60*mm))
p('Part 1 &mdash; Bangla vs English', H2)

finding('O1', 'Most of the gap is at the output, not in understanding', 'NEW', 'moderate to strong (all 24 flips read in full).',
        'Bangla passes 54 of 104 subtasks against 70 for English. Reading every flip shows that most Bangla-only '
        'failures reached the right conclusion and failed only on how the result was written.',
        ['9 of the 20 Bangla-only failures are correct answers written in Bangla script (e.g. 1-10/0: "the highest '
         'midterm-1 score is 100 and the lowest is 60; the difference is 40", in Bangla with Bangla digits; the '
         'English run gave the same numbers in English).',
         '3 more are correct actions with a different English word or format in the file (O3).',
         'Scoring content instead of script would give Bangla 66 vs 70.'],
        prior='MAPS, X-WebAgentBench and BabelArena report non-English drops but do not split them by where the '
              'error arises. "Language confusion" (Marchisio et al., 2024) and WorldBench&rsquo;s locale mismatch '
              'describe individual pieces.')

finding('O2', 'Answers follow the prompt language; tool arguments never do', 'NEW', 'strong.',
        'With no rule about output language, the agent splits by audience: what it says to the user is in Bangla, '
        'what it passes to tools is in English.',
        ['34 of 38 free-text Bangla answers are in Bangla script, with 89 Bangla digits (e.g. 1-13/2 answers "na", '
         'Bangla for "no", where the check looks for "No").',
         '0 of 283 executed tool arguments (cell values, event names, file contents, shell commands, email fields) '
         'contain Bangla script.',
         '2,475 Bangla digits appear in the reasoning of 66 runs; none reach a tool argument.',
         '<b>Contrast with the TheAgentCompany runs:</b> there, an explicit "write messages and files in English" rule '
         'kept everything English (B2 in the earlier brief). Here, without the rule, only the answers moved to Bangla.'],
        prior='"Lost in Execution" (ACL 2026; Chinese, Hindi, Igbo) finds the opposite pattern dominant: tool '
              'parameter values written in the user&rsquo;s language. This model keeps tool arguments English and '
              'moves only the user-facing answer. Language confusion work (Marchisio et al.) asks whether models '
              'answer in the user&rsquo;s language; here they do, and the English-only checker penalises it.')

finding('O3', 'Translated keywords come back as different English words', 'NEW', 'moderate (46 checks).',
        'For every check that needs an English word from the task, I looked at whether the Bangla prompt kept that '
        'word in Latin script or turned it into Bangla.',
        extra=[Spacer(1, 2), table([
            ['The English word the check needs was ...', 'Checks', 'English passed', 'Bangla passed'],
            ['left in Latin script in the Bangla prompt', '21', '17', '15'],
            ['translated or transliterated into Bangla', '25', '17', '9'],
        ], [86*mm, 26*mm, 33*mm, 33*mm], add=False), Spacer(1, 3)] + [bul(x) for x in [
            'The 2 losses in the first row come from cut-off rewrites (O7), not from wording.',
            'The second row loses 8: answers in Bangla script (Tom twice, "yes" twice, "No"), a retry loop (1-15/1), '
            'and two word changes: "travelling" became the event "Trip to Florida" (1-1/4) and "yogurt" became "curd" '
            '(1-4/1).',
            'Format drifts the same way: "8:00" became "08:00 AM" (1-6/2), and "utilities fee" became "utility fee" '
            '(1-4/3, which English also fails, with "utilities").',
            'Words the agent can copy from the files or calendars are recovered even when the prompt uses a native '
            'Bangla word: "onion" (1-7/5), "stock" (1-7/3), "computer" (1-7/4), "dinner" (1-2/1).']],
        prior='translation artifacts in translated test sets (Artetxe et al., EMNLP 2020) and English-source cue '
              'inheritance (2605.07093). The role of the environment in recovering the English word is not found '
              'reported.')

finding('O4', 'Names given only in Bangla script come back lower-cased', 'NEW', 'suggestive (8 tasks).',
        'In the 8 email tasks about Bob (1-20/0&ndash;4, 1-21/0&ndash;2), the English task writes "Bob"; the Bangla task '
        'writes the name only in Bangla script, which has no capital letters.',
        ['The English agent queried the mailbox as "bob" in 2 of 8 runs; the Bangla agent did in 6 of 8.',
         'The mailbox folder is "Bob" and the tool is case-sensitive, so the listing comes back empty and the agent '
         'concludes there are no emails (e.g. 1-21/2 answers "no" in Bangla; the correct answer is "yes").',
         'English passed 4 of these 8 tasks, Bangla 1.',
         'In 1-20/2 the Bangla agent queried only the user&rsquo;s own mailbox ("Alice") and gave up; in 1-21/1 it '
         'tried "Alice" and then "bob". The English agent also tried "alice" first in 1-20/2, but then searched the '
         'file system, found the Bob folder and answered correctly.'],
        prior='lower-casing usernames also happens in English (A4 in the earlier brief), and romanization is studied '
              'as a model-internal mechanism (RomanLens; RomanSetu). Case loss when converting a name back from a '
              'caseless script for a tool call is not found reported.',
        caveat='8 tasks; across all 104 pairs, case mismatches are similar (English 5 of 45 username calls, Bangla 6 '
               'of 46), because in tasks about the user ("my emails") both languages guess the name.')

finding('O5', 'The strategy barely changes', 'NEW', 'strong for single-app tasks.',
        'Translating the whole prompt leaves the plan largely unchanged.',
        ['99 of 104 pairs start with the same two actions; 67 (64%) take exactly the same sequence of actions.',
         'Identical runs are far more common in single-app tasks (63/93) than two-app tasks (4/11).',
         'Use of the llm app is the same (5 runs each); steps rise by 3% (825 to 849).'],
        prior='MAPS reports "planning drift" in non-English languages and PolyWorkBench reports that language affects '
              'the whole trajectory; both also translate the working material. Here only the instruction is '
              'translated.',
        caveat='two-app tasks so far are few (11); divergence may grow with chain length.')

finding('O6', 'Translation changes how ambiguous instructions are read, in both directions', 'PARTLY KNOWN', 'suggestive (3 cases).',
        'The translation settles ambiguities in the English task, sometimes towards the reference and sometimes away.',
        ['1-8/1 "remove all students&rsquo; class and the header": the Bangla text says "the header" in the singular, '
         'definite form. The agent deleted only the Class header and kept "Name", matching the reference; the '
         'English run also deleted "Name". Bangla passes.',
         '1-8/0 "delete all students&rsquo; score and the header": the Bangla run cleared the whole table including '
         'names, matching the reference; the English run kept the names. Bangla passes.',
         '1-11/0 "sort students score descently by midterm1": the Bangla text reads as "sort the students&rsquo; scores '
         'by midterm1"; the agent wrote only the Name and midterm1 columns and dropped midterm2. Bangla fails.'],
        prior='translation artifacts change model behaviour on translated test sets (Artetxe et al., 2020).',
        caveat='the translation was produced by gemma4:31b itself.')

finding('O7', 'Whole-document rewrites cut off by the token cap, then retried', 'PARTLY KNOWN', 'suggestive (3 cases).',
        'In 3 document-editing tasks the Bangla agent tried to write a whole document in one action; the response was '
        'cut off by the 512-token cap and the same action was retried until the step limit.',
        ['1-15/0 "add a sentence to the end of house_creak.docx": the English agent wrote only the sentence (the tool '
         'appends; the document grew from 12,891 to 12,932 characters) and passed. The Bangla agent read the file, '
         'reasoned that write_to_file overwrites it, and tried to rewrite the full story plus the sentence, 14 times.',
         'The tool description is the same English text in both prompts and does not say whether it appends.',
         'Malformed steps: English 29 in 8 runs, Bangla 62 in 6 runs; the excess is these retry streaks (14&ndash;15 '
         'steps each), not more runs with errors.'],
        prior='truncation-driven retry loops are known (2607.01641) and appear in English too (A2 in the earlier '
              'brief). The different belief about the tool in Bangla is one or two cases.',
        caveat='depends on the harness&rsquo;s 512-token response cap.')

finding('O8', 'Anecdotal differences (state as hypotheses only)', 'NEW', 'anecdotal (one or a few cases each).',
        'Contrasts worth re-testing on the full run.',
        ['<b>Avoided an over-action.</b> 1-2/1: both calendars already show dinner at 18:30&ndash;19:30. The English run '
         'added a second, overlapping dinner and failed; the Bangla run answered that they already share dinner, and '
         'passed.',
         '<b>Skipped a tool loop.</b> 2-8/0 (business cards to contacts.xlsx): the English run re-prompted the '
         '50-token llm app 8 times and ran out of steps; the Bangla run wrote the OCR results straight into the sheet '
         'and passed.',
         '<b>Narrated answers on non-question tasks.</b> In 6 of 72 non-question tasks the Bangla run wrote a Bangla '
         'summary as the final answer, where the instructions say to answer "None"; the English run never did.'])

# ------------------------------------------------------------------ Part 2
story.append(CondPageBreak(70*mm))
p('Part 2 &mdash; Behaviour that does not depend on language', H2)
finding('L1', 'The same agent habits appear in both languages', 'KNOWN', 'strong.',
        'The behaviours found across all 300 English runs (A1 to A12 in the earlier brief) show up equally in the '
        'Bangla runs.',
        ['<b>Almost no verification:</b> runs that read back what they wrote: English 3 of 63, Bangla 4 of 59.',
         '<b>Giving up after an empty result:</b> runs with an empty email or calendar listing that finished within 2 '
         'steps: English 3 of 7, Bangla 3 of 9.',
         '<b>Lower-casing usernames:</b> English 5 of 45 username calls, Bangla 6 of 46 (but see O4).',
         '<b>Finishing and limits:</b> finished 99 vs 97 of 104; 20-step limit 5 vs 7.',
         '<b>Retry loops after cut-off output:</b> present in both (O7).',
         '<b>Arithmetic slips:</b> 1-5/3 (budget after 3 years at 10%) is wrong in both with different wrong values '
         '(English 2,730,381; Bangla 2,730,881; correct 2,729,881).'],
        prior='"no or incomplete verification" (MAST); "search inertia" (SciExplore).')

# ------------------------------------------------------------------ caveats
p('Caveats and next steps', H2)
bullets([
    '<b>Partial run.</b> 104 of 300 subtasks; no three-app tasks yet and only 11 two-app tasks. Re-run the paired '
    'comparison when the run finishes.',
    '<b>Translation by the same model.</b> The Bangla tasks were translated by gemma4:31b; a human-checked translation '
    'would separate translation quality from agent behaviour (affects O3, O4, O6).',
    '<b>Determinism.</b> Temperature 0 makes most differences attributable to the prompt language, but Ollama is not '
    'perfectly deterministic; repeating the 24 differing pairs once would confirm they are stable.',
    '<b>Report two scores.</b> The official (English-keyword) score and a content score that accepts a correct Bangla '
    'answer, synonyms and equivalent time formats. The difference is the evaluation share of the gap (O1).',
    '<b>Ablations that would make O2 and O4 causal:</b> (1) add "write the final answer in English" to the Bangla '
    'prompt; (2) keep person names in Latin script inside the Bangla task text.',
])

p('Sources', H2)
SRC = [
    ('Lost in Execution: multilingual robustness of tool calling (ACL 2026)', 'https://aclanthology.org/2026.acl-long.2039/'),
    ('When the API speaks the wrong language: multilingual tool use', 'https://arxiv.org/pdf/2608.11715'),
    ('Language confusion in LLMs (Marchisio et al., EMNLP 2024)', 'https://arxiv.org/html/2406.20052v3'),
    ('Translation artifacts in cross-lingual transfer (Artetxe et al., EMNLP 2020)', 'https://aclanthology.org/2020.emnlp-main.618'),
    ('Translation tax / English-source cue inheritance', 'https://arxiv.org/pdf/2605.07093'),
    ('RomanLens: latent romanization in LLMs', 'https://arxiv.org/html/2502.07424v2'),
    ('RomanSetu (ACL 2024)', 'https://aclanthology.org/2024.acl-long.833'),
    ('WorldBench', 'https://arxiv.org/html/2609.01056'),
    ('MAPS: multilingual agent performance and security', 'https://arxiv.org/html/2505.15935v3'),
    ('PolyWorkBench', 'https://arxiv.org/pdf/2607.06008'),
    ('Infinite agentic loops', 'https://arxiv.org/pdf/2607.01641'),
    ('MAST: why multi-agent LLM systems fail', 'https://arxiv.org/pdf/2503.13657'),
    ('SciExplore (search inertia)', 'https://arxiv.org/pdf/2607.20926'),
    ('OfficeBench', 'https://arxiv.org/abs/2407.19056'),
]
for name, url in SRC:
    story.append(Paragraph(f'{name} &mdash; <link href="{url}"><font color="#2d5a9b">{url}</font></link>', SMALL))


def footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16*mm, 9*mm, 'OfficeBench Bangla vs English - findings (104-pair snapshot)')
    canvas.drawRightString(A4[0] - 16*mm, 9*mm, f'page {doc_.page}')
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=16*mm, rightMargin=16*mm,
                        title='OfficeBench in Bangla vs English: findings', author='analysis')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
