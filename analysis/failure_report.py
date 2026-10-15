"""Detailed 'why tasks fail' PDF for the gemma4:31b OfficeBench runs (English + Bangla).

Computes the failure taxonomy counts from the saved runs and renders a multi-page PDF with
definitions, counts, root-cause explanations, and concrete verified examples.

    python analysis/failure_report.py
"""
import glob, json, os, sys, contextlib, io
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
from history_to_trace import evaluate

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                HRFlowable, KeepTogether, ListFlowable, ListItem)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Bengali-capable font (Nirmala UI, shipped with Windows) — without it Bangla renders as boxes.
pdfmetrics.registerFont(TTFont('Nirmala', 'C:/Windows/Fonts/Nirmala.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Nirmala-Bold', 'C:/Windows/Fonts/Nirmala.ttc', subfontIndex=2))
pdfmetrics.registerFontFamily('Nirmala', normal='Nirmala', bold='Nirmala-Bold',
                              italic='Nirmala', boldItalic='Nirmala-Bold')
BN_FONT, BN_BOLD = 'Nirmala', 'Nirmala-Bold'

OUT = 'analysis/OfficeBench_why_tasks_fail.pdf'
INK = colors.HexColor('#18202c'); MUTED = colors.HexColor('#5a6476'); ACCENT = colors.HexColor('#2d5a9b')
LINE = colors.HexColor('#dce1e8'); FAIL = colors.HexColor('#b8392f'); WARN = colors.HexColor('#9a6516')
BAND = colors.HexColor('#eef1f5'); AGENTC = colors.HexColor('#b8392f'); BENCHC = colors.HexColor('#9a6516')

CATS = [
    ('A-REASON', 'ভুল হিসাব / ভুল উত্তর', 'agent',
     'মডেল ডেটা ঠিকমতো পড়ে, কিন্তু হিসাব/গণনা/যুক্তিতে ভুল করে — তাই লেখা মানটি ভুল। '
     'Evaluator হুবহু মান মেলায় (কোনো সহনশীলতা নেই), তাই কাছাকাছি হলেও fail।'),
    ('A-INTENT', 'কাজটাই করেনি / ভুল কাজ করেছে', 'agent',
     'মডেল টাস্ক ভুল বোঝে বা প্রয়োজনীয় ক্রিয়াটি করেই না — যেমন ফাইল সরায় না, নতুন সারি যোগ করে না, '
     'অথবা action-টাস্ককে প্রশ্ন ভেবে শুধু টেক্সট উত্তর দেয়।'),
    ('A-ACTION', 'আটকে যাওয়া / ২০ ধাপ শেষ', 'agent',
     'লম্বা multi-app workflow-এ মডেল পথ হারায় — একই ভুল action বারবার করে আটকে যায় (got_stuck), '
     'অথবা ২০ ধাপের মধ্যে কাজ শেষ করতে পারে না।'),
    ('A-STATE', 'যা দেখেছে তা উপেক্ষা', 'agent',
     'পরিবেশে দেখা তথ্য অগ্রাহ্য করে — যেমন একটা সময় ইতিমধ্যে দখল করা জেনেও সেখানেই ইভেন্ট বসায় (overlap)।'),
    ('EVAL-MISMATCH', 'check টাস্কের বাইরে চায়', 'bench',
     'Benchmark-এর দোষ: টাস্ক শুধু "খুঁজে বের করো" বলে, কিন্তু evaluator একটা নির্দিষ্ট event/keyword '
     'দাবি করে যা টাস্ক কখনো তৈরি করতে বলেনি। মডেলের উত্তর যুক্তিসঙ্গত, তবু fail।'),
    ('C-HARNESS', 'infra/সেভ সমস্যা', 'bench',
     'পরিবেশ/হারনেসের সমস্যা: যেমন Windows-এ colon-যুক্ত ফাইলনাম docker cp করতে না পারা — '
     'মডেলের দোষ নয়।'),
]


def categorize(tid, sid, tag):
    d = f'tasks/{tid}/outputs/{sid}/{tag}'
    if not os.path.exists(f'{d}/env_history.json'):
        return 'C-HARNESS'
    env = json.load(open(f'{d}/env_history.json', encoding='utf-8'))
    with contextlib.redirect_stdout(io.StringIO()):
        passed, reason = evaluate(tid, sid, f'./{d}/testbed')
    if passed:
        return None
    last = env[-1][0] if env else None
    lname = last.get('action') if isinstance(last, dict) else None
    mal = sum('Malformed' in str(o) for _, o in env)
    if lname == 'got_stuck' or mal >= 3:
        return 'A-ACTION'
    if lname != 'finish_task':
        return 'A-ACTION'
    if 'calendar_no_overlap' in reason:
        return 'A-STATE'
    if 'evaluate_contain' in reason and 'ics' in reason:
        return 'EVAL-MISMATCH'
    if 'excel_cell' in reason or 'file_exist' in reason:
        return 'A-INTENT' if 'file_exist' in reason else 'A-REASON'
    return 'A-REASON'


