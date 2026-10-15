"""Build the gemma4:31b WorkBench-on-OfficeBench report (HTML), then print it to PDF with Edge.

    python wb_bench/report/build_report.py

Every per-run number is read from wb_bench/tasks/*/outputs/<lang>/gemma4_31b_wb1/result.json.
Numbers about the earlier WorkBench study are quoted from WORKBENCH_FAILURE_ANALYSIS.pdf
(C:/Users/Lenovo/Music); numbers about the 300-task OfficeBench runs from results/*.jsonl.
"""
import glob
import html
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TAG = 'gemma4_31b_wb1'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

NAMES = {
    'T03': 'Send an email (body + subject)', 'T10': 'Cancel my first meeting on a date',
    'T13': 'Cancel the next {event} meeting', 'T15': 'Cancel my next meeting with {name}',
    'T16': 'If not met {name} in N days, book 30-min catch-up', 'T17': 'Cancel meetings on a day after a time',
    'T18': 'Cancel all future meetings with {name}', 'T19': 'Cancel all future {event} meetings',
    'T20': 'Create a 1.5-hour event at a date/time', 'T54': 'If not met {name} in N days, send email',
    'T55': 'If no meeting with {name} in next N days, send email',
}
# Failures that come from my grader's assumptions, not from a wrong action (see section 3).
GRADER_ASSUMPTION = {('T16.v2', 'en'), ('T16.v3', 'en'), ('T20.v1', 'en'), ('T20.v1', 'bn')}


def load():
    rows = []
    for p in glob.glob(os.path.join(ROOT, 'wb_bench', 'tasks', '*', 'outputs', '*', TAG, 'result.json')):
        rows.append(json.load(open(p, encoding='utf-8')))
    return sorted(rows, key=lambda r: (r['variant'], r['lang']))


def pct(a, b):
    return f'{100 * a / b:.1f}%'


def ob300():
    out = {}
    for tag, lang in (('think', 'en'), ('bn', 'bn')):
        rs = [json.loads(l) for l in open(os.path.join(ROOT, 'results', f'gemma4_31b_{tag}_result.jsonl'))]
        out[lang] = (sum(r['is_pass'] for r in rs), len(rs))
    return out


