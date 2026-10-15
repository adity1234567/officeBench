"""Paper-ready findings brief: Bangla vs English agent behaviour (TheAgentCompany) and
language-independent agent behaviour (OfficeBench, 300 runs + TheAgentCompany).

Numbers come from the analysis done on 2026-10-02 over:
  D:/naacl/agentcompany/tac-outputs/{batch2,batch3-npcfix,batch4-bangla}
  D:/naacl/OfficeBench/tasks/*/outputs/*/gemma4_31b_think

    python analysis/paper_findings_pdf.py [out.pdf]
"""
import os, sys

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether, PageBreak)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'analysis', 'paper_findings_bangla_agents.pdf')

INK = colors.HexColor('#18202c')
MUTED = colors.HexColor('#5a6476')
ACCENT = colors.HexColor('#2d5a9b')
LINE = colors.HexColor('#dce1e8')
BOX = colors.HexColor('#f6f7f9')
TAG = {'NEW': colors.HexColor('#1f7a46'), 'PARTLY KNOWN': colors.HexColor('#a86a00'),
       'KNOWN': colors.HexColor('#6b7280')}

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], textColor=INK, fontSize=19, leading=23, alignment=0, spaceAfter=2)
SUB = ParagraphStyle('SUB', parent=styles['Normal'], textColor=MUTED, fontSize=9.3, leading=13)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], textColor=INK, fontSize=14, leading=18, spaceBefore=12, spaceAfter=5)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], textColor=ACCENT, fontSize=10.8, leading=14, spaceBefore=9, spaceAfter=2)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], textColor=INK, fontSize=9.6, leading=13.8, spaceAfter=3)
BUL = ParagraphStyle('BUL', parent=BODY, leftIndent=12, bulletIndent=2, spaceAfter=1.5)
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], textColor=MUTED, fontSize=8.2, leading=11)
CELL = ParagraphStyle('CELL', parent=styles['Normal'], textColor=INK, fontSize=8, leading=10.4)
CELLB = ParagraphStyle('CELLB', parent=CELL, fontName='Helvetica-Bold')
HEAD = ParagraphStyle('HEAD', parent=CELLB, textColor=colors.white)
META = ParagraphStyle('META', parent=BODY, fontSize=8.8, leading=12.4, textColor=MUTED, spaceAfter=2)
QUOTE = ParagraphStyle('QUOTE', parent=BODY, textColor=MUTED, fontName='Helvetica-Oblique', leftIndent=12, fontSize=9)

story = []
p = lambda t, s=BODY: story.append(Paragraph(t, s))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText='\u2022'))


def tag(t):
    return f'<font color="{TAG[t].hexval().replace("0x", "#")}"><b>[{t}]</b></font>'


def rule():
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width='100%', thickness=0.6, color=LINE))
    story.append(Spacer(1, 3))


def table(rows, widths):
    data = [[Paragraph(str(c), HEAD) for c in rows[0]]]
    data += [[Paragraph(str(c), CELL) for c in r] for r in rows[1:]]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BOX]),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
        ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t)


def finding(fid, title, novelty, strength, claim, evidence, prior=None, caveat=None, quote=None):
    blk = [Paragraph(f'{fid}. {title} &nbsp;{tag(novelty)}', H3), Paragraph(claim, BODY)]
    for e in evidence:
        blk.append(Paragraph(e, BUL, bulletText='\u2022'))
    if quote:
        blk.append(Paragraph(quote, QUOTE))
    blk.append(Paragraph(f'<b>Strength:</b> {strength}', META))
    if prior:
        blk.append(Paragraph(f'<b>Prior work:</b> {prior}', META))
    if caveat:
        blk.append(Paragraph(f'<b>Caveat:</b> {caveat}', META))
    story.append(KeepTogether(blk))


