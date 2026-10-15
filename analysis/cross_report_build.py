"""Cross-benchmark failure report (synthesis of the four FAILURE_ANALYSIS PDFs)."""
import os, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether, NextPageTemplate, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

FIG = sys.argv[1]
OUT = sys.argv[2]

F = 'C:/Windows/Fonts/'
pdfmetrics.registerFont(TTFont('Arial', F + 'arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', F + 'arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Italic', F + 'ariali.ttf'))
pdfmetrics.registerFont(TTFont('Arial-BoldItalic', F + 'arialbi.ttf'))
from reportlab.lib.fonts import addMapping
addMapping('Arial', 0, 0, 'Arial'); addMapping('Arial', 1, 0, 'Arial-Bold')
addMapping('Arial', 0, 1, 'Arial-Italic'); addMapping('Arial', 1, 1, 'Arial-BoldItalic')

INK = colors.HexColor('#1b1b1a'); INK2 = colors.HexColor('#52514e'); MUTED = colors.HexColor('#8a8984')
RULE = colors.HexColor('#d9d8d3'); BAND = colors.HexColor('#f3f2ee'); ACCENT = colors.HexColor('#2a78d6')
OBS_C, INT_C, HYP_C = '#1b6fbf', '#8a5a00', '#7a3fa0'

ss = {
    'title': ParagraphStyle('title', fontName='Arial-Bold', fontSize=22, leading=27, textColor=INK, spaceAfter=6),
    'subtitle': ParagraphStyle('subtitle', fontName='Arial', fontSize=12, leading=16, textColor=INK2),
    'h1': ParagraphStyle('h1', fontName='Arial-Bold', fontSize=15, leading=19, textColor=INK, spaceBefore=6, spaceAfter=6),
    'h2': ParagraphStyle('h2', fontName='Arial-Bold', fontSize=11.5, leading=15, textColor=INK, spaceBefore=8, spaceAfter=4),
    'h3': ParagraphStyle('h3', fontName='Arial-Bold', fontSize=9.8, leading=13, textColor=INK, spaceBefore=6, spaceAfter=2),
    'body': ParagraphStyle('body', fontName='Arial', fontSize=9.2, leading=13, textColor=INK, spaceAfter=4),
    'bullet': ParagraphStyle('bullet', fontName='Arial', fontSize=9.2, leading=13, textColor=INK, leftIndent=11,
                             bulletIndent=2, spaceAfter=2),
    'cap': ParagraphStyle('cap', fontName='Arial', fontSize=8, leading=10.5, textColor=INK2, spaceBefore=2, spaceAfter=8),
    'cell': ParagraphStyle('cell', fontName='Arial', fontSize=7.8, leading=9.8, textColor=INK),
    'cellb': ParagraphStyle('cellb', fontName='Arial-Bold', fontSize=7.8, leading=9.8, textColor=INK),
    'small': ParagraphStyle('small', fontName='Arial', fontSize=8, leading=10.5, textColor=INK2),
    'toc1': ParagraphStyle('toc1', fontName='Arial-Bold', fontSize=9.5, leading=14, leftIndent=0),
    'toc2': ParagraphStyle('toc2', fontName='Arial', fontSize=9, leading=12.5, leftIndent=14, textColor=INK2),
    'box': ParagraphStyle('box', fontName='Arial', fontSize=9, leading=12.6, textColor=INK),
}


def tag(kind):
    c = {'O': OBS_C, 'I': INT_C, 'H': HYP_C}[kind]
    t = {'O': 'OBSERVED', 'I': 'INTERPRETATION', 'H': 'HYPOTHESIS'}[kind]
    return f'<font name="Arial-Bold" size="6.8" color="{c}">[{t}]</font> '


O, I, H = tag('O'), tag('I'), tag('H')


class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ('h1', 'h2'):
            lvl = 0 if f.style.name == 'h1' else 1
            key = f'k{id(f)}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(f.getPlainText(), key, level=lvl, closed=False)
            self.notify('TOCEntry', (lvl, f.getPlainText(), self.page, key))


def on_page(c, d):
    c.saveState()
    c.setFont('Arial', 7.5); c.setFillColor(MUTED)
    c.drawString(18 * mm, 10 * mm, 'Cross-benchmark failure analysis · English vs Bangla agents')
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f'{d.page}')
    c.setStrokeColor(RULE); c.setLineWidth(0.5)
    c.line(18 * mm, 13.5 * mm, A4[0] - 18 * mm, 13.5 * mm)
    c.restoreState()


def on_cover(c, d):
    c.saveState()
    c.setFillColor(ACCENT); c.rect(0, A4[1] - 9 * mm, A4[0], 9 * mm, fill=1, stroke=0)
    c.restoreState()


doc = Doc(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=17 * mm, bottomMargin=18 * mm,
          title='Cross-Benchmark Failure Analysis: English vs Bangla Agents',
          author='Failure analysis synthesis', subject='OfficeBench, tau2-bench, WorkBench, TheAgentCompany')
fr = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='f')
doc.addPageTemplates([PageTemplate('cover', [fr], onPage=on_cover), PageTemplate('body', [fr], onPage=on_page)])
W = doc.width

story = []
P = lambda t, s='body': Paragraph(t, ss[s])


def B(t):
    story.append(Paragraph(t, ss['bullet'], bulletText='•'))


def h1(t): story.append(CondPageBreak(60 * mm)); story.append(P(t, 'h1'))
def h2(t): story.append(CondPageBreak(35 * mm)); story.append(P(t, 'h2'))
def h3(t): story.append(P(t, 'h3'))
def para(t): story.append(P(t))