def tally(tag):
    c = Counter()
    for cfg in glob.glob('tasks/*/subtasks/*.json'):
        p = cfg.replace(os.sep, '/'); tid, sid = p.split('/')[1], p.split('/')[3][:-5]
        k = categorize(tid, sid, tag)
        if k:
            c[k] += 1
    return c


EN = tally('gemma4_31b_think')
BN = tally('gemma4_31b_bn')
EN_TOT, BN_TOT = sum(EN.values()), sum(BN.values())

styles = getSampleStyleSheet()
H1 = ParagraphStyle('H1', parent=styles['Title'], fontName=BN_BOLD, textColor=INK, fontSize=19, leading=25, spaceAfter=2)
SUBT = ParagraphStyle('SUBT', parent=styles['Normal'], fontName=BN_FONT, textColor=MUTED, fontSize=9.5, leading=14)
H2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName=BN_BOLD, textColor=INK, fontSize=14, leading=19, spaceBefore=14, spaceAfter=4)
H3 = ParagraphStyle('H3', parent=styles['Heading3'], fontName=BN_BOLD, textColor=INK, fontSize=11.5, leading=16, spaceBefore=8, spaceAfter=2)
BODY = ParagraphStyle('BODY', parent=styles['Normal'], fontName=BN_FONT, textColor=INK, fontSize=10, leading=16)
SMALL = ParagraphStyle('SMALL', parent=styles['Normal'], fontName=BN_FONT, textColor=MUTED, fontSize=8.5, leading=13)
EX = ParagraphStyle('EX', parent=styles['Normal'], fontName=BN_FONT, textColor=INK, fontSize=9.5, leading=15,
                    leftIndent=8, borderPadding=(6, 6, 6, 6), backColor=BAND)

story = []
def P(t, s=BODY): story.append(Paragraph(t, s))
def rule(): story.append(Spacer(1, 4)); story.append(HRFlowable(width='100%', thickness=0.6, color=LINE)); story.append(Spacer(1, 4))

P('OfficeBench — কেন টাস্ক fail হয়', H1)
P('gemma4:31b · বিস্তারিত ব্যর্থতা বিশ্লেষণ · ইংরেজি ও বাংলা রান · ৩০০ সাবটাস্ক', SUBT)
rule()

P('১. কীভাবে মাপা হয় (সংক্ষেপে)', H2)
P('প্রতিটি টাস্কে এজেন্টকে ২০ ধাপ পর্যন্ত কাজ করতে দেওয়া হয়: সে app-এ switch করে, action (JSON) '
  'চালায়, ফলাফল দেখে, আবার সিদ্ধান্ত নেয়। শেষে benchmark-এর নিজস্ব স্বয়ংক্রিয় check (যেমন এক্সেল সেলের '
  'মান মেলানো, ফাইল আছে কিনা, ক্যালেন্ডারে overlap আছে কিনা) দিয়ে pass/fail ঠিক হয়। একটি টাস্ক তখনই '
  'pass যখন তার সব check পাস করে।')

P('২. সার্বিক ফলাফল', H2)
data = [['', 'ইংরেজি', 'বাংলা'],
        ['Pass', '132 / 300  (44.0%)', '103 / 300  (34.3%)'],
        ['Fail', f'{EN_TOT} / 300', f'{BN_TOT} / 300']]
t = Table(data, colWidths=[40*mm, 60*mm, 60*mm])
t.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Nirmala'), ('FONTSIZE', (0, 0), (-1, -1), 10), ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Nirmala-Bold'),
    ('FONTNAME', (0, 1), (0, -1), 'Nirmala-Bold'), ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
    ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
story.append(Spacer(1, 4)); story.append(t); story.append(Spacer(1, 6))

en_agent = sum(EN[k] for k, _, s, _ in CATS if s == 'agent')
en_bench = EN_TOT - en_agent
P(f'<b>দোষ কার:</b> ইংরেজি রানে {EN_TOT}টি fail-এর মধ্যে <b>{en_agent} ({100*en_agent//EN_TOT}%) মডেলের '
  f'নিজের সীমাবদ্ধতা</b>, মাত্র {en_bench} ({100*en_bench//EN_TOT}%) benchmark/infra-এর সমস্যা। '
  'অর্থাৎ ৪৪% স্কোর মূলত মডেলের আসল সামর্থ্যই দেখায়, benchmark bug-এর কারণে কৃত্রিমভাবে কম নয়।')