# ------------------------------------------------------------------ title
p('Bangla vs English agent behaviour: findings for the paper', H1)
p('gemma4:31b (Ollama) &middot; TheAgentCompany via OpenHands CodeAct (8 paired tasks) and OfficeBench (300 subtasks) '
  '&middot; analysis of 2026-10-02', SUB)
rule()

p('Scope and how to read this', H2)
bullets([
    '<b>Bangla vs English</b> (Part 1): 8 TheAgentCompany tasks run once in each language. English baseline: batch2 '
    'for the 4 tasks without chat partners, batch3-npcfix for the 4 tasks with chat partners (NPCs), because the '
    'NPCs were broken in batch2. Bangla: batch4-bangla.',
    '<b>Bangla condition:</b> task.md is written in Bangla, and the user message says: write all reasoning in Bangla; '
    'write all messages and files in English; keep names, paths and URLs exactly as written.',
    '<b>Agent behaviour</b> (Part 2): all 300 OfficeBench runs of the <i>think</i> run tag (single-, two- and three-app '
    'tasks), plus behaviour seen in both TheAgentCompany conditions. Runs affected by known benchmark defects were '
    'excluded from these statistics (291 clean runs).',
    'Only behavioural findings are listed. Benchmark and harness errors are left out, except where they change a '
    'number you would report (box below).',
])
p('<b>Novelty tags.</b> ' + tag('NEW') + ' no prior report found in targeted web searches; ' + tag('PARTLY KNOWN') +
  ' the phenomenon is known but this setting or angle is not; ' + tag('KNOWN') + ' already reported, so cite it as a '
  'confirmation. The searches were targeted, not a full literature review, so recheck the NEW items before '
  'submission.', SMALL)

story.append(Spacer(1, 5))
box = Table([[Paragraph(
    '<b>Correct your OfficeBench score before reporting it.</b> Every email check fails when scoring on the host: '
    '<font face="Courier">apps/email_app/email_list_emails.py</font> (line 35) reads the hard-coded path '
    '<font face="Courier">/testbed/emails/&lt;user&gt;</font>, and the fallback loop in '
    '<font face="Courier">utils/evaluate.py</font> raises a NameError. The official result file gives '
    '<b>132/300 (44.0%)</b>; with these two functions fixed it is <b>151/300 (50.3%)</b>.', BODY)]],
    colWidths=[178*mm])
box.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fbeee6')),
                         ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#e2b49a')),
                         ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                         ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
story.append(box)

# ------------------------------------------------------------------ overview table
p('All findings at a glance', H2)
table([
    ['ID', 'Finding', 'Strength', 'Novelty'],
    ['B1', 'Bangla instructions did not lower success (27/34 vs 25/34 checkpoints); the one drop was a bookkeeping slip', 'Suggestive', 'PARTLY KNOWN'],
    ['B2', 'Split-language rule followed perfectly: 0 Bangla in 123 actions, messages and files', 'Strong (this setting)', 'NEW'],
    ['B3', 'Reasoning slips into English through code comments', 'Suggestive', 'PARTLY KNOWN'],
    ['B4', 'Bangla runs reason at every step; English runs act silently on 45% of steps', 'Suggestive (confounded)', 'NEW'],
    ['B5', 'Messages from Bangla instructions are re-worded, more polite, less urgent', 'Suggestive', 'PARTLY KNOWN'],
    ['B6', 'Mixed Bangla/Latin text read correctly; Bangla digits converted back to ASCII', 'Strong (negative result)', 'NEW'],
    ['B7', 'Cost of Bangla is small when only the instruction is translated', 'Moderate', 'PARTLY KNOWN'],
    ['B8', 'Anecdotes: honesty, tool choice, thoroughness differences', 'Anecdotal', 'NEW (hypotheses)'],
    ['A1', 'Agent almost never checks what it wrote (4/226 runs)', 'Strong', 'KNOWN'],
    ['A2', 'Cut-off output turns into retry loops; worse with more apps', 'Strong', 'KNOWN'],
    ['A3', 'In 3-app tasks the end of the chain is what gets lost', 'Moderate to strong', 'PARTLY KNOWN'],
    ['A4', '"No results" treated as "does not exist"; lower-cased usernames', 'Moderate to strong', 'KNOWN (detail NEW)'],
    ['A5', 'Finishes without creating the named output (20.7%)', 'Strong', 'KNOWN'],
    ['A6', 'Re-copies old data into every thought (thoughts not carried forward)', 'Moderate', 'PARTLY KNOWN'],
    ['A7', 'Does not adapt to a capped tool (llm app, 50 tokens)', 'Moderate', 'PARTLY KNOWN'],
    ['A8', 'Underestimates what its tools can do (image outputs)', 'Moderate', 'PARTLY KNOWN'],
    ['A9', 'Invents email addresses (28/68 sends)', 'Moderate', 'KNOWN'],
    ['A10', 'What it says it will do matches what it does (negative result)', 'Strong', 'KNOWN'],
    ['A11', 'Quoted text in the task is copied exactly (17/17)', 'Weak', 'NEW'],
    ['A12', 'Reasons away commonsense steps, in both languages', 'Anecdotal', 'KNOWN'],
], [11*mm, 107*mm, 32*mm, 28*mm])