def main():
    rows = load()
    assert len(rows) == 66, len(rows)
    by = {(r['variant'], r['lang']): r for r in rows}
    en = [r for r in rows if r['lang'] == 'en']
    bn = [r for r in rows if r['lang'] == 'bn']
    en_p, bn_p = sum(r['pass'] for r in en), sum(r['pass'] for r in bn)
    en_l = en_p + sum(1 for r in en if not r['pass'] and (r['variant'], 'en') in GRADER_ASSUMPTION)
    bn_l = bn_p + sum(1 for r in bn if not r['pass'] and (r['variant'], 'bn') in GRADER_ASSUMPTION)
    errors = sum(1 for r in rows if r.get('error'))
    steps_en = sum(r['steps'] for r in en) / len(en)
    steps_bn = sum(r['steps'] for r in bn) / len(bn)
    ob = ob300()

    tmpl_rows = ''
    for t in sorted(NAMES):
        e = [by[(f'{t}.v{i}', 'en')]['pass'] for i in (1, 2, 3)]
        b = [by[(f'{t}.v{i}', 'bn')]['pass'] for i in (1, 2, 3)]
        def cell(xs):
            s = sum(xs)
            cls = 'ok' if s == 3 else 'bad'
            return f'<td class="num {cls}">{s}/3</td>'
        tmpl_rows += f'<tr><td>{t}</td><td>{html.escape(NAMES[t])}</td>{cell(e)}{cell(b)}</tr>'

    run_rows = ''
    for t in sorted(NAMES):
        for i in (1, 2, 3):
            v = f'{t}.v{i}'
            for lang in ('en', 'bn'):
                r = by[(v, lang)]
                res = 'PASS' if r['pass'] else ('FAIL*' if (v, lang) in GRADER_ASSUMPTION else 'FAIL')
                cls = 'ok' if r['pass'] else 'bad'
                run_rows += (f'<tr><td>{v}</td><td>{lang.upper()}</td><td class="task" lang="{lang}">'
                             f'{html.escape(r["task"])}</td><td class="num">{r["steps"]}</td>'
                             f'<td class="num {cls}">{res}</td></tr>')

    doc = TEMPLATE.format(
        en_p=en_p, bn_p=bn_p, en_pct=pct(en_p, 33), bn_pct=pct(bn_p, 33),
        en_l=en_l, bn_l=bn_l, en_lpct=pct(en_l, 33), bn_lpct=pct(bn_l, 33),
        errors=errors, steps_en=f'{steps_en:.1f}', steps_bn=f'{steps_bn:.1f}',
        ob_en=ob['en'][0], ob_en_n=ob['en'][1], ob_en_pct=pct(*ob['en']),
        ob_bn=ob['bn'][0], ob_bn_n=ob['bn'][1], ob_bn_pct=pct(*ob['bn']),
        tmpl_rows=tmpl_rows, run_rows=run_rows)
    html_path = os.path.join(HERE, 'gemma4_31b_workbench_on_officebench.html')
    open(html_path, 'w', encoding='utf-8').write(doc)
    pdf_path = os.path.join(HERE, 'gemma4_31b_workbench_on_officebench.pdf')
    profile = os.path.join(os.environ.get('TEMP', HERE), 'edge_pdf_profile')
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--user-data-dir={profile}',
                    '--no-first-run', '--no-default-browser-check',
                    f'--print-to-pdf={pdf_path}', 'file:///' + html_path.replace('\\', '/')],
                   check=True, capture_output=True, timeout=120)
    print(pdf_path)


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>gemma4:31b on WorkBench templates in OfficeBench</title>
<style>
@page {{ size: A4; margin: 16mm 15mm 16mm 15mm; }}
body {{ font-family: "Segoe UI", "Nirmala UI", Arial, sans-serif; font-size: 10pt; color: #1d1d1f; line-height: 1.45; }}
[lang="bn"] {{ font-family: "Nirmala UI", "Vrinda", sans-serif; }}
h1 {{ font-size: 18pt; margin: 0 0 4pt 0; }}
h2 {{ font-size: 13pt; margin: 16pt 0 6pt 0; border-bottom: 1.5pt solid #2f5d8a; padding-bottom: 2pt; color: #1f3f63; }}
h3 {{ font-size: 11pt; margin: 10pt 0 4pt 0; }}
.sub {{ color: #555; font-size: 9pt; margin-bottom: 10pt; }}
.box {{ background: #f2f6fa; border-left: 3pt solid #2f5d8a; padding: 7pt 10pt; margin: 8pt 0; }}
.warn {{ background: #fdf5e8; border-left: 3pt solid #c47a00; padding: 7pt 10pt; margin: 8pt 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 6pt 0 8pt 0; font-size: 9pt; }}
th, td {{ border: 0.6pt solid #c9d1da; padding: 3pt 5pt; vertical-align: top; text-align: left; }}
th {{ background: #e6edf4; }}
td.num, th.num {{ text-align: center; white-space: nowrap; }}
.ok {{ color: #1f6b35; font-weight: 600; }}
.bad {{ color: #a32020; font-weight: 600; }}
td.task {{ font-size: 8.5pt; }}
.kpis {{ display: flex; gap: 8pt; margin: 8pt 0; }}
.kpi {{ flex: 1; border: 0.8pt solid #c9d1da; border-radius: 4pt; padding: 6pt 8pt; }}
.kpi b {{ display: block; font-size: 15pt; color: #1f3f63; }}
.kpi span {{ font-size: 8.5pt; color: #555; }}
ul {{ margin: 4pt 0 4pt 16pt; padding: 0; }} li {{ margin: 2pt 0; }}
code {{ font-family: Consolas, monospace; font-size: 8.8pt; background: #f1f1f1; padding: 0 2pt; }}
.small {{ font-size: 8.5pt; color: #555; }}
.pb {{ page-break-before: always; }}
tr {{ page-break-inside: avoid; }}
</style></head><body>

<h1>gemma4:31b on WorkBench templates, run in OfficeBench</h1>
<div class="sub">English vs Bangla &middot; 11 templates &times; 3 variants &times; 2 languages = 66 runs &middot; run 2026-10-10 &middot;
tag <code>wb1</code> &middot; generated by <code>wb_bench/report/build_report.py</code> from the 66 <code>result.json</code> files</div>

<h2>Summary</h2>
<div class="kpis">
 <div class="kpi"><b>{en_p}/33</b><span>English, strict ({en_pct})</span></div>
 <div class="kpi"><b>{bn_p}/33</b><span>Bangla, strict ({bn_pct})</span></div>
 <div class="kpi"><b>{en_l}/33 &middot; {bn_l}/33</b><span>EN &middot; BN, counting grader-assumption failures as passes</span></div>
 <div class="kpi"><b>{errors}</b><span>runs with a crash or harness error</span></div>
</div>
<ul>
 <li><b>All 66 runs completed without errors.</b> Strict score: English {en_p}/33, Bangla {bn_p}/33.</li>
 <li><b>Only one of the five failures is a real model mistake</b> (T15.v1, Bangla: it deleted two meetings with Dana instead of the next one).
 The other four come from my grader's assumptions: a 9:00 workday start (T16) and an exact event title (T20).</li>
 <li><b>No English&ndash;Bangla difference is visible</b> on these 11 templates: the model is near the ceiling in both languages.
 This agrees with the earlier WorkBench study (gemma4:31b 81.1% English vs 82.2% Bangla on 90 tasks, McNemar p = 1.000).</li>
 <li><b>One failure pattern repeats across both environments:</b> in WorkBench and here, gemma's English T16 runs ("book a catch-up at my
 first free slot") pick a different slot than expected, while the Bangla runs pick the expected one.</li>
 <li><b>OfficeBench needed two fixes to run these tasks at all:</b> its <code>delete_event</code> action can never delete an event (two bugs),
 and my grader had to ignore the sent copy that <code>send_email</code> files in the sender's folder. Neither bug affects your
 earlier 300-task OfficeBench scores, because none of those tasks deletes a calendar event.</li>
</ul>

<h2>1. What was run</h2>
<p>The Bangla translations in <code>batch_1..5.csv</code> are WorkBench templates (T01&ndash;T69). OfficeBench has only email (list, read,
send to one recipient), calendar (create, delete by exact title, list; no attendees, no edit), Excel, Word, PDF, OCR, shell and an LLM app.
It has no CRM, analytics or project-management app, so only 11 templates map onto OfficeBench's apps without workarounds.
They were run as OfficeBench tasks:</p>
<table>
<tr><th>Item</th><th>Setting</th></tr>
<tr><td>Templates</td><td>T03, T10, T13, T15, T16, T17, T18, T19, T20, T54, T55 (email and calendar; 3 phrasings each)</td></tr>
<tr><td>Languages</td><td>English template text and the Bangla translation from the CSVs; OfficeBench's Bangla system prompt (<code>lang=bn</code>) for Bangla runs</td></tr>
<tr><td>Model</td><td>gemma4:31b on ollama.com, temperature 0, at most 20 steps, one run per cell</td></tr>
<tr><td>Slot values</td><td>Chosen by me and identical in both languages (names Carlos, Dana, Lee, Priya; today Wed 2024-05-15 09:00; user Alice)</td></tr>
<tr><td>Starting state</td><td>A hand-built calendar of 15 events and 2 inbox emails, designed so each task has one correct end state</td></tr>
<tr><td>Scoring</td><td>Strict end-state check (<code>wb_bench/evaluate.py</code>): Alice's calendar must equal the expected set of (title, start, end),
and the delivered emails must equal the expected ones (recipient, subject, body phrase). Any extra change fails the run.</td></tr>
</table>
<div class="warn"><b>Not the same benchmark as WorkBench.</b> WorkBench has its own sandbox and ground truth. Here the slot values, starting
data and grader are mine, so the scores below are <i>not</i> directly comparable with WorkBench scores. Section 4 compares the patterns.</div>

<h2>2. Results</h2>
<table>
<tr><th>Template</th><th>Task</th><th class="num">English</th><th class="num">Bangla</th></tr>
{tmpl_rows}
<tr><th colspan="2">Total (strict)</th><th class="num">{en_p}/33</th><th class="num">{bn_p}/33</th></tr>
</table>
<p class="small">Mean steps per run: English {steps_en}, Bangla {steps_bn}.</p>

<h2>3. The five failures</h2>
<table>
<tr><th>Run</th><th>What the model did</th><th>Expected</th><th>Verdict</th></tr>
<tr><td>T15.v1 BN</td><td>Deleted "Meeting with Dana" (May 16) <b>and</b> "Project review with Dana" (May 20)</td><td>Delete only the next one (May 16)</td>
<td class="bad">Real error: over-deletion</td></tr>
<tr><td>T16.v2 EN</td><td>Booked "Catch up with Carlos" on May 16, 08:00&ndash;08:30</td><td>First free slot from 09:00: 09:30&ndash;10:00</td>
<td>Grader assumption (workday start)</td></tr>
<tr><td>T16.v3 EN</td><td>Booked "catch-up" on May 16, 08:00&ndash;08:30</td><td>09:30&ndash;10:00</td><td>Grader assumption (workday start)</td></tr>
<tr><td>T20.v1 EN</td><td>Created "Roadmap review with Dana", May 22 14:00&ndash;15:30</td><td>Title exactly "Roadmap review"</td>
<td>Grader assumption (exact title)</td></tr>
<tr><td>T20.v1 BN</td><td>Same as English</td><td>Title exactly "Roadmap review"</td><td>Grader assumption (exact title)</td></tr>
</table>
<ul>
<li><b>T16:</b> the template says "my first free slot from tomorrow" but never says when the workday starts. 08:00 is a defensible
reading; my grader assumed 09:00. All three Bangla T16 runs chose 09:30 and passed.</li>
<li><b>T20:</b> OfficeBench events have no attendee field, so adding the person's name to the title is a reasonable way to record
"with Dana". Time and duration were correct in both languages.</li>
<li><b>T15.v1 BN</b> is the only failure where the action itself is wrong. The model treated "the next meeting with Dana" as every upcoming
meeting with Dana. The other two Bangla phrasings of T15 passed.</li>
</ul>
<div class="box">Counting the four grader-assumption failures as passes gives <b>English {en_l}/33 and Bangla {bn_l}/33</b>.
Either way, the difference between languages is one run or fewer.</div>

<h2>4. Comparison with the earlier WorkBench study</h2>
<p>Source: <code>WORKBENCH_FAILURE_ANALYSIS.pdf</code> (generated 2026-10-10; WorkBench pilot, 90 tasks, 15 per domain; English condition C0 vs
Bangla condition C6; WorkBench's own end-state check; one run per cell at temperature 0). The WorkBench repository is not on this
machine, so tasks can only be matched to templates through the task descriptions quoted in that report.</p>
<h3>4.1 Overall and by domain (gemma4:31b, WorkBench)</h3>
<table>
<tr><th>Domain</th><th class="num">English</th><th class="num">Bangla</th><th>Relevance here</th></tr>
<tr><td>All 90 tasks</td><td class="num">73/90 (81.1%)</td><td class="num">74/90 (82.2%)</td><td>Gap &minus;1.1 pp, 95% CI [&minus;10.0, 7.8], McNemar p = 1.000</td></tr>
<tr><td>Email</td><td class="num">15/15</td><td class="num">14/15</td><td>T03 here: 3/3 and 3/3</td></tr>
<tr><td>Calendar</td><td class="num">13/15</td><td class="num">14/15</td><td>Most of the templates run here are calendar templates</td></tr>
<tr><td>Multi-domain</td><td class="num">8/15</td><td class="num">9/15</td><td>T54, T55 here: 3/3 and 3/3</td></tr>
<tr><td>gpt-oss:20b, all 90</td><td class="num">53/90 (58.9%)</td><td class="num">48/90 (53.3%)</td><td>Not run here</td></tr>
</table>
<h3>4.2 WorkBench tasks from the same templates</h3>
<table>
<tr><th>WorkBench task</th><th>Template</th><th>What the report found</th><th>What happened here</th></tr>
<tr><td>calendar:63 (gemma)</td><td>T16 (catch-up)</td><td>English failed: booked "catch-up" at 11:00, overlapping a 10:00&ndash;12:00 event; ground truth and
Bangla chose 13:00. Coded general model weakness (same slot error in multi_domain:84 and :200).</td>
<td>Same pattern: English T16.v2/v3 booked 08:00; all Bangla T16 runs chose the expected 09:30.</td></tr>
<tr><td>calendar:38 (gpt-oss)</td><td>T13 (cancel the next X)</td><td>English deleted the next "Quarterly Sales Review" <b>and</b> a past
one.</td><td>gemma deleted only the next "Team sync" in all 6 runs (6/6 pass).</td></tr>
<tr><td>calendar:84 (gpt-oss)</td><td>likely T18 (cancel all future meetings)</td><td>Deleted past meetings against "future" (English;
Bangla "&#2488;&#2494;&#2478;&#2472;&#2503;" likewise).</td><td>gemma kept the past events in all 12 T18/T19 runs (12/12 pass).</td></tr>
</table>
<p>The one real failure here (T15.v1 Bangla, deleting more meetings than asked) is the same kind of error as gpt-oss's calendar:38 in
WorkBench: a "next" or "future" constraint is not kept. In WorkBench this was coded general model weakness, because it also
happens in English.</p>
<div class="box"><b>Agreement:</b> both environments show no measurable English&ndash;Bangla gap for gemma4:31b on email and calendar
tasks. The genuine Bangla failures found in WorkBench (relative-date phrases such as "&#2455;&#2468; &#2488;&#2474;&#2509;&#2468;&#2494;&#2489;&#2503;")
come from templates that cannot run in OfficeBench (they need email dates or the analytics app), so this run could not test them.</div>

<h2>5. What happened in the OfficeBench environment</h2>
<h3>5.1 Context: the earlier 300-task OfficeBench runs</h3>
<table>
<tr><th>Run</th><th class="num">Passed</th></tr>
<tr><td>gemma4:31b, English (tag <code>think</code>)</td><td class="num">{ob_en}/{ob_en_n} ({ob_en_pct})</td></tr>
<tr><td>gemma4:31b, Bangla (tag <code>bn</code>)</td><td class="num">{ob_bn}/{ob_bn_n} ({ob_bn_pct})</td></tr>
</table>
<p class="small">OfficeBench's own 300 tasks are mostly file tasks (Excel, Word, PDF, OCR) plus email and calendar, and their gap
(about 10 points) is larger than on the WorkBench templates. Those runs are context only; they are not part of this report's 66 runs.</p>
<h3>5.2 Problems found in OfficeBench, and fixes</h3>
<table>
<tr><th>Problem</th><th>Effect</th><th>Fix (this run only; <code>apps/</code> untouched)</th></tr>
<tr><td><code>delete_event</code> wraps the title in <code>"..."</code>, which breaks inside the <code>bash -c</code> wrapper</td>
<td>"Vendor call" arrives as "Vendor"; nothing matches, yet the app reports "Successfully delete"</td><td>Quote it as <code>create_event</code> does</td></tr>
<tr><td><code>delete_event</code> calls <code>calendar.subcomponent.remove</code>; the attribute is <code>subcomponents</code></td>
<td>Every real delete raises an error and reports "Failed"; an existing event can never be deleted</td><td>Patched copy of the file copied into the container</td></tr>
<tr><td><code>send_email</code> also saves a sent copy in the sender's folder</td><td>My first grader counted it as an extra email</td>
<td>Grader ignores the sender's own folder; all runs regraded</td></tr>
<tr><td><code>list_events</code> takes <code>username</code>, while <code>create_event</code>/<code>delete_event</code> take <code>user</code></td>
<td>A model that reuses the argument name gets "Malformed action" (seen once in a pilot)</td><td>Not changed (part of the benchmark)</td></tr>
</table>
<div class="box"><b>Correction to an earlier claim.</b> I first said the <code>delete_event</code> bugs affected your earlier 300-task
OfficeBench scores. They did not: a check of all 300 task texts found no task that deletes or cancels a calendar event (the "delete" tasks
are about Excel rows and files). The bugs matter only for tasks like the WorkBench templates, where 8 of the 11 templates delete events.</div>
<h3>5.3 Run history</h3>
<ul>
<li>A pilot (T10.v1) failed in both languages and exposed the two <code>delete_event</code> bugs. Every T10 run made before the fix
was deleted and rerun.</li>
<li>One restart was wasted by my own mistake: the patched apps were copied to <code>/apps_patched</code> instead of <code>/apps</code>.
Those runs were deleted and rerun.</li>
<li>The machine rebooted at 04:19 because memory and disk ran out (C: dropped to 0.02 GB free; Windows paging file on C:). After
the reboot, Docker Desktop would not start until stale socket files in <code>AppData\Local\Docker\run</code> and
<code>docker-secrets-engine</code> were moved aside. The WSL swap file was moved to <code>D:\WSL</code> and the WSL VM capped at 4 GB.</li>
<li>The run resumed at 05:26 and finished at 05:40. None of the 66 graded runs has a harness error; finished runs were never rerun.</li>
</ul>

<h2>6. Limits</h2>
<ul>
<li><b>Small and easy:</b> 33 runs per language on the 11 simplest templates; the model is near the ceiling, so the run cannot show a gap of a
few points (WorkBench's 90-task interval already allows up to about 8 points).</li>
<li><b>One run per cell</b> at temperature 0; run-to-run variation is not measured.</li>
<li><b>My slot values, starting data and grader.</b> Different choices (for example a 08:00 workday) would change T16 and T20.</li>
<li><b>Translations:</b> the Bangla text is taken from the CSVs unchanged. It uses ASCII digits (for example "30 &#2478;&#2495;&#2472;&#2495;&#2463;&#2503;&#2480;"), and person
and event names stay in Latin script. Native-speaker review is still pending, as in the WorkBench study.</li>
</ul>

<div class="pb"></div>
<h2>Appendix: all 66 runs</h2>
<p class="small">FAIL* = failed only because of a grader assumption (section 3). Task text is exactly what the model received.</p>
<table>
<tr><th>Variant</th><th>Lang</th><th>Task text</th><th class="num">Steps</th><th class="num">Result</th></tr>
{run_rows}
</table>
</body></html>
'''

if __name__ == '__main__':
    main()