P('৩. ব্যর্থতার ধরন — গণনা', H2)
rows_t = [['ধরন', 'কী', 'দোষ', 'ইংরেজি', 'বাংলা']]
order = ['A-REASON', 'A-INTENT', 'A-ACTION', 'A-STATE', 'EVAL-MISMATCH', 'C-HARNESS']
meta = {c[0]: c for c in CATS}
for k in order:
    _, title, side, _ = meta[k]
    rows_t.append([k, title, 'মডেল' if side == 'agent' else 'বেঞ্চমার্ক',
                   f'{EN.get(k,0)} ({100*EN.get(k,0)//EN_TOT}%)', f'{BN.get(k,0)} ({100*BN.get(k,0)//BN_TOT}%)'])
bt = Table(rows_t, colWidths=[26*mm, 52*mm, 22*mm, 26*mm, 26*mm])
bt.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Nirmala'), ('FONTSIZE', (0, 0), (-1, -1), 8.7), ('BACKGROUND', (0, 0), (-1, 0), BAND),
    ('FONTNAME', (0, 0), (-1, 0), 'Nirmala-Bold'), ('TEXTCOLOR', (0, 0), (-1, -1), INK),
    ('FONTNAME', (0, 1), (0, -1), 'Nirmala-Bold'), ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
    ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
story.append(Spacer(1, 4)); story.append(bt)

P('৪. প্রতিটি ধরন — ব্যাখ্যা ও বাস্তব উদাহরণ', H2)
EXAMPLES = {
    'A-REASON': ('1-5/3 — "বাজেট ৩ বছরে ১০% হারে বাড়লে predicted budget যোগ করো"',
                 'প্রত্যাশিত: <b>2,729,881</b> (= 2,051,000 × 1.1³)। মডেল লিখেছে <b>2,730,381</b> — '
                 'compounding-এ সামান্য ভুল, ৫০০ বেশি। check হুবহু মান চায়, তাই fail।'),
    'A-INTENT': ('1-3/4 — "সব docx/pdf/image ফাইল new_dir ফোল্ডারে সরাও"',
                 'মডেল ফাইলগুলো <b>সরায়ইনি</b> — new_dir তৈরি হয়নি, data/-তে ফাইল আগের জায়গাতেই। '
                 'বদলে একটা answer.txt লিখেছে, অর্থাৎ action-টাস্ককে প্রশ্ন ভেবেছে। '
                 '(1-4/2-তেও "annual bonus 50000" নতুন সারি যোগ করেনি।)'),
    'A-ACTION': ('3-10/0 — "প্রতিটি প্রাপকের জন্য ফোল্ডার বানাও ও বিল লেখো"',
                 'মডেল একই shell কমান্ড (echo ... > Alice/mobile_bill.txt) বারবার চালিয়ে ২০ ধাপ শেষ করে ফেলে — '
                 'লম্বা workflow-এ পথ হারিয়ে আটকে যায়।'),
    'A-STATE': ('1-2/1 — "Bob ও Tom কি একসাথে ডিনার করতে পারে? সময় যোগ করো"',
                 'দুজনেরই ১৮:৩০–১৯:৩০-এ আগে থেকেই "dinner" আছে। মডেল সেটা দেখেও ঠিক ওই সময়েই নতুন '
                 'ডিনার বসায় → overlap → no-overlap check fail।'),
    'EVAL-MISMATCH': ('1-2/0 — "Bob ও Tom-এর এক ঘণ্টার মিটিংয়ের সময় খুঁজে বের করো"',
                      'টাস্ক শুধু "খুঁজে বের করতে" বলে; মডেল সঠিক সময় (14:30–15:30) দেয়। কিন্তু evaluator '
                      'ক্যালেন্ডারে "meeting" keyword-যুক্ত event দাবি করে, যা টাস্ক বানাতে বলেনি → fail। '
                      'এটা benchmark-এর কড়াকড়ি, মডেলের ভুল নয়।'),
    'C-HARNESS': ('3-52/0 — "মিটিং এজেন্ডা বানিয়ে ইমেইল করো"',
                  'মডেল একটা ইমেইল ফাইল বানায় যার নামে colon আছে ("Meeting Reminder: Agenda.eml")। '
                  'Linux-এ বৈধ, কিন্তু Windows-এ docker cp সেটা কপি করতে পারে না → ফলাফল সেভ হয় না। '
                  'পরিবেশের সীমাবদ্ধতা, মডেলের দোষ নয়।'),
}
for k in order:
    _, title, side, why = meta[k]
    ex_title, ex_body = EXAMPLES[k]
    blk = [Paragraph(f'{k} — {title}  '
                     f'<font color="{"#b8392f" if side=="agent" else "#9a6516"}">[{("মডেল" if side=="agent" else "বেঞ্চমার্ক")}]</font>', H3),
           Paragraph('<b>কেন:</b> ' + why, BODY),
           Paragraph(f'<b>উদাহরণ — {ex_title}</b><br/>{ex_body}', EX),
           Spacer(1, 4)]
    story.append(KeepTogether(blk))