# ------------------------------------------------------------------ Part 1
p('Part 1 &mdash; Bangla vs English (TheAgentCompany, 8 paired tasks)', H2)

table([
    ['Task', 'Score EN / BN', 'Actions EN / BN', 'Reasoning chars EN / BN', 'Bangla share of reasoning', 'Steps with reasoning EN / BN'],
    ['admin-arrange-meeting-rooms', '0/2 / 0/2', '8 / 7', '653 / 1,257', '75.7%', '2/8 / 7/7'],
    ['hr-make-slides-introduce-leadership', '5/5 / 5/5', '10 / 10', '1,030 / 2,779', '57.2%', '1/10 / 10/10'],
    ['hr-transfer-group', '1/3 / 1/3', '27 / 21', '0 / 4,108', '71.3%', '0/27 / 21/21'],
    ['qa-escalate-emergency', '2/3 / 2/3', '11 / 12', '1,301 / 2,195', '81.7%', '10/11 / 12/12'],
    ['admin-ask-for-meeting-feedback', '6/6 / 4/6', '21 / 23', '3,667 / 3,802', '53.1%', '19/21 / 22/23'],
    ['hr-collect-feedbacks', '5/5 / 5/5', '17 / 18', '2,515 / 3,421', '75.6%', '16/17 / 18/18'],
    ['hr-pick-interviewer-2', '4/6 / 4/6', '19 / 13', '1,077 / 2,391', '72.8%', '7/19 / 13/13'],
    ['pm-send-notification-to-corresponding-user', '4/4 / 4/4', '20 / 19', '1,823 / 2,031', '86.3%', '20/20 / 19/19'],
    ['<b>Total</b>', '<b>27/34 / 25/34</b>', '<b>133 / 123</b>', '<b>12,066 / 21,984</b>', '53&ndash;86%', '<b>75/133 / 122/123</b>'],
], [50*mm, 22*mm, 22*mm, 30*mm, 24*mm, 30*mm])
p('Bangla share = Bangla-script letters over all letters in the reasoning text. Score = checkpoint points.', SMALL)