def table(rows, widths, header=1, align_right_from=None, zebra=True, bold_first_col=False):
    data = []
    for r_i, r in enumerate(rows):
        row = []
        for c_i, v in enumerate(r):
            st = ss['cellb'] if (r_i < header or (bold_first_col and c_i == 0)) else ss['cell']
            if align_right_from is not None and c_i >= align_right_from and r_i >= header:
                st = ParagraphStyle('r', parent=st, alignment=2)
            row.append(Paragraph(str(v), st))
        data.append(row)
    t = Table(data, colWidths=[w * W for w in widths], repeatRows=header, hAlign='LEFT')
    sty = [('VALIGN', (0, 0), (-1, -1), 'TOP'), ('TOPPADDING', (0, 0), (-1, -1), 2.6),
           ('BOTTOMPADDING', (0, 0), (-1, -1), 2.6), ('LEFTPADDING', (0, 0), (-1, -1), 4),
           ('RIGHTPADDING', (0, 0), (-1, -1), 4), ('LINEBELOW', (0, header - 1), (-1, header - 1), 0.8, INK2),
           ('LINEBELOW', (0, -1), (-1, -1), 0.6, RULE)]
    if zebra:
        for i in range(header, len(rows)):
            if (i - header) % 2 == 1:
                sty.append(('BACKGROUND', (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(sty))
    story.append(t)


def cap(t): story.append(P(t, 'cap'))


def fig(name, width_frac=1.0, caption=None):
    path = os.path.join(FIG, name)
    from PIL import Image as PI
    w, h = PI.open(path).size
    iw = W * width_frac
    items = [Image(path, width=iw, height=iw * h / w)]
    if caption:
        items.append(P(caption, 'cap'))
    story.append(KeepTogether(items))


def callout(lines, title=None):
    content = []
    if title:
        content.append(Paragraph(f'<b>{title}</b>', ss['box']))
    for l in lines:
        content.append(Paragraph(l, ss['box'], bulletText='•') if not l.startswith('§') else Paragraph(l[1:], ss['box']))
    t = Table([[content]], colWidths=[W])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef4fb')),
                           ('LINEBEFORE', (0, 0), (0, -1), 2.5, ACCENT),
                           ('LEFTPADDING', (0, 0), (-1, -1), 9), ('RIGHTPADDING', (0, 0), (-1, -1), 9),
                           ('TOPPADDING', (0, 0), (-1, -1), 7), ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
    story.append(t); story.append(Spacer(1, 6))


# =============================== COVER ===============================
story.append(Spacer(1, 30 * mm))
story.append(P('Cross-Benchmark Failure Analysis', 'title'))
story.append(P('English vs Bangla LLM agents on OfficeBench, τ²-bench, WorkBench and TheAgentCompany', 'subtitle'))
story.append(Spacer(1, 6 * mm))
story.append(P('Results and analysis · where and why models fail · root causes · trajectory-level comparison · '
               'evidence and recommendations', 'small'))
story.append(Spacer(1, 10 * mm))
table([
    ['', 'OfficeBench', 'τ²-bench', 'WorkBench', 'TheAgentCompany'],
    ['Interaction', 'Single-turn office tasks in a container (≤ 20 steps)', 'Customer-service dialogue with an LLM user simulator',
     'Single-turn function calling against a sandbox DB', 'Long-horizon company tasks (OpenHands) with LLM coworkers'],
    ['Models', 'gemma4:31b, gpt-oss:20b', 'gemma4:31b, gpt-oss:20b', 'gemma4:31b, gpt-oss:20b', 'gemma4:31b'],
    ['Paired tasks', '300 subtasks', '218 (gemma), 149 (gpt-oss), +219 teammate set', '90 (15 × 6 domains)', '23 task-runs (21 tasks)'],
    ['Scoring', 'Benchmark checks on final files (3 scorer defects fixed)', 'DB state, actions, info, device state (reward ≥ 1)',
     'Final DB = ground truth and every call executes', 'Weighted checkpoints; pass = all points'],
    ['Failures analysed by hand', '42 + 25 EN-pass/BN-fail', '40 + 26 EN-pass/BN-fail', 'All 112 failed runs (22 EN-pass/BN-fail)', '8 selected cases'],
], [0.16, 0.21, 0.21, 0.21, 0.21], bold_first_col=True)
story.append(Spacer(1, 10 * mm))
story.append(P('<b>Source material.</b> This report synthesises four failure-analysis reports generated on 2026-10-10 with the same '
               'pipeline (failure_analysis_pipeline.md): OFFICEBENCH_, TAU2_, WORKBENCH_ and TAC_FAILURE_ANALYSIS.pdf. Every number '
               'is transcribed from those reports; nothing was re-run for this synthesis. Where a source report flags a number '
               'as heuristic, provisional or single-annotator, that caveat is carried over.', 'small'))
story.append(Spacer(1, 4 * mm))
story.append(P('<b>Evidence tags.</b> ' + O + 'a count, rate, test or trace excerpt reported in a source. ' + I +
               'a reading of what observed facts mean. ' + H + 'a plausible mechanism not yet confirmed; a follow-up '
               'experiment is proposed for each.', 'small'))
story.append(NextPageTemplate('body'))
story.append(PageBreak())

# =============================== TOC ===============================
story.append(P('Contents', 'title'))
toc = TableOfContents(); toc.levelStyles = [ss['toc1'], ss['toc2']]
story.append(toc)
story.append(PageBreak())

# =============================== EXEC SUMMARY ===============================
h1('Executive summary')
callout([
    O + '<b>Language effects are model- and benchmark-dependent.</b> gemma4:31b is worse in Bangla on OfficeBench '
    '(50.3% → 42.3%, p = 0.003) and τ²-bench (49.5% → 38.1%, p = 0.001), not on WorkBench (81.1% → 82.2%). gpt-oss:20b is '
    '<i>better</i> in Bangla on OfficeBench (28.7% → 35.3%, p = 0.022) and unchanged on τ²-bench and WorkBench. TAC '
    '(23 task-runs) shows 39.1% → 26.1%, not significant (p = 0.25).',
    O + '<b>Most Bangla-only failures are not Bangla agent failures.</b> Of 163 hand-analysed EN-pass/BN-fail cases, only '
    '24 (14.7%) are coded genuine Bangla agent failures (C1). The rest are the user simulator (35), checker or task '
    'ambiguity (22), translation (9), tools/environment (8), general weaknesses that also occur in English (45) and unclear '
    'cases (20).',
    O + '<b>The dominant confound differs by benchmark design:</b> English-only answer checkers on OfficeBench (15 of 42 gemma '
    'cases), the Bangla user simulator on τ²-bench (35 of 66 cases), general model weakness on WorkBench (17 of 22), '
    'run-to-run noise and environment walls on TAC.',
    O + '<b>Removing benchmark-side confounds shrinks every significant gap toward zero:</b> OfficeBench gemma +8.0 → +1.9 pp '
    '(CI [−1.9, 5.6]); τ² gemma +11.5 → +5.8 pp ([−1.9, 12.8]); OfficeBench gpt-oss −6.7 → −3.3 pp ([−7.7, 1.5]); TAC +13.0 '
    '→ 0.0 pp.',
    O + '<b>Two genuine Bangla mechanisms recur across models and benchmarks:</b> (1) entity grounding from a script without '
    'letter case: names written in Bangla script are lower-cased for case-sensitive lookups (OfficeBench: 3 gemma + 6 '
    'gpt-oss cases); (2) re-rendering English values from a Bangla prompt: "Trip" for travelling, "curd" for yogurt, '
    '"08:00 AM" for 8:00, a rolling 7-day window for "last week".',
    O + '<b>Language-independent failure mechanisms dominate absolute failure counts:</b> benchmark defects (31.5% of gemma '
    'English failures on OfficeBench), malformed actions (gpt-oss: 1,671 invalid actions in English on OfficeBench), '
    'wrong tool arguments (40 of 79 gpt-oss failures on WorkBench), unverified empty results, cut-off output loops, '
    'step-budget exhaustion on three-app tasks (gemma 25%, gpt-oss 7.1% in English).',
    I + '<b>Errors that originate early are rarely recovered.</b> Across the traced chains, a grounding or planning error '
    'is followed by a control failure: the empty result is accepted, the same malformed action is retried, the correct '
    'evidence is rejected. The decisive weakness is usually <i>execution-level control</i> (verification and recovery), '
    'not the initial reasoning step alone.',
    H + '<b>gpt-oss’s Bangla advantage on OfficeBench is a format effect, not better reasoning.</b> The Bangla prompt '
    'coincides with fewer invalid actions (1,671 → 955) and fewer built-in tool calls (643 → 99); removing English '
    'format failures symmetrically shrinks the advantage to −3.3 pp (n.s.). Causality needs a format ablation.',
    O + '<b>The two models fail at different layers of the same agent pipeline.</b> gpt-oss:20b fails early, at the '
    'action-format and tool-argument layers (50% of its OfficeBench English failures produce no valid action; 51% of '
    'its WorkBench failures are wrong arguments). gemma4:31b gets past those layers and fails later, on content, step '
    'budget and the language of its answer (8% no-valid-action failures). ' + I + 'Why: each model’s training defaults '
    'collide with a different part of the benchmark interface, and a model that fails early never reaches the later '
    'layers (Section 4.5).',
], title='Key findings')
para('<b>Highest-value actions.</b> (1) Make checkers language-agnostic (normalise Bengali digits, accept Bangla answers, or '
     'state the answer language). (2) Fix the user simulator so it cannot confirm and stop in one turn and must call device '
     'tools. (3) Keep names, literals and digits protected in translation (now done for OfficeBench v2: 298/298 tasks pass '
     'the automatic checks). (4) Add verification and stuck-recovery to the agent loop (retry lookups with case variants, '
     'chunk long writes, change strategy after repeated malformed actions). (5) Run ≥ 3 seeds per cell, because TAC shows '
     'run-to-run variation as large as the language gap.')

# =============================== 0. SCOPE ===============================
h1('0. Data, design and method')
para('All four studies use a <b>paired design</b>: the same task runs once in English and once in Bangla (system prompt and '
     'task translated; tool names, IDs, file names and URLs kept English), at temperature 0, one run per cell. Each paired '
     'task falls into PP (both pass), PF (English pass, Bangla fail), FP (English fail, Bangla pass) or FF (both fail). The '
     'gap is English minus Bangla success; MELR = (EN − BN) / EN. Tests are exact McNemar on discordant pairs, Wilson '
     'intervals for rates and paired bootstrap (4,000 resamples) for gaps; Holm correction is applied within families of '
     'subgroup tests.')
para('Every hand-analysed failure receives a <b>first failure point</b> (the earliest step that, corrected alone, would most likely have '
     'passed), a <b>failure type</b> and one <b>confound class</b> from a shared seven-class scheme, decided by the same decision '
     'tree (translation → simulator → understanding → tool → argument → environment → verification), with an added '
     'Step 0: “is the output already correct for the task as written?”.')
table([
    ['Class', 'Meaning', 'Side of the system'],
    ['C1 Genuine Bangla agent failure', 'The Bangla input led the agent astray; English did not fail this way', 'Agent'],
    ['C2 User simulator / NPC error', 'The Bangla simulated user/coworker stopped early, gave wrong values, replied in English, skipped device actions', 'Benchmark (simulator)'],
    ['C3 Translation / localization', 'The translated text changed the task or a literal; or localized NPC text breaks a check', 'Benchmark (task)'],
    ['C4 Tool / environment', 'A harness, tool or infrastructure fault blocks a valid action', 'Harness'],
    ['C5 Checker / task ambiguity', 'The check rejects a correct outcome (e.g., answer in Bangla script) or the task admits two readings', 'Benchmark (check)'],
    ['C6 General model weakness', 'The same mechanism fails in an English run of the same model', 'Agent (language-independent)'],
    ['C7 Unclear / noise', 'No visible mechanism, or reruns of the same task disagree', '—'],
], [0.27, 0.53, 0.20])
cap('Table 0.1. Confound classes shared by all four analyses. C2 is structurally zero on OfficeBench and WorkBench (no simulated user).')
h3('Outcome categories used in this report')
B('<b>Complete task failure</b>: no required artefact or write exists at the end (e.g., stuck runs, no file, write never called).')
B('<b>Partial success</b>: some checkpoints or sub-goals met (TAC partial points; compound tasks with one part missing).')
B('<b>Inefficient execution</b>: the run wastes its budget on invalid or repeated actions, whether or not it eventually passes.')
B('<b>Incorrect or incomplete output</b>: an artefact or answer exists but its content, format or script is wrong.')
h3('Reliability of the labels')
table([
    ['Benchmark', 'Annotation', 'Agreement'],
    ['OfficeBench', 'Single annotator for the 42 + 25 trace notes; codebook validated on 16 double-coded cases', 'κ = 0.78 primary code, 0.64 side (16 cases)'],
    ['τ²-bench', '46 of 66 notes double-coded and adjudicated; 20 newest single-annotator', 'κ = 0.39 fine confound; 0.71 artefact vs agent'],
    ['WorkBench', 'Annotator, blind second reviewer and adjudicator on every EN-pass/BN-fail case (all Claude models)', 'Confound κ: gemma 0.59, gpt-oss 0.77'],
    ['TAC', 'Single annotator (Claude model), 8 cases', 'Not measured'],
], [0.15, 0.55, 0.30])
cap('Table 0.2. Label provenance. All annotators are LLMs; native-speaker review of translations is pending in WorkBench.')

# =============================== 1. RESULTS ===============================
h1('1. Results and analysis')
h2('1.1 Overall success, English vs Bangla')
table([
    ['Benchmark', 'Model', 'n', 'EN', 'BN', 'Gap (pp) [95% CI]', 'MELR', 'McNemar p'],
    ['OfficeBench', 'gemma4:31b', '300', '50.3%', '42.3%', '+8.0 [3.0, 13.0]', '15.9%', '0.003'],
    ['OfficeBench', 'gpt-oss:20b', '300', '28.7%', '35.3%', '−6.7 [−12.0, −1.3]', '−23.3%', '0.022'],
    ['τ²-bench', 'gemma4:31b', '218', '49.5%', '38.1%', '+11.5 [5.0, 17.4]', '23.1%', '0.001'],
    ['τ²-bench (teammate set)', 'gemma4:31b', '219', '33.8%', '25.1%', '+8.7', '25.7%', '0.034'],
    ['τ²-bench', 'gpt-oss:20b', '149', '38.9%', '39.6%', '−0.7 [−10.7, 8.7]', '−1.7%', '1.000'],
    ['WorkBench', 'gemma4:31b', '90', '81.1%', '82.2%', '−1.1 [−10.0, 7.8]', '−1.4%', '1.000'],
    ['WorkBench', 'gpt-oss:20b', '90', '58.9%', '53.3%', '+5.6 [−5.6, 16.7]', '9.4%', '0.424'],
    ['TAC (latest BN run)', 'gemma4:31b', '23', '39.1%', '26.1%', '+13.0 [0.0, 26.1]', '33.3%', '0.250'],
], [0.20, 0.13, 0.06, 0.08, 0.08, 0.20, 0.10, 0.15], align_right_from=2)
cap('Table 1.1. Success rates by benchmark, model and language. Positive gap = Bangla worse. τ² denominators exclude '
    'infrastructure-error pairs on both sides; gpt-oss retail and banking lost many tasks to provider errors.')
fig('f1_success.png', 1.0, 'Figure 1.1. Success rate of every run. Model differences are larger than language differences: gemma '
    'leads gpt-oss by 21.6 pp (OfficeBench), 10.6 pp (τ², different denominators) and 22.2 pp (WorkBench) in English.')
para(O + 'Three of the seven model-benchmark comparisons show a significant gap, in <b>opposite directions</b>: gemma loses in Bangla '
     'on OfficeBench and τ²-bench; gpt-oss gains in Bangla on OfficeBench. The difference between the two models’ gaps is '
     '+14.7 pp [7.7, 22.3] on OfficeBench and +14.1 pp [2.0, 26.2] on the 149 τ² tasks shared by all four cells, but −6.7 pp '
     '[−20.0, 6.7] on WorkBench.')
para(I + 'A single claim of the form “agents are worse in Bangla” is not supported: the sign of the language effect depends on '
     'the model, and its size depends on which benchmark components (checker, simulator, translation) see the Bangla text.')

h2('1.2 Paired outcomes')
table([
    ['Benchmark · model', 'PP', 'PF (EN only)', 'FP (BN only)', 'FF', 'Discordant balance'],
    ['OfficeBench · gemma', '109', '42', '18', '131', '2.3 : 1 against Bangla'],
    ['OfficeBench · gpt-oss', '61', '25', '45', '169', '1 : 1.8 in favour of Bangla'],
    ['τ²-bench · gemma', '68', '40', '15', '95', '2.7 : 1 against Bangla'],
    ['τ²-bench · gpt-oss', '32', '26', '27', '64', 'balanced'],
    ['WorkBench · gemma', '66', '7', '8', '9', 'balanced'],
    ['WorkBench · gpt-oss', '38', '15', '10', '27', '1.5 : 1 against Bangla (n.s.)'],
    ['TAC · gemma', '6', '3', '0', '14', 'one-directional, 3 pairs'],
], [0.26, 0.08, 0.13, 0.13, 0.08, 0.32], align_right_from=1)
cap('Table 1.2. Paired outcome counts. FF dominates OfficeBench and TAC: most tasks that fail, fail in both languages.')
para(O + 'Flips occur in both directions everywhere except TAC. Even where gemma is significantly worse in Bangla, 18 '
     '(OfficeBench) and 15 (τ²) tasks pass <i>only</i> in Bangla. ' + I + 'At one run per cell, part of every discordant '
     'count is sampling noise; TAC’s reruns (Section 1.5) show how large that part can be.')

h2('1.3 Task size and domain')
fig('f5_obsize.png', 1.0, 'Figure 1.2. OfficeBench success by number of apps. gemma’s Bangla gap is concentrated in short tasks; '
    'gpt-oss is higher in Bangla at every size; every run collapses on three-app tasks.')
para(O + 'On OfficeBench the gemma gap is +16.1 pp on single-app tasks (Holm-adjusted p = 0.004), +9.5 pp on two-app (adjusted '
     'p = 0.186) and exactly 0 on three-app tasks (28/112 in both languages). Every run falls sharply with task size: gemma '
     'English 67.7% → 25.0%, gpt-oss English 44.1% → 7.1%. ' + I + 'Three-app tasks fail for the same reasons in both languages '
     '(step budget, cut-off writes, benchmark defects), which masks any language effect; the zero gap there says nothing '
     'about Bangla on hard tasks.')
table([
    ['τ²-bench domain', 'gemma EN', 'gemma BN', 'gemma gap', 'gpt-oss EN', 'gpt-oss BN', 'gpt-oss gap'],
    ['Airline', '66.0%', '46.0%', '+20.0', '39.6%', '45.8%', '−6.2'],
    ['Retail', '73.2%', '51.2%', '+22.0', '43.9%', '26.8%', '+17.1'],
    ['Telecom', '47.1%', '41.4%', '+5.7', '39.1%', '50.0%', '−10.9'],
    ['Banking', '10.0%', '7.5%', '+2.5', '21.4%', '21.4%', '0.0'],
], [0.22, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13], align_right_from=1)
cap('Table 1.3. τ²-bench by domain. No single domain survives Holm correction. Banking is near floor for both models and '
    'carries no language signal.')
table([
    ['WorkBench domain', 'gemma EN', 'gemma BN', 'gpt-oss EN', 'gpt-oss BN'],
    ['Email', '100.0%', '93.3%', '73.3%', '66.7%'], ['Calendar', '86.7%', '93.3%', '66.7%', '73.3%'],
    ['Analytics', '86.7%', '66.7%', '73.3%', '46.7%'], ['Project mgmt', '86.7%', '93.3%', '53.3%', '60.0%'],
    ['CRM', '73.3%', '86.7%', '60.0%', '46.7%'], ['Multi-domain', '53.3%', '60.0%', '26.7%', '26.7%'],
], [0.24, 0.19, 0.19, 0.19, 0.19], align_right_from=1)
cap('Table 1.4. WorkBench by domain (15 tasks each; descriptive only). Analytics shows the largest one-way drop for both models; '
    'multi-domain is hardest in both languages.')
table([
    ['TAC run', 'Full completion', 'Set 1 (RocketChat, GitLab)', 'Set 2 (ownCloud)', 'Mean partial score'],
    ['English', '9/23 (39.1%)', '6/11 (54.5%)', '3/12 (25.0%)', '0.515'],
    ['Bangla, latest run', '6/23 (26.1%)', '5/11 (45.5%)', '1/12 (8.3%)', '0.433'],
    ['Bangla, first run', '5/23 (21.7%)', '4/11 (36.4%)', '1/12 (8.3%)', '0.423'],
], [0.22, 0.18, 0.24, 0.18, 0.18], align_right_from=1)
cap('Table 1.5. TAC full completion and partial credit. ownCloud tasks (Set 2) are hardest in both languages.')

h2('1.4 Unexpected outcomes')
B(O + '<b>gpt-oss improves in Bangla on OfficeBench.</b> 45 subtasks pass only in Bangla vs 25 only in English; 19 of the 45 '
  'English failures are action-format failures, and all 45 English runs contain at least one malformed action.')
B(O + '<b>gemma’s Bangla runs are leaner on WorkBench</b> (3.29 requests and 3.17 tool calls per task vs 3.78 and 3.96 in English), '
  'largely because two English analytics runs looped on the same read call.')
B(O + '<b>Some English passes are not real successes.</b> WorkBench analytics:98 passed in English by abstaining after 24 '
  'looping read calls; OfficeBench 1-2/4 passes in English only because its answer happens to contain the keyword “Tom”.')
B(O + '<b>Correct answers fail.</b> On OfficeBench 1-2/0 all four cells give the right free slot (14:30–15:30) and all four fail, '
  'because two of the four checks require a calendar event the task never asks for.')

h2('1.5 How much of the gap survives confound filtering')
fig('f2_forest.png', 1.0, 'Figure 1.3. English − Bangla gap as scored (black) and after removing benchmark-side confounds '
    '(green). Scenario codes refer to the source reports (OfficeBench S9: drop translation, tool and checker cases on both '
    'sides; τ² S7: drop premature-stop dialogues in either language and credit Bengali-digit answers; WorkBench S4: drop '
    'translation, tool and checker cases symmetrically; TAC S5: credit the checker artefact and drop tasks whose Bangla reruns '
    'disagree).')
para(O + 'Every significant gap moves toward zero and its interval then includes zero. Crediting correct Bangla-script answers '
     'alone moves OfficeBench gemma from +8.0 to +3.0 pp (p = 0.233). For τ² gemma, dropping premature-stop dialogues in '
     'either language gives +7.1 pp (p = 0.090). For TAC, the choice between the first and latest Bangla run moves the gap '
     'from +13.0 to +17.4 pp on its own, and 1 of 13 reruns changed full completion (3 changed the score).')
para(I + 'The measured language gaps are of the size that benchmark-side artefacts can explain. This does <b>not</b> prove '
     'Bangla has no cost: the residual cases (C1 + C7) are too few for one-run-per-cell data to establish or exclude a '
     'modest effect. ' + O + 'One-sided filters are biased: on τ², applying the simulator filter only to EN-pass/BN-fail cases '
     'turns gpt-oss’s null gap into a −12.8 pp “Bangla advantage”, which is why symmetric scenarios are preferred above.')

# =============================== 2. WHY AND WHERE ===============================
h1('2. Why and where the models fail')
h2('2.1 Which runs and tasks fail')
table([
    ['Benchmark', 'Run', 'Failed runs', 'Fail in every cell', 'Pass in every cell'],
    ['OfficeBench', 'gemma EN / BN', '149 / 173', '113 of 300 subtasks fail in all four runs', '48'],
    ['OfficeBench', 'gpt-oss EN / BN', '214 / 194', '', ''],
    ['τ²-bench', 'gemma EN / BN', '110 / 135', '33 of 149 shared tasks fail in all four', '21'],
    ['τ²-bench', 'gpt-oss EN / BN', '91 / 90', '', ''],
    ['WorkBench', 'gemma EN / BN', '17 / 16', '6 of 90 tasks fail in all four', '37'],
    ['WorkBench', 'gpt-oss EN / BN', '37 / 42', '', ''],
    ['TAC', 'gemma EN / BN', '14 / 17', '14 of 23 task-runs fail in both languages', '6'],
], [0.15, 0.18, 0.15, 0.40, 0.12])
cap('Table 2.1. Failure volume. Hard tasks are hard for everyone: the all-cells-fail sets are the largest single group on '
    'OfficeBench and TAC.')
B(O + '<b>Weakest conditions:</b> three-app OfficeBench tasks (gpt-oss English 7.1%), τ² banking (≤ 21.4% for every cell), '
  'TAC ownCloud tasks (Bangla 8.3%), WorkBench multi-domain (gpt-oss 26.7% in both languages).')
B(O + '<b>Model decides more than language:</b> 8 WorkBench tasks pass for gemma in both languages and fail for gpt-oss in both; '
  '11 τ² tasks pass in English and fail in Bangla for <i>both</i> models (the strongest cross-model candidates for a '
  'Bangla-side cause).')
B(O + '<b>Benchmark defects decide many outcomes:</b> on OfficeBench a defect decides at least one of three fully coded runs '
  'on 57 subtasks; 44 subtasks fail for the identical coded cause in every run.')

h2('2.2 Where in the trajectory failures start')
para('The first failure point is grouped into the stage of the trajectory where the decisive error happened: task-level '
     'reasoning (instruction understanding, entity/slot grounding, constraint preservation, planning), execution-level '
     'action (tool selection, tool-argument construction, tool execution), control (result verification, premature '
     'termination) and final response only.')
table([
    ['First failure point', 'OB gemma (42)', 'OB gpt-oss (25)', 'τ² gemma (40)', 'τ² gpt-oss (26)', 'WB gemma (7)', 'WB gpt-oss (15)', 'TAC (8)'],
    ['Instruction understanding', '5', '4', '0', '3', '1', '0', '0'],
    ['Entity / slot grounding', '5', '7', '7', '5', '2', '1', '0'],
    ['Task constraint preservation', '3', '1', '4', '3', '1', '1', '0'],
    ['Planning', '5', '1', '6', '5', '1', '0', '2'],
    ['Tool selection', '0', '0', '6', '1', '0', '1', '0'],
    ['Tool-argument construction', '4', '1', '4', '2', '2', '11', '1'],
    ['Tool execution', '2', '2', '0', '0', '0', '0', '1'],
    ['Result verification', '2', '4', '1', '3', '0', '0', '2'],
    ['Premature termination', '1', '2', '11', '1', '0', '1', '1'],
    ['Final response only', '15', '3', '1', '0', '0', '0', '0'],
    ['Unclear', '0', '0', '0', '3', '0', '0', '1'],
], [0.25, 0.105, 0.11, 0.105, 0.11, 0.105, 0.11, 0.105], align_right_from=1)
cap('Table 2.2. First failure point of the analysed EN-pass/BN-fail cases (TAC: the 8 selected cases, which include reruns '
    'and both-fail tasks). OB = OfficeBench, WB = WorkBench.')
fig('f4_origin.png', 1.0, 'Figure 2.1. Stage at which the decisive error occurs. Note: 10 of τ² gemma’s 11 “premature '
    'termination” cases were caused by the simulated user, not the agent.')
para(O + 'Each benchmark has a characteristic failure stage: OfficeBench gemma at the <b>final response</b> (15/42: correct content, '
     'wrong script); τ² at <b>task-level grounding/planning</b> and <b>termination</b>; WorkBench gpt-oss at <b>tool-argument '
     'construction</b> (11/15); TAC at <b>control</b> (verification, stopping). ' + O + 'Tool syntax is never the first failure '
     'point of a τ² Bangla failure, and no WorkBench tool call contains Bangla characters (0 of 641 arguments).')

h2('2.3 Failure outcome categories')
table([
    ['Category', 'Where it shows up (evidence)', 'Scale'],
    ['Complete task failure', 'OfficeBench stuck runs after empty replies (2-1/0, 2-1/1); cut-off write loops ending with no file '
     '(1-15/0, 1-15/1, 2-6/0, 2-22/1); τ² required write never called (gemma 39 EN / 37 BN failures) or the dialogue stopped '
     'before the write (26 / 46); TAC admin-remove-pages-pdf produced no file in either Bangla run.',
     'Largest category on τ² and in OfficeBench three-app tasks'],
    ['Partial success', 'TAC: 17 of 23 task-runs earn identical partial points in both languages; mean partial score 0.515 EN vs '
     '0.433 BN (Wilcoxon p = 0.141); pm-send-notification 3/4 (one of three people not notified); ml-grade-exam 1/8. '
     'OfficeBench compound tasks with a skipped part (3-15/0 image skipped) and dropped columns (1-11/0, 1-6/4).',
     'Only TAC measures it directly'],
    ['Inefficient execution', 'gpt-oss OfficeBench: 1,671 invalid actions EN vs 955 BN; 643 vs 99 built-in tool calls; 139 vs 49 '
     'steps with no action; 86 vs 63 runs at the 20-step limit. gemma: 14–15 identical rejected writes per TL case. WorkBench '
     'analytics:98 EN: 24 looping read calls. gpt-oss WorkBench: 4.23 EN vs 3.84 BN requests per task.',
     'Pervasive for gpt-oss; episodic for gemma'],
    ['Incorrect or incomplete output', 'OfficeBench answer in Bangla script/digits (15 gemma cases, e.g., 40 and $20,000 written in '
     'Bengali digits); word re-rendering (“Trip”, “curd”, “08:00 AM”); wrong content (WC: 36 of 131 both-fail gemma Bangla runs); '
     'WorkBench wrong filters (crm:77 missing status filter → 5 spurious updates); τ² wrong write arguments (19 per gemma run).',
     'Largest category among Bangla-only failures'],
], [0.18, 0.60, 0.22])
cap('Table 2.3. The four outcome categories with representative evidence. The same run can be inefficient and still pass.')

h2('2.4 How runs end')
table([
    ['OfficeBench gpt-oss:20b (299 runs per language)', 'English', 'Bangla'],
    ['Invalid (malformed) actions', '1,671', '955'], ['Calls to its own built-in tools (container.exec, …)', '643', '99'],
    ['Steps with no action at all', '139', '49'], ['Runs ended as stuck', '31', '14'],
    ['Runs ended at the 20-step limit', '86', '63'], ['Runs that finished with an answer', '182', '222'],
], [0.60, 0.20, 0.20], align_right_from=1)
cap('Table 2.4. gpt-oss on OfficeBench: execution-control signals. The Bangla prompt coincides with far fewer format failures.')
fig('f6_tau2signals.png', 1.0, 'Figure 2.2. τ²-bench: automatic failure signal of every failed run (four largest signals). '
    'The only signal that grows sharply in Bangla is the simulator ending the dialogue before the agent acted (gemma 26 → 46).')
table([
    ['τ²-bench dialogue signals', 'gemma EN', 'gemma BN', 'gpt-oss EN', 'gpt-oss BN'],
    ['Runs where the user writes mostly Latin script', '218', '33', '149', '54'],
    ['Messages per run (mean)', '34.70', '33.50', '40.10', '38.80'],
    ['Agent tool calls per run (mean)', '7.69', '6.64', '7.26', '6.44'],
    ['Runs ending in transfer to a human', '108', '112', '52', '55'],
    ['Simulator ended chat before the agent acted', '26', '46', '3', '3'],
], [0.44, 0.14, 0.14, 0.14, 0.14], align_right_from=1)
cap('Table 2.5. τ²-bench run-level signals. 33 gemma and 54 gpt-oss Bangla runs have a simulated user writing mostly English, '
    'a simulator-fidelity problem the agent cannot fix. The premature-stop detector is heuristic (about half of a random '
    'sample of its flags were true premature stops).')

# =============================== 3. ROOT CAUSES ===============================
story.append(CondPageBreak(140 * mm)); h1('3. Root-cause analysis')
h2('3.1 Confound classes across benchmarks')
fig('f3_confound.png', 1.0, 'Figure 3.1. Confound class of every hand-analysed case. *TAC’s 8 cases include reruns and both-fail '
    'tasks; the others are EN-pass/BN-fail cases only.')
table([
    ['Class', 'OB gemma', 'OB gpt-oss', 'τ² gemma', 'τ² gpt-oss', 'WB gemma', 'WB gpt-oss', 'TAC', 'Total (163)'],
    ['C1 Genuine Bangla agent failure', '6', '7', '6', '2', '2', '1', '0', '24 (14.7%)'],
    ['C2 User simulator / NPC', '0', '0', '19', '16', '0', '0', '0', '35 (21.5%)'],
    ['C3 Translation / localization', '6', '0', '1', '0', '1', '0', '1', '9 (5.5%)'],
    ['C4 Tool / environment', '5', '2', '0', '0', '0', '0', '1', '8 (4.9%)'],
    ['C5 Checker / task ambiguity', '15', '6', '0', '0', '1', '0', '0', '22 (13.5%)'],
    ['C6 General weakness', '3', '1', '14', '7', '3', '14', '3', '45 (27.6%)'],
    ['C7 Unclear / noise', '7', '9', '0', '1', '0', '0', '3', '20 (12.3%)'],
    ['Cases', '42', '25', '40', '26', '7', '15', '8', '163'],
], [0.25, 0.08, 0.09, 0.08, 0.09, 0.08, 0.09, 0.07, 0.17], align_right_from=1)
cap('Table 3.1. Confound counts. Upper bound on genuine Bangla agent effects (C1 + C7): 44 of 163 (27.0%); lower bound (C1): 24 (14.7%).')
para(I + 'The benchmark’s interaction design predicts its dominant confound. Tasks whose answer is a free-text string checked '
     'by keyword (OfficeBench) are dominated by checker language; dialogue tasks with a same-model simulator (τ²) by the '
     'simulator; strict function-calling tasks with English tool descriptions (WorkBench) by language-independent argument '
     'errors; long-horizon tasks with brittle web apps (TAC) by environment walls and run-to-run noise.')

h2('3.2 Root causes, mechanisms and contribution to failure')
para('Each cause is listed with its mechanism, how it turns into the final failure, the evidence and its status. '
     '<b>Confirmed</b> = the mechanism is visible in traces and the counterfactual (usually the English run or a rerun) '
     'succeeds; <b>Plausible</b> = consistent with traces but with a competing explanation; <b>Hypothesis</b> = inferred '
     'from aggregate association only.')
RC = [
    ['#', 'Root cause (category)', 'Mechanism → contribution to failure', 'Evidence', 'Status'],
    ['R1', 'English-only checker; answer in Bangla script (benchmark: check)', 'Prompt never names an answer language → agent '
     'answers in Bangla script/digits → keyword check for ASCII value fails although content is correct.',
     'OB: 15 gemma C5 cases (1-10/0 and 2-31/0: numbers in Bengali digits; 1-13/2: Bangla “na” for No); 2 gpt-oss. TAC T01: NPCs reply in Bangla, '
     'CP5 needs “helpful”. τ²: Bengali-digit fix flips 2 gemma runs.', 'Confirmed'],
    ['R2', 'Benchmark defects (benchmark: check)', 'Check asks for something the task does not (or the reference/app is '
     'wrong) → correct work scored FAIL in every language.',
     'OB: 47 of 149 gemma EN failures (31.5%), 39 of 131 both-fail; 1-2/0 fails in all four cells; 57 subtasks decided by a defect.',
     'Confirmed'],
    ['R3', 'User-simulator errors (benchmark: simulator)', 'Bangla simulated user confirms and emits ###STOP### in one turn, '
     'gives an internal ID as a name, answers in English, or narrates a device action without calling the tool → the '
     'required write or device state is never reached.',
     'τ²: 35 of 66 cases (53%); premature-stop flags 46 BN vs 26 EN (gemma); airline 19; telecom device-action failures.',
     'Confirmed per case; detector counts heuristic'],
    ['R4', 'Translation changed the task (benchmark: task)', 'Machine translation altered a literal or the operation → agent '
     'faithfully executes the wrong task.',
     'OB: 3-56/0 quoted homework sentence translated; 3-68/0 “sum” became “add” (wrote 104.98 and 1389.99 instead of 1494.97); '
     '2-38/2 and 3-17/0 files-to-create presented as existing; 3-55/0, 2-40/2. TAC: translations faithful in all 8 cases.',
     'Confirmed'],
    ['R5', 'Entity grounding from caseless script (reasoning: grounding)', 'Name present only in Bangla script → agent writes '
     'it in lower case → case-sensitive mailbox/calendar lookup returns empty → empty result accepted (see R12).',
     'OB gemma 1-20/3, 1-21/1, 1-21/2; gpt-oss 1-21/1, 1-21/2, 2-39/0, 2-39/1, 2-39/3, 2-40/1 (same two subtasks fail for both '
     'models). τ²: Bangla-script names/IDs in lookups.', 'Confirmed; replicated across models'],
    ['R6', 'Re-rendering values into English (reasoning: argument construction)', 'Agent maps a Bangla word or time back to a '
     'different English surface form → exact-match check fails.',
     'OB 1-1/4 “Trip to Florida” (both models), 1-4/1 “curd” for yogurt, 1-6/2 “08:00 AM” for 8:00.',
     'Confirmed per case; medium confidence it is language-caused'],
    ['R7', 'Relative-date grounding (reasoning: grounding)', '“Last week” grounded as rolling 7 days instead of the previous '
     'calendar week → searches return nothing → correct evidence later rejected.',
     'WB email:41 (gemma): windows 11-23..29 vs 11-19..26; undated search found both emails, agent rejected them.',
     'Plausible (pending native-speaker review of the phrase)'],
    ['R8', 'Malformed actions / format non-adherence (execution: tool-call format)', 'Model emits its native tool-call habit '
     '(container.exec, repo_browser), invalid JSON or empty replies → harness rejects the step → repeated invalid steps end '
     'the run as stuck or at the step limit.',
     'OB gpt-oss: 54 FMT failures; 1,671 invalid actions EN; 19 of 45 FP subtasks are EN format failures. Pilot qwen2.5-7b: '
     '7 of 12 runs stuck. WB: invented argument names (new?, field, value_to_plot) crash runs (5 BN, 2 EN).',
     'Confirmed as mechanism; the link to prompt language is a Hypothesis'],
    ['R9', 'Output cap + whole-document rewrite (execution control; context/output limits)', 'Agent plans to resend the '
     'entire file (write tool’s append behaviour undocumented) → action exceeds the 512-token reply cap → “Malformed '
     'action!” → identical retries until the step budget is spent.',
     'OB 1-15/0 (14 rejected writes), 1-15/1 (15), 2-6/0, 2-22/1 (English recovered by chunking in 2-6/0).', 'Confirmed'],
    ['R10', 'Wrong tool arguments (execution: argument construction)', 'Missing or wrong filter values, thresholds or IDs → '
     'wrong rows changed or nothing found.',
     'WB gpt-oss: 40 of 79 labelled failures; crm:77 status filter dropped → 5 spurious updates; τ² “write with wrong '
     'arguments” 19/19 (gemma), 25/21 (gpt-oss); τ² airline 8 invented 2 free bags.', 'Confirmed; language-independent (C6)'],
    ['R11', 'Tool-selection mistakes (execution: tool choice)', 'Agent calls tools that belong to the user or do not exist, or '
     'transfers instead of using a discoverable tool → required action never happens.',
     'τ² telecom: run_speed_test / toggle_airplane_mode called by the agent → “not found”; banking: transfer instead of '
     'unlock_discoverable_agent_tool; WB crm:77 non-existent customer_relationship_manager_update_task.', 'Confirmed'],
    ['R12', 'No verification of results (control)', 'Empty or implausible tool results accepted as final; success claimed '
     'without checking state.',
     'OB 1-20/2 (empty listing accepted at step 2; English searched the filesystem), ER code 9 both-fail runs; TAC '
     'hr-transfer-group false success claims, sde-install-go verified by absolute path (grader’s `go version` fails), '
     'ml-grade-exam guessed grades.', 'Confirmed'],
    ['R13', 'Premature termination (control)', 'Agent stops at the first acceptable answer or before finishing all sub-goals.',
     'TAC hr-pick-interviewer-2 (both languages stop after first acceptance), pm-send run A (2 of 3 notified); OB gpt-oss '
     '1-2/3 “I don’t know” after one step; τ² early transfer.', 'Confirmed'],
    ['R14', 'Step budget exhaustion on long tasks (control; task length)', 'Three-app tasks need more steps than 20 once one '
     'retry loop occurs → budget runs out.',
     'OB SB code 18 of 131 both-fail gemma; three-app success 25.0% (gemma) / 7.1% (gpt-oss EN).', 'Confirmed for three-app tasks'],
    ['R15', 'Harness / environment faults (harness)', 'llm app limited to 50 tokens returns empty strings for a reasoning model; '
     'empty model replies; shell quoting; ownCloud 401/permission walls; admin password prompts; provider errors.',
     'OB gpt-oss 2-36/0, 3-89/0 (all 14 llm calls empty); 2-1/0, 2-1/1; 3-9/0 apostrophe; TAC T05 (401), T07 (password '
     'modal); WB provider errors (S6 leaves gap unchanged).', 'Confirmed mechanism; Bangla-triggered empty replies a Hypothesis'],
    ['R16', 'Context handling (harness: memory)', 'Earlier thoughts are not carried forward in the OfficeBench loop (only '
     'actions/results are) → the agent may re-derive or forget a plan and repeat a failed action.',
     'Design note in the OfficeBench report; repeated identical retries in R8/R9 are consistent with it.', 'Hypothesis'],
    ['R17', 'Run-to-run variance (measurement)', 'Single-run attributions mix mechanism and sampling noise.',
     'TAC: 1 of 13 reruns changed full completion, 3 changed score; sde-install-go passes and fails in Bangla. OB C7: 2-32/1, '
     '3-87/0 diverge on identical OCR input.', 'Confirmed as variance; cause per case unknown'],
]
table(RC, [0.055, 0.16, 0.31, 0.34, 0.135])
cap('Table 3.2. Root-cause catalogue. OB = OfficeBench, WB = WorkBench. Categories map to the requested taxonomy: reasoning '
    'errors (R5–R7), tool-selection mistakes (R11), malformed tool calls (R8), failure to verify (R12), repeated unsuccessful '
    'retries and inefficient execution (R8, R9), context/output limitations (R9, R16), premature termination (R13), plus '
    'benchmark-side (R1–R4) and harness (R15) causes.')

h2('3.3 How much each cause explains')
table([
    ['Cause', 'Effect on the measured result', 'Evidence type'],
    ['R1 answer-language checker', 'OfficeBench gemma gap +8.0 → +3.0 pp when Bangla-script answers are credited', O],
    ['R2–R4 checker, translation, harness', 'OfficeBench gemma gap → −0.7 pp (one-sided) / +1.9 pp (symmetric S9)', O],
    ['R3 user simulator', 'τ² gemma gap +11.5 → +7.1 pp after dropping premature-stop dialogues in either language', O],
    ['R8 format failures', 'OfficeBench gpt-oss Bangla advantage −6.7 → −3.3 pp after dropping English format failures', O + H],
    ['R1 + R17 noise (TAC)', 'TAC gap +13.0 → 0.0 pp after crediting the checker artefact and dropping disagreeing reruns', O],
    ['R10–R14 general weaknesses', 'Dominate absolute failure counts in every benchmark (e.g., 82 of 112 WorkBench failed runs are C6)', O],
], [0.28, 0.56, 0.16])
cap('Table 3.3. Contribution of each cause family to the headline numbers.')

h2('3.4 Confirmed causes vs open hypotheses')
callout([
    '<b>Confirmed</b> (trace-level mechanism plus a passing counterfactual): R1, R2, R3 (per case), R4, R5, R9, R10, R11, '
    'R12, R13, R14, R15 (mechanism).',
    '<b>Plausible</b> (mechanism visible, alternative not excluded): R6 word re-rendering (could be lexical ambiguity of the '
    'Bangla word); R7 relative-date grounding (could be a translation that leans to “past 7 days”, which would make it C3).',
    '<b>Hypotheses</b> (aggregate association only): Bangla prompts suppress gpt-oss’s native tool-call habit (R8); empty '
    'replies in 2-1/0 and 2-1/1 are Bangla-triggered (R15); missing thought carry-over causes repeated retries (R16); the 9 '
    'gpt-oss and 7 gemma C7 OfficeBench cases hide a genuine Bangla reasoning cost.',
    '<b>Not supported by the data</b>: “Bangla breaks tool calling” (no case fails first on tool syntax; 0 Bangla characters in '
    '641 WorkBench arguments) and “Bangla agents reason worse” in general (no EN-pass/BN-fail OfficeBench case has a wrong '
    'number, date or path tied by the trace to reading Bangla).',
])

# =============================== 4. COMPARATIVE ===============================
h1('4. Comparative and trajectory-level analysis')
h2('4.1 Across models')
table([
    ['Dimension', 'gemma4:31b', 'gpt-oss:20b'],
    ['English capability', 'Higher on every benchmark (50.3 / 49.5 / 81.1 / 39.1%)', 'Lower (28.7 / 38.9 / 58.9%)'],
    ['Bangla effect', 'Cost on OfficeBench (+8.0) and τ² (+11.5); none on WorkBench', 'Gain on OfficeBench (−6.7); none on τ² and WorkBench'],
    ['Dominant own failure', 'Content and planning errors; cut-off write loops; answers in Bangla script', 'Action-format failures and wrong tool arguments'],
    ['Answer language', 'Answers in Bangla when prompted in Bangla (15 C5 cases on OB)', 'Mostly answers in English (4 Bangla answers among 25 cases)'],
    ['Shared Bangla mechanisms', 'Name case (3 OB), word re-rendering (Trip, curd, 08:00 AM)', 'Name case (6 OB), word re-rendering (Trip)'],
    ['Tool-related harness issue', '512-token reply cap', 'llm app 50-token limit consumed by hidden reasoning'],
], [0.22, 0.39, 0.39])
cap('Table 4.1. Model comparison. The same Bangla mechanism appears in both models; their different net effects come from '
    'model-specific failure modes that the Bangla prompt amplifies (gemma: script of the answer) or dampens (gpt-oss: format).')
h2('4.2 Across benchmarks and languages')
table([
    ['Benchmark', 'Where Bangla text reaches a brittle component', 'Resulting dominant confound', 'Net gap (gemma)'],
    ['OfficeBench', 'Free-text answers checked by English keywords; machine-translated literals', 'C5 checker, C3 translation', '+8.0 pp, significant'],
    ['τ²-bench', 'The simulated customer itself speaks Bangla and controls when the dialogue ends', 'C2 simulator', '+11.5 pp, significant'],
    ['WorkBench', 'Nowhere critical: English tool descriptions, DB-state check, no free-text answer', 'C6 general weakness', '−1.1 pp, n.s.'],
    ['TAC', 'Bangla NPC replies stored verbatim, English keyword checkpoint; small sample', 'C7 noise, C6, one C3', '+13.0 pp, n.s.'],
], [0.14, 0.42, 0.22, 0.22])
cap('Table 4.2. The size of the Bangla gap tracks how many benchmark components consume Bangla text, not the agent’s tool use.')
para(I + 'WorkBench is the closest to a controlled test of the agent alone (no simulator, no free-text check), and it shows no '
     'gap for either model. This supports the reading that most of the gaps elsewhere are produced by the evaluation '
     'pipeline’s handling of Bangla rather than by the agents’ task competence; the boundary is WorkBench’s small size (90 '
     'tasks; a cost up to 8–17 points cannot be excluded).')
story.append(CondPageBreak(230 * mm)); h2('4.3 How early mistakes propagate')
fig('f7_chains.png', 0.98, 'Figure 4.1. Six traced failure chains. Box colour marks the kind of step; each chain is taken from the '
    'trace notes in the source reports.')
para(O + 'Patterns visible in the chains:')
B('<b>Grounding → silent empty result → acceptance.</b> In 1-20/3, a one-character case error makes the lookup return '
  'nothing; the agent treats “no emails” as the answer. The English run of 1-20/2 shows the recovery that was missing: after '
  'an equally wrong first lookup it searched the filesystem and found the mailbox.')
B('<b>Plan → hard limit → identical retries.</b> In 1-15/0 the plan is reasonable given an under-documented tool, but the '
  'agent never adapts after the first rejection; 14 identical actions consume the budget. In 2-6/0 English hit the same wall '
  'five times and then recovered by chunking.')
B('<b>Early grounding overrides later evidence.</b> In WorkBench email:41 the wrong date window is chosen at step 2; at step 5 '
  'the correct emails are retrieved and <i>rejected</i> because they conflict with the agent’s own earlier interpretation.')
B('<b>External termination.</b> In τ² airline 19 the agent’s chain is correct to the last step; the simulated user ends the '
  'dialogue, so no agent-side change could have passed.')
B('<b>Tool misuse → degraded instructions → simulator drift.</b> In τ² telecom, the agent first calls user-side tools itself, '
  'then gives vague instructions; the simulated user toggles the wrong settings, and the run ends in transfer.')
B('<b>Environment wall → no alternative plan.</b> In TAC admin-remove-pages-pdf both Bangla runs retry the same '
  'authenticated URLs after a 401; English found a public-share-link workaround (and still failed on content).')

h2('4.4 Task-level reasoning, execution-level control, or their interaction?')
table([
    ['Origin', 'Typical cases', 'Share of analysed cases'],
    ['Task-level reasoning only', 'Translation-induced misreadings (OB 3-68/0), filtered roster (2-20/0), τ² airline 9 (flown '
     'reservation cancelled), dropped constraints', 'Largest first-failure stage on τ² and OfficeBench gpt-oss (Figure 2.1)'],
    ['Execution-level control only', 'Format failures (gpt-oss), wrong tool arguments (WB gpt-oss 11/15), harness faults, '
     'cut-off loops', 'Dominant on WorkBench gpt-oss and OfficeBench gpt-oss English'],
    ['Interaction', 'Grounding error not caught by verification (1-20/3, 1-21/x, email:41); reasonable plan defeated by a '
     'hard limit without adaptation (1-15/x); tool misuse amplified by simulator (telecom)', 'Most of the genuine Bangla cases (C1)'],
    ['Outside the agent', 'Checker language (C5), simulator (C2), benchmark defects', '35.7% of gemma OB cases; 53% of τ² cases'],
], [0.22, 0.52, 0.26])
cap('Table 4.3. Origin of failures.')
para(I + 'The genuine Bangla failures share a two-stage structure: a small task-level slip specific to the Bangla input (case, '
     'word, date window) that would be harmless if execution-level control verified results. ' + H + 'Most C1 cases would '
     'therefore be removed either by fixing the input (protect names, dates and literals) or by adding verification '
     '(retry empty lookups with case variants; re-check a window that returns nothing). Experiment E6 tests this.')

# =============================== 5. EVIDENCE & RECS ===============================
h2('4.5 Why the two models fail at different layers')
para('An agent run passes through the same layers in every benchmark: (L1) read and ground the task, (L2) plan, '
     '(L3) emit an action in the required format, (L4) fill in the tool arguments, (L5) control the run (check results, '
     'recover, decide when to stop), (L6) write the final answer. The question is at which layer each model breaks first.')
table([
    ['Layer', 'gemma4:31b', 'gpt-oss:20b', 'Source'],
    ['L3 Action format (no valid action, malformed or invented tool calls)', '12 of 149 English failures (8%)',
     '107 of 214 English failures (50%); 1,671 invalid actions; 643 calls to its own built-in tools', 'OfficeBench, Fig. 7 and II.9 of source'],
    ['L4 Tool arguments', '11 of 33 failed runs (33%)', '40 of 79 failed runs (51%); invented argument names crash runs',
     'WorkBench R.5'],
    ['L1–L2 Content and task reading (wrong content, task read differently)', '43 of 149 English failures (29%) are wrong content',
     '49 of 214 (23%)', 'OfficeBench, Fig. 7'],
    ['L5 Control (step budget, cut-off loops)', '42 of 149 English failures (28%) run out of steps or loop at the reply cap',
     '24 of 214 (11%)', 'OfficeBench, Fig. 7'],
    ['L6 Answer language (correct answer in Bangla script)', '15 of 42 EN-pass/BN-fail cases', '3 of 25 (only 4 Bangla-script '
     'answers among them)', 'OfficeBench §6, II.8'],
    ['Shared Bangla input slip (L1: name case)', '3 cases', '6 cases (same two subtasks fail for both)', 'OfficeBench F3, G4'],
], [0.27, 0.27, 0.30, 0.16])
cap('Table 4.4. First broken layer by model. OfficeBench shares use the primary root-cause families of all coded failures; '
    'WorkBench shares use the adjudicated failure type of every failed run.')
h3('Why gpt-oss breaks at the format and argument layers')
B(I + '<b>Its own tool-calling habit competes with the benchmark’s format.</b> OfficeBench asks for plain text '
  '(“##Command: {json}”). gpt-oss repeatedly calls tools that exist in its own training setup but not in OfficeBench '
  '(container.exec, repo_browser: 643 calls in English). Each such call is rejected as malformed, and enough of them end '
  'the run as stuck. ' + O + 'Evidence: 50% of its English failures produce no valid action; all 45 English runs that '
  'Bangla later passed contain at least one malformed action.')
B(I + '<b>When the interface handles the format, the errors move one layer down.</b> WorkBench uses provider-side function '
  'calling, so the JSON syntax is no longer gpt-oss’s problem; its failures then concentrate at argument filling (51%): '
  'missing filters, wrong thresholds, invented argument names. The model’s weakness is turning task constraints into exact '
  'structured values, and the interface decides whether that shows up as a format error or an argument error.')
B(I + '<b>Hidden reasoning consumes fixed token budgets.</b> gpt-oss reasons in a separate channel before answering. Where '
  'the harness allows only 50 tokens (the OfficeBench llm app), the reasoning uses them up and the visible answer is '
  'empty (all 14 calls in 2-36/0 and 3-89/0). ' + O + 'This failure does not occur for gemma.')
B(H + '<b>Capacity.</b> gpt-oss:20b is a mixture-of-experts model with far fewer active parameters per token than gemma4:31b; '
  'precise argument construction may suffer from that. This is not tested by any of the four studies.')
h3('Why gemma breaks at the content, control and answer layers')
B(I + '<b>It follows the text action format reliably</b> (8% no-valid-action failures), so most of its runs reach the later '
  'layers, and its failures appear there: wrong content (29%), running out of steps or looping at the 512-token reply cap '
  '(28%), and benchmark defects that only matter once a run produces output (32%).')
B(I + '<b>It mirrors the user’s language in its answer.</b> Given a Bangla prompt, gemma writes its final answer in Bangla '
  'script and digits; the English keyword checker then rejects it (15 of its 42 Bangla-only failures). gpt-oss stays '
  'anchored to English in its answers, so this layer barely affects it. The same behaviour that makes gemma a better '
  'Bangla conversational partner is penalised by an English-only checker.')
B(I + '<b>Its control layer is the weak point under hard limits.</b> When an action is rejected for length, gemma tends to '
  'resend the same long action (14–15 identical retries in 1-15/0 and 1-15/1) instead of changing strategy; this is a '
  'recovery failure, not a reasoning failure.')
h3('Two cross-cutting reasons')
B(I + '<b>Failure masking.</b> A run can only fail at a later layer if it survives the earlier ones. gpt-oss loses half its '
  'English runs at the format layer, so its content, budget and answer-language failures are under-counted, not absent. '
  'Comparing models by failure counts per layer therefore needs per-layer pass rates (how many runs reached each layer), '
  'which none of the source reports records yet.')
B(I + '<b>Language interacts with the layer, not the model.</b> The Bangla input changes behaviour at the layer where each '
  'model is fragile: it reduces gpt-oss’s format failures (1,671 → 955 invalid actions) and increases gemma’s answer-language '
  'failures. The one Bangla mechanism located at L1, the lower-cased name, appears in both models, because it comes from the '
  'input script (no letter case), not from either model.')
para(H + 'Prediction that tests this account: give gpt-oss native function calling on OfficeBench and its Bangla advantage '
     'should disappear while its argument errors rise (experiment E5); tell gemma to answer in English and its Bangla gap '
     'should fall to about +3 pp (E2).')

h1('5. Evidence and recommendations')
h2('5.1 Evidence matrix for the major findings')
table([
    ['Finding', 'Observed facts', 'Interpretation', 'Open hypothesis'],
    ['Bangla gap is model- and benchmark-dependent', 'gemma +8.0 (OB, p=.003), +11.5 (τ², p=.001), −1.1 (WB); gpt-oss −6.7 '
     '(OB, p=.022), −0.7 (τ²), +5.6 (WB)', 'No universal “Bangla is worse” claim holds', 'Gaps reflect evaluation components more than agents'],
    ['Checker language drives OB gemma gap', '15 of 42 PF cases are correct answers in Bangla script; crediting them: +8.0 → +3.0', 'Benchmark artefact', '—'],
    ['Simulator drives τ² gap', '35 of 66 PF cases C2; premature-stop flags 46 vs 26', 'Benchmark artefact; same model plays both roles', 'A stronger simulator removes most PF cases'],
    ['Genuine Bangla mechanisms are few', '24 of 163 cases C1; name case in both models', 'Grounding, not tool syntax', 'Protecting names removes them'],
    ['gpt-oss gains from Bangla prompt', 'Invalid actions 1,671 → 955; built-in calls 643 → 99', 'Format effect', 'Script switch suppresses native tool-call habit'],
    ['Failures are mostly language-independent', '113 OB subtasks fail in all four runs; 82/112 WB failures C6', 'Fix the agent loop and benchmarks first', '—'],
    ['Noise is large', 'TAC reruns change 3 of 13 scores; gap +13.0 vs +17.4 by rerun choice', 'Single runs cannot attribute small effects', '—'],
], [0.21, 0.33, 0.23, 0.23])
cap('Table 5.1. Separation of observed facts, interpretations and hypotheses.')

h2('5.2 Recommended improvements')
h3('Benchmark and evaluation')
B('<b>Language-agnostic checking</b> (R1): normalise Bengali digits (Bengali digits → ASCII 0–9), accept Bangla answers via an answer-key '
  'synonym list or a semantic judge, or state the answer language in the task. Apply the same rule to TAC keyword '
  'checkpoints and τ² communicate checks.')
B('<b>Repair benchmark defects</b> (R2): audit the 57 OfficeBench subtasks where a defect decides a run (e.g., 1-2/0 requires a '
  '“meeting” event the task never asks for) and document tool semantics (write_to_file appends).')
B('<b>Constrain the user simulator</b> (R3): reject a user turn that confirms and stops at once; require device-tool calls '
  'for device actions; check that the simulator speaks the target language; consider a fixed, stronger simulator model '
  'independent of the agent.')
B('<b>Case-insensitive identity lookups</b> (R5) in mailbox and calendar tools, or canonical Latin names in prompts.')
h3('Translation')
B('<b>Protected tokens</b> (R4, R5): keep person names, file names, quoted literals and grader strings in Latin script, use ASCII '
  'digits, and verify automatically. For OfficeBench this is implemented in the v2 translation (298/298 tasks pass the '
  'automatic checks; 294 strings changed; Bob kept in 54/54 tasks).')
B('<b>Native-speaker review</b> of relative-date phrases and domain terms (R7) before claiming genuine effects.')
h3('Agent and harness')
B('<b>Verification before finishing</b> (R12): treat an empty result as a signal to retry (case variants, alternative tool, '
  'filesystem search) rather than as the answer; re-read the changed state before claiming success.')
B('<b>Stuck recovery</b> (R8, R9): after two identical rejected actions, force a strategy change (chunked or append writes, '
  'shorter text); expose the reply cap and the append semantics in the tool description; raise the 512-token cap for long writes.')
B('<b>Format robustness</b> (R8): use native function calling or constrained decoding for gpt-oss; return a structured error '
  'naming the invalid argument instead of crashing the run (WorkBench invented argument names).')
B('<b>Fix harness limits</b> (R15): raise the llm app limit above 50 tokens for reasoning models; retry empty model replies; '
  'quote shell arguments; pre-authorise ownCloud sessions where the task does not test authentication.')
B('<b>Completion checklists</b> (R13, R14): derive sub-goals from the task and check them before finish_task; reserve budget '
  'for three-app tasks.')

h2('5.3 Follow-up experiments')
table([
    ['#', 'Experiment', 'Tests', 'Prediction if the hypothesis holds', 'Metric'],
    ['E1', 'Rerun OfficeBench Bangla with the v2 translation (names Latin, ASCII digits, literals protected). A rerun was started on '
     '2026-10-10 (tag bn2) and has not completed; its results are not part of this report.', 'R4, R5, R6', 'NC and TX cases disappear; '
     'gemma gap shrinks toward the S9 value', 'PF count by code; gap'],
    ['E2', 'Answer-language control: “answer in English” instruction vs multilingual checker', 'R1', 'Both remove the 15 AL cases; '
     'gap ≈ +3 pp', 'Gap, AL count'],
    ['E3', '≥ 3 seeds per cell on all benchmarks', 'R17', 'Discordant counts shrink; CIs reflect variance', 'Per-task pass rate, ICC'],
    ['E4', 'τ²: Bangla agent with a fixed strong simulator; and English simulator with Bangla agent', 'R3', 'Most C2 cases pass; '
     'residual gap ≈ C1 + C6', 'Gap, premature-stop rate'],
    ['E5', 'gpt-oss format ablation: native tool calling vs text JSON, in both languages', 'R8 (H)', 'Bangla advantage disappears '
     'under native tool calling', 'Invalid actions, gap'],
    ['E6', 'Verification ablation: auto-retry empty lookups with case variants; chunked-write recovery', 'R5, R9, R12', 'C1 name-case '
     'and TL cases pass', 'PF count; steps used'],
    ['E7', 'Reply-cap ablation (512 → 2048 tokens) and documented append semantics', 'R9', 'Cut-off loops vanish in both languages', 'TL count'],
    ['E8', 'Relative-date probe set reviewed by native speakers', 'R7', 'Rolling-window grounding persists only if genuine', 'Accuracy on probes'],
    ['E9', 'Symmetric audit of EN-fail/BN-pass cases (OfficeBench, τ²) and native-speaker second review', 'Bias in S-scenarios', 'Symmetric gaps match S9/S7', 'κ, gap'],
    ['E10', 'Scale TAC beyond 23 task-runs with English reruns too', 'Power', 'Gap estimate stabilises', 'Gap CI width'],
], [0.05, 0.33, 0.12, 0.32, 0.18])
cap('Table 5.2. Proposed experiments, each tied to a failure mechanism.')

h2('5.4 Limitations of this synthesis')
B('One run per cell at temperature 0 in every benchmark (only some TAC Bangla tasks were rerun).')
B('All annotators are LLMs; second review exists for WorkBench and part of τ²; agreement on fine confounds is modest '
  '(τ² κ = 0.39).')
B('Different task sets and sample sizes (23 to 300 pairs); TAC and WorkBench are pilots.')
B('Heuristic signals: the τ² premature-stop detector has about 50% precision; gpt-oss OfficeBench Bangla failures beyond the '
  'first 51 subtasks are not root-cause coded.')
B('Bangla tasks were machine-translated by the same model family (gemma4:31b); translation noise is part of the Bangla condition.')
B('This document transcribes the source reports; it did not recompute any statistic.')

# =============================== APPENDIX ===============================
h1('Appendix A. Glossary of codes')
table([
    ['Code', 'Meaning'],
    ['PP / PF / FP / FF', 'Both pass / English pass, Bangla fail / English fail, Bangla pass / both fail'],
    ['MELR', 'Multilingual expected loss ratio = (EN − BN) / EN'],
    ['BM', 'Benchmark defect (check asks for what the task does not; wrong reference; app corrupts output)'],
    ['WC / TR', 'Wrong content / task read differently'],
    ['SB / TL / DL', 'Out of steps / cut-off output loop at the reply cap / reasoning loop'],
    ['FMT / ER / PF / CAP', 'Action-format failure / empty result, gave up / premature finish / capability claim or refusal'],
    ['AL / NC / WD / TX', 'Answer language / name case / word choice / translation shift (Bangla cells only)'],
    ['OTH / INF', 'Other / infrastructure (crashed runs, empty API replies)'],
    ['C-AMBIG, C-WEAKCHECK, C-HARNESS, C-LLMAPP', 'Contributing tags: ambiguous task, weak check, harness issue, llm-app issue'],
    ['S0–S9', 'Sensitivity scenarios of the source reports (S0 = as scored)'],
], [0.28, 0.72])
h1('Appendix B. Source-report cross-reference')
table([
    ['Topic', 'OfficeBench report', 'τ²-bench report', 'WorkBench report', 'TAC report'],
    ['Headline results', 'R, §2, §11', 'R, §2, §11', 'R, §2, §11', 'R, §2, §11'],
    ['Trace notes', 'App. A (gemma), App. D (gpt-oss)', 'App. A (66 cases)', 'App. A, B, C', 'App. A (8 cases)'],
    ['Sensitivity', '§11 (S0–S9), II.10', '§11 (S0–S7)', '§11 (S0–S6)', '§11 (S0–S5)'],
    ['Case studies', '§15 (3-68/0, 1-10/0, 1-15/0)', '§15 (airline 19, 9, 8)', '§15 (email:41, crm:77, analytics:98)', '§15 (T01, T03, T08)'],
], [0.18, 0.22, 0.20, 0.22, 0.18])

doc.multiBuild(story)
print('wrote', OUT)