P('৫. ইংরেজি বনাম বাংলা — ভাষা কীভাবে ব্যর্থতা বাড়ায়', H2)
cmp = [['ক্যাটেগরি', 'ইংরেজি pass', 'বাংলা pass', 'পার্থক্য'],
       ['১ অ্যাপ (93)', '66.7%', '45.2%', '−21.5%'],
       ['২ অ্যাপ (95)', '54.7%', '45.3%', '−9.4%'],
       ['৩ অ্যাপ (112)', '16.1%', '16.1%', '0%'],
       ['সব মিলিয়ে', '44.0%', '34.3%', '−9.7%']]
ct = Table(cmp, colWidths=[40*mm, 34*mm, 34*mm, 30*mm])
ct.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Nirmala'), ('FONTSIZE', (0, 0), (-1, -1), 9), ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white), ('FONTNAME', (0, 0), (-1, 0), 'Nirmala-Bold'),
    ('FONTNAME', (0, -1), (-1, -1), 'Nirmala-Bold'), ('BACKGROUND', (0, -1), (-1, -1), BAND),
    ('TEXTCOLOR', (3, 1), (3, 3), FAIL), ('LINEBELOW', (0, 0), (-1, -1), 0.4, LINE),
    ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4)]))
story.append(Spacer(1, 4)); story.append(ct); story.append(Spacer(1, 6))
P('বাংলা নির্দেশনায় একই মডেল <b>বেশি ভুল উত্তর (A-REASON)</b> দেয় — ইংরেজিতে fail-এর ৩৯% ছিল A-REASON, '
  'বাংলায় তা <b>৪৮%</b>। মানে ভাষা বদলালে মূলত মডেলের বোঝা ও হিসাবের ভুল বাড়ে, নতুন ধরনের ব্যর্থতা নয়।', BODY)
P('<b>লক্ষণীয়:</b> ১-অ্যাপ টাস্কে ভাষার প্রভাব সবচেয়ে বেশি (−21.5%), কিন্তু ৩-অ্যাপ টাস্কে কোনো পার্থক্য নেই '
  '(১৬.১% = ১৬.১%)। কারণ ৩-অ্যাপ টাস্ক এমনিতেই মডেলের সাধ্যের বাইরে — সেখানে দু-ভাষাতেই প্রায় সব fail করে, '
  'তাই ভাষা আর গুরুত্ব রাখে না। ভাষার প্রভাব সেখানেই দেখা যায় যেখানে মডেলের কাজটা করার সামর্থ্য আছে।', BODY)

P('৬. সারসংক্ষেপ', H2)
story.append(ListFlowable([
    ListItem(Paragraph('প্রায় সব ব্যর্থতা (ইংরেজিতে ~94%, বাংলায় ~95%) <b>মডেলের নিজের সীমাবদ্ধতা</b> — '
                       'ভুল হিসাব, কাজটা না করা, বা লম্বা workflow-এ আটকে যাওয়া।', BODY)),
    ListItem(Paragraph('মাত্র ~5-6% benchmark/infra-এর সমস্যা (check বেশি চায়, বা Windows সেভ সমস্যা)।', BODY)),
    ListItem(Paragraph('সবচেয়ে বড় একক কারণ <b>ভুল মান/হিসাব (A-REASON)</b>, এরপর কাজ-না-করা ও আটকে-যাওয়া।', BODY)),
    ListItem(Paragraph('৩-অ্যাপ টাস্ক সবচেয়ে কঠিন (উভয় ভাষায় ~16%) — লম্বা multi-app planning মডেলের মূল দুর্বলতা।', BODY)),
    ListItem(Paragraph('বাংলা নির্দেশনা performance ~10 পয়েন্ট কমায়, মূলত বোঝা ও হিসাবের ভুল বাড়িয়ে।', BODY)),
], bulletType='bullet', start='•'))

doc = SimpleDocTemplate(OUT, pagesize=A4, topMargin=15*mm, bottomMargin=15*mm, leftMargin=16*mm, rightMargin=16*mm,
                        title='OfficeBench — Why Tasks Fail', author='OfficeBench analysis')
doc.build(story)
print('wrote', OUT, os.path.getsize(OUT)//1024, 'KB')