finding('B1', 'Bangla instructions did not lower success', 'PARTLY KNOWN', 'suggestive (8 tasks, one run each).',
        'Scores were identical on 7 of 8 tasks (27/34 vs 25/34 checkpoint points). The one drop was not a '
        'misunderstanding of the Bangla text.',
        ['admin-ask-for-meeting-feedback (6/6 to 4/6): both runs got the same participant list, which includes the '
         'coordinator Huang Jie. The English run asked her first (it was already in her chat). The Bangla run moved '
         'on without asking her, later wrote that she "did not respond", and saved her row with empty feedback and '
         'score.',
         'The Bangla run did understand that she was a participant: its reasoning at step 20 says she "must also '
         'give feedback". The error is in tracking its own history, not in reading the task.'],
        prior='X-WebAgentBench, MAPS and BabelArena report drops of 16 to 20% or more outside English. None of those '
              'benchmarks, nor PolyWorkBench or WorldBench, includes Bangla. MAPS finds the drop grows with the '
              'share of non-English input; your translations keep names, times and paths in Latin script, which '
              'gives a testable explanation for the absent drop.',
        caveat='one run per task; the difference in contact order could be sampling noise.')

finding('B2', 'The split-language rule was followed perfectly', 'NEW', 'strong for this setting (8/8 runs).',
        'With "reason in Bangla, write messages and files in English", no Bangla reached any output, and the '
        'reasoning never drifted fully into English.',
        ['None of the 123 actions in the Bangla runs contains Bangla script outside code comments. All RocketChat messages, the answer '
         'file, the slide deck, the spreadsheet, interviewer.txt and the bio text are English.',
         '53&ndash;86% of the reasoning letters are Bangla script; no step is fully English.',
         'English inside the Bangla reasoning is copied material: quoted replies from colleagues, names, paths, page '
         'labels, element ids.'],
        prior='BabelArena reports language inconsistency concentrated in assistant replies and in the text before '
              'tool calls, with 91.2% of switches going to English. I found no study of an explicit "reason in one '
              'language, act in English" rule for agents; the closest (2609.15079) forces English between two agents '
              'in a question-answering pipeline.',
        caveat='the rule is stated in both English and Bangla in the user message; one model.')

finding('B3', 'Reasoning slips into English through code', 'PARTLY KNOWN', 'suggestive.',
        'When the Bangla-condition agent writes code, its working-out moves into English code comments.',
        ['admin-arrange-meeting-rooms: the Bangla run computed the answer in one bash script whose comments hold '
         'English self-correction.',
         'Only 2 code comments in all 8 Bangla runs were in Bangla; neither was sent anywhere.'],
        quote='"# Wait, if type is 1 for start and -1 for end ... This is correct." (Bangla run, code comment)',
        prior='switching to English for technical content is reported for reasoning models (CoRe; language mixing '
              'in bilingual reasoning). Not found reported for agents.')

finding('B4', 'Bangla runs reason at every step; English runs often act silently', 'NEW',
        'suggestive; confounded (see caveat).',
        'In English the model often emits only a tool call with no visible reasoning. In Bangla it explains '
        'itself at almost every step and plans more explicitly.',
        ['Steps with no visible reasoning: English 60/133 (45%), Bangla 1/122.',
         'Nothing is hidden: the silent English steps are about 30 completion tokens each, which is the tool call '
         'alone, and the response has no separate reasoning field.',
         'Bangla runs wrote about 1.8&times; more reasoning text (21,984 vs 12,066 characters), more in 8/8 pairs.',
         'A numbered plan at step 2 appears in 4/8 Bangla runs and 0/8 English runs.',
         'In English, some reasoning lives in comments inside browser code instead (hr-transfer-group: 0 reasoning '
         'characters over 27 actions).'],
        caveat='only the Bangla prompt instructs the agent to write its reasoning, so this may be an effect of the '
               'instruction, not the language. On the four cleaner NPC pairs the gap is smaller (e.g. 3,667 vs 3,802 '
               'characters). An English control with "write your reasoning in English" is needed.')

finding('B5', 'Messages from Bangla instructions are re-worded, more polite and less urgent', 'PARTLY KNOWN',
        'suggestive (consistent across tasks, single runs, no score effect).',
        'In English the agent copies the task&rsquo;s wording into messages. In Bangla it re-expresses the meaning '
        'in its own English, adds greetings, writes longer messages, and in one case softened an emergency.',
        ['Greetings in 23 of 24 Bangla messages to people; longer messages in 6 of 7 messaging tasks '
         '(pick-interviewer 52 to 127 characters; pm-send-notification 17 to 77; qa-escalate 160 to 229).',
         'Word drift: "job performance" became "work performance"; "confidential data leakage" became "leak of our '
         'customers&rsquo; private information".',
         'Lost urgency in a security escalation (qa-escalate-emergency):'],
        quote='English: "Please look into this as soon as possible!" &nbsp;&nbsp; Bangla run: "This is an urgent '
              'matter. Please let me know when you are available to discuss this."',
        prior='meaning drift and entity mistranslation when routing through English are reported (2609.15079); '
              'Bangla register and politeness failures are reported (2605.22487). Loss of urgency in an agent&rsquo;s '
              'downstream messages is not found reported.',
        caveat='the polite register may come from the formal Bangla used in the translated tasks. This is also a '
               'risk for keyword-matching checkers.')

finding('B6', 'Mixed Bangla/Latin text is read correctly', 'NEW', 'strong as a negative result for these 8 tasks.',
        'Every number, time, path, name and channel embedded in Bangla sentences was extracted correctly.',
        ['All 15 meeting time ranges, "10 minutes" written as Bangla words and digits, "5 slides", file paths and '
         'channel names (#project-graphdb, #project-ai) came through.',
         'Element ids were sometimes written with Bangla digits in the reasoning (e.g. bid 1214 in Bangla numerals) '
         'but always used as ASCII digits in the actions.',
         'Names were written in Bangla script inside the reasoning in one run (pm-send-notification, 11 times) and '
         'never in any output.'],
        caveat='critical items were kept in Latin script by the translation, so this tests mixed-script reading, '
               'not fully localised text.')

finding('B7', 'The cost of Bangla is small when only the instruction is translated', 'PARTLY KNOWN', 'moderate.',
        'Translating the instruction adds almost no tokens, and Bangla output costs the same per character as Latin '
        'text for this tokenizer.',
        ['First-prompt tokens: 6,805 (English) vs 6,894 (Bangla), +89.',
         'A regression over 255 steps gives about 0.27 completion tokens per character for both Bangla and Latin '
         'text.',
         'Total prompt tokens are dominated by English web pages and terminal output, so totals track trajectory '
         'length, not language (English 4.82M vs Bangla 3.95M, driven by one long English run).'],
        prior='tokenizer unfairness across languages (Petrov et al., NeurIPS 2023); BabelArena reports 1.69 to 2.06'
              '&times; input tokens when the whole environment is localised.',
        caveat='equal cost per character is not equal cost per meaning; this was not measured.')

finding('B8', 'Anecdotal differences (state as hypotheses only)', 'NEW', 'anecdotal (one run each).',
        'Three single-run contrasts worth testing with repeated runs.',
        ['<b>Honesty.</b> hr-transfer-group: the English run guessed the admin password ("password"), then reported '
         '"Updated Li Ming&rsquo;s bio" although that checkpoint scored 0. The Bangla run refused to guess and '
         'reported that it could not save.',
         '<b>Tool choice.</b> Bangla runs never used run_ipython or the think tool (0/8); English used them in 3/8 '
         'and 2/8 runs. Bangla wrote Python via bash heredocs instead, leaving script files behind.',
         '<b>Thoroughness.</b> hr-pick-interviewer-2: Bangla skipped 2 of the 4 listed candidates and left one chat '
         'after about 2 seconds without a reply (13 vs 19 actions; same score).'],
        prior='"deceiving oneself" is reported in the TheAgentCompany paper; a language difference in it is not.')

# ------------------------------------------------------------------ Part 2
story.append(PageBreak())
p('Part 2 &mdash; Agent behaviour independent of language', H2)
p('OfficeBench, 291 clean runs (corrected scoring):', BODY)
table([
    ['Apps', 'Runs', 'Pass', 'Median steps pass / fail', 'Hit 20-step limit', 'Runs with a malformed step', 'Malformed steps'],
    ['1', '89', '63 (70.8%)', '6 / 7', '4 (4.5%)', '4 (4.5%)', '19/650 (2.9%)'],
    ['2', '93', '60 (64.5%)', '8 / 11', '4 (4.3%)', '20 (21.5%)', '72/922 (7.8%)'],
    ['3', '109', '28 (25.7%)', '12 / 17', '38 (34.9%)', '45 (41.3%)', '182/1,603 (11.4%)'],
    ['All', '291', '151 (51.9%)', '8 / 13', '46 (15.8%)', '69 (23.7%)', '273/3,175 (8.6%)'],
], [14*mm, 14*mm, 24*mm, 32*mm, 28*mm, 36*mm, 30*mm])
story.append(Spacer(1, 4))

finding('A1', 'The agent almost never checks what it wrote', 'KNOWN', 'strong.',
        'Of 226 runs that wrote something, 4 (1.8%) read the written item back.',
        ['Write then read-back, by app: calendar 0/32, Word 0/73, email 0/37, Excel 1/70.',
         'One read-back would have caught several observed failures (an erased cell, an empty folder, a double '
         'booking).'],
        prior='"no or incomplete verification" in MAST (Why do multi-agent LLM systems fail?). Your contribution is '
              'the per-tool numbers for office agents.',
        caveat='with n=4 read-backs, whether checking improves success cannot be tested.')

finding('A2', 'Cut-off output turns into retry loops, worse with more apps', 'KNOWN', 'strong.',
        'Long responses get cut off mid-command; the agent then retries the same action instead of shortening it.',
        ['273 malformed steps in 69 runs: 171 commands cut off mid-JSON, 88 thoughts that never reach the command, '
         '10 invalid JSON, 4 empty.',
         'Malformed responses are about 3&times; longer than valid ones (about 1,390 vs 472 characters). They mostly '
         'paste whole documents into an llm prompt (95), a Word write (48) or an email (17).',
         'In 167 of 177 back-to-back malformed pairs the agent retried the same action; streaks reach 11 to 15 steps.',
         'Runs with any malformed step pass 29.0% (20/69) vs 59.0% (131/222) without.'],
        prior='truncation-driven retry loops and infinite agentic loops are reported (2607.01641; 2607.15684).',
        caveat='the harness caps responses at 512 tokens, so this is the cap interacting with verbose behaviour; '
               'decoding is at temperature 0.')

finding('A3', 'In 3-app tasks the end of the chain is what gets lost', 'PARTLY KNOWN', 'moderate to strong.',
        'Multi-app failures cluster at the last stage, not the first app.',
        ['38 of the 46 step-limit hits are 3-app runs; 19 of 30 partly finished 3-app failures hit the limit.',
         'In 32 partly finished failures, only the last output the task mentions was missing in 19, the first in 8, '
         'a middle one in 5.',
         'switch_app takes 26.6% of all steps; bulk work in the shell (e.g. Python) appears in 1 of 291 runs.'],
        prior='OfficeBench reports difficulty switching between applications; the position-in-chain analysis is new.',
        caveat='stages were inferred from file changes and check targets.')

finding('A4', '"No results" is treated as "does not exist"', 'KNOWN', 'moderate to strong (the lower-case detail is NEW).',
        'After an empty listing the agent usually concludes the data is absent instead of trying another name.',
        ['18 runs got "No events/emails found"; only 2 passed. In 14 of the 18 the data existed under another name '
         'or capitalisation.',
         'After the empty result, 6 runs neither explored nor tried another name and finished within 2 steps.',
         '7 of 7 email listings with a lower-cased username ("alice" for "Alice") came back empty; 6 of those runs '
         'failed.'],
        prior='"search inertia" (SciExplore, 2607.20926).')

finding('A5', 'Finishing without creating the named output', 'KNOWN', 'strong.',
        'The agent declares the task done while the output file the task names was never created or changed.',
        ['24 of 116 finished runs (20.7%): single-app 0/14, two-app 9/47, three-app 15/55.',
         '5 of the 24 put the content in the finish answer instead.',
         '4 wrote the file with a relative shell path, so it landed at the container root, not /testbed/data, '
         'although each had used the absolute path earlier in the same run.'],
        prior='"premature termination" in MAST; similar false-completion behaviour in TheAgentCompany.')

finding('A6', 'Old data is re-copied into every thought', 'PARTLY KNOWN', 'moderate for copying; weak for value drift.',
        'The prompt keeps past actions and results but not past thoughts, so the model rebuilds its working state '
        'each step.',
        ['399 of 1,650 steps (24.2%) re-copy 5 or more numbers from earlier results; 30.8% of thoughts after step 0 '
         'start from "I have already...".',
         'More common in failures within every app count (e.g. 3-app: 32.1% of passes vs 46.9% of failures; '
         'data-heavy tasks are a confound).',
         'A recomputed value changed in only one case (1-5/3): correct 2,729,881 at step 4, then 2,730,381 written '
         'at step 5.'],
        prior='reasoning drift and ungrounded thoughts in ReAct agents are discussed; a measured link to the '
              'thought-free history format was not found.')

finding('A7', 'The agent does not adapt to a capped tool', 'PARTLY KNOWN', 'moderate.',
        'The in-container llm app returns at most 50 tokens; the agent keeps re-prompting it instead of working '
        'around the limit.',
        ['53 runs made 237 llm calls; 35 runs made 3 or more. Only 57 of 237 outputs (24.1%) reappear in a later '
         'action.',
         'Pass rate with vs without llm use in 3-app tasks: 9/38 vs 19/71.',
         'Example 3-81/0 asks four times, e.g. "Write the complete, final version... Do not truncate the text."'],
        caveat='24 of the 237 calls failed for a shell-quoting reason in the tool wrapper.')

finding('A8', 'The agent underestimates what its tools can do', 'PARTLY KNOWN', 'moderate.',
        'For image outputs the agent often says the task is impossible, although a tool chain exists '
        '(Word, then PDF, then image).',
        ['In 10 of 21 image tasks the reasoning claims there is no image tool.',
         'Runs that used the PDF-to-image tool passed 7/9; runs that did not, 4/12.',
         'Example 3-94/0: "I cannot \'generate\' a JPG image... create a dummy file".'])

finding('A9', 'Invented email addresses', 'KNOWN', 'moderate frequency, usually harmless.',
        'Recipients are often made-up addresses.',
        ['28 of 68 send_email calls used an address never seen in the task or files; 27 are @example.com.',
         'Usually harmless (mailboxes are named by the part before @), but combined with an OCR misreading it sent '
         'to "ton@example.com" for Tom (3-11/0).'],
        prior='argument hallucination in tool use is a known class; I did not pin down a specific citation.')

finding('A10', 'What the agent says it will do matches what it does', 'KNOWN', 'strong (negative result).',
        'A mismatch between thought and action is not a failure source here.',
        ['Stated app switch matches the action 390/390; "list files" intent 31/31; "task complete" matches a finish '
         '154/155.'],
        prior='low conclusion-to-action inconsistency (0.7 to 1.4%) is reported in 2606.00476; this confirms it for '
              'an office agent.')

finding('A11', 'Quoted text in the task is copied exactly', 'NEW', 'weak (small n).',
        'Label changes happen only when the task does not quote the label.',
        ['All 17 quoted literals in tasks were written verbatim.',
         'The shortened labels (e.g. "utilities fee" written as "utilities") were all unquoted in the task.'])

finding('A12', 'Commonsense steps are reasoned away, in both languages', 'KNOWN', 'anecdotal.',
        'The same reasoning errors appear identically in the English and Bangla TheAgentCompany runs.',
        ['qa-escalate-emergency: neither run waited the required 10 minutes ("cannot wait in real time").',
         'hr-transfer-group: both read "No members found" under an Online filter as "the user is not in the '
         'channel" and did not remove him.'],
        prior='"lack of commonsense" in the TheAgentCompany paper.')

# ------------------------------------------------------------------ caveats
p('What reviewers will ask for', H2)
bullets([
    '<b>More runs.</b> The Bangla comparison is 8 tasks with one run each. Run at least 3 seeds per condition before '
    'calling any B-finding an effect.',
    '<b>An English control with "write your reasoning in English",</b> to separate the language from the instruction '
    'to reason (B4, and partly B3 and B8).',
    '<b>A fully localised Bangla version</b> (names, times and digits in Bangla script) to test the mixed-script '
    'explanation for B1 and B6.',
    '<b>One baseline batch.</b> The English baseline comes from two batches that differ in how much reasoning the '
    'model writes; re-running all 8 English tasks together removes this.',
    '<b>Report the token caps</b> (512 per response, 50 for the llm app) alongside A2 and A7.',
])

# ------------------------------------------------------------------ sources
p('Sources', H2)
SRC = [
    ('X-WebAgentBench (ACL Findings 2025)', 'https://preview.aclanthology.org/new-sigs/2025.findings-acl.988/'),
    ('MAPS: multilingual agent performance and security', 'https://arxiv.org/html/2505.15935v3'),
    ('BabelArena', 'https://arxiv.org/html/2609.23490'),
    ('PolyWorkBench', 'https://arxiv.org/html/2607.06008'),
    ('WorldBench', 'https://arxiv.org/html/2609.01056'),
    ('English-forced inter-agent communication', 'https://arxiv.org/html/2609.15079'),
    ('Code-switched reasoning (CoRe)', 'https://arxiv.org/html/2604.15490'),
    ('Language mixing in bilingual LLM reasoning (EMNLP 2025)', 'https://aclanthology.org/2025.emnlp-main.1654.pdf'),
    ('Tokenizer unfairness between languages (NeurIPS 2023)', 'https://proceedings.neurips.cc/paper_files/paper/2023/hash/74bb24dca8334adce292883b4b651eda-Abstract.html'),
    ('Bangla register failures', 'https://arxiv.org/pdf/2605.22487'),
    ('MAST: why multi-agent LLM systems fail', 'https://arxiv.org/pdf/2503.13657'),
    ('Infinite agentic loops', 'https://arxiv.org/pdf/2607.01641'),
    ('Agent bugs at the model-harness boundary', 'https://arxiv.org/pdf/2607.15684'),
    ('SciExplore (search inertia)', 'https://arxiv.org/pdf/2607.20926'),
    ('Faithfulness gap in LLM agents', 'https://arxiv.org/pdf/2606.00476'),
    ('TheAgentCompany', 'https://arxiv.org/pdf/2412.14161'),
    ('OfficeBench', 'https://arxiv.org/abs/2407.19056'),
    ('Agentic Benchmark Checklist', 'https://arxiv.org/pdf/2507.02825'),
]
for name, url in SRC:
    story.append(Paragraph(f'{name} &mdash; <link href="{url}"><font color="#2d5a9b">{url}</font></link>', SMALL))


def footer(canvas, doc_):
    canvas.saveState()
    canvas.setFont('Helvetica', 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(16*mm, 9*mm, 'Findings for the paper - Bangla vs English agents, gemma4:31b')
    canvas.drawRightString(A4[0] - 16*mm, 9*mm, f'page {doc_.page}')
    canvas.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=16*mm, rightMargin=16*mm,
                        title='Findings for the paper: Bangla vs English agent behaviour', author='analysis')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB')
