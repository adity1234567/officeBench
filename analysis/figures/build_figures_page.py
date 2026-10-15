"""Inline analysis/figures/*.svg into a single viewable page (analysis/figures/figures.html).

    python analysis/figures/make_fig0_teaser.py      # regenerate the teaser from the run data
    python analysis/figures/build_figures_page.py    # then rebuild the page
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
read = lambda n: open(os.path.join(HERE, n), encoding='utf-8').read().strip()

# strip the XML namespace decl (not needed inline) and keep everything else as drawn
inline = lambda s: re.sub(r'\s+xmlns="[^"]*"', '', s)

FIGS = inline(read('fig_steps.svg'))
FIG0 = inline(read('fig0_teaser.svg'))
FIG1 = inline(read('fig1_study_design.svg'))
FIG2 = inline(read('fig2_failure_coding.svg'))

PAGE = """<title>OfficeBench Method Figures</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Noto+Sans+Bengali:wght@400;600&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap">
<style>
/* layout: one column of full-bleed figures, the interactive teaser first, each with its claim underneath */
:root {
  --bg: #fbfaf8;
  --surface: #ffffff;
  --ink: #1b2330;
  --muted: #5e6675;
  --rule: #e2ded7;
  --accent: #b4650a;
  --ok: #1a7f4b;
  --bad: #b3391f;
  --serif: "Source Serif 4", Georgia, "Times New Roman", serif;
  --sans: "IBM Plex Sans", "Noto Sans Bengali", ui-sans-serif, system-ui, "Segoe UI", Helvetica, Arial, sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #14171c; --surface: #1b1f26; --ink: #e8e6e1; --muted: #9aa2ae;
    --rule: #2e343d; --accent: #f0a93b; --ok: #4cb37c; --bad: #e07a5f; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #14171c; --surface: #1b1f26; --ink: #e8e6e1; --muted: #9aa2ae;
  --rule: #2e343d; --accent: #f0a93b; --ok: #4cb37c; --bad: #e07a5f; color-scheme: dark;
}
body { background: var(--bg); color: var(--ink); font-family: var(--sans); }
.wrap { max-width: 1180px; margin: 0 auto; padding-inline: 20px; padding-block: 40px 56px;
        display: flex; flex-direction: column; gap: 40px; }
header { display: flex; flex-direction: column; gap: 10px; border-bottom: 1px solid var(--rule); padding-bottom: 22px; }
h1 { font-family: var(--serif); font-size: clamp(26px, 4vw, 34px); font-weight: 600; line-height: 1.15;
     margin: 0; text-wrap: balance; letter-spacing: -0.01em; }
.standfirst { margin: 0; color: var(--muted); font-size: 15px; line-height: 1.55; max-width: 66ch; }
.eyebrow { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent); font-weight: 600; }
figure { margin: 0; display: flex; flex-direction: column; gap: 14px; }
.plate { background: var(--surface); border: 1px solid var(--rule); border-radius: 4px;
         padding: 18px; overflow-x: auto; }
.plate svg { display: block; width: 100%; min-width: 760px; height: auto;
             color: var(--ink); font-family: var(--sans); }
#teaser svg { min-width: 940px; }
#steps svg { min-width: 980px; }
/* the drawn files carry literal hues so they stand alone; the page maps them onto its tokens */
.plate svg [fill="#d97706"] { fill: var(--accent); }
.plate svg [stroke="#d97706"] { stroke: var(--accent); }
.plate svg [fill="#1a7f4b"] { fill: var(--ok); }
.plate svg [stroke="#1a7f4b"] { stroke: var(--ok); }
.plate svg [fill="#b3391f"] { fill: var(--bad); }
.plate svg [stroke="#b3391f"] { stroke: var(--bad); }
figcaption { font-family: var(--serif); font-size: 15.5px; line-height: 1.55; max-width: 72ch; color: var(--ink); }
figcaption b { font-weight: 600; }
figcaption span { color: var(--muted); }

/* --- interactive teaser --- */
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.controls .sep { flex: 1 1 12px; }
button { font: inherit; font-size: 12.5px; color: var(--ink); background: var(--surface);
         border: 1px solid var(--rule); border-radius: 999px; padding: 5px 13px; cursor: pointer;
         transition: background .12s, border-color .12s, color .12s; }
button:hover { border-color: var(--accent); }
button[aria-pressed="true"] { background: color-mix(in srgb, var(--accent) 16%, transparent);
                              border-color: var(--accent); color: var(--accent); font-weight: 600; }
button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.t0-stage { transition: opacity .18s; cursor: pointer; }
.t0-stage.dim { opacity: .18; }
.s-step, .s-arrow { transition: opacity .18s; }
.s-step { cursor: pointer; }
.s-step.dim, .s-arrow.dim { opacity: .16; }
.s-step.on .s-card { stroke: var(--accent); stroke-opacity: .9; stroke-width: 1.8; }
.s-arrow.on { stroke: var(--accent); stroke-opacity: 1; stroke-width: 2.4; }
.s-out { cursor: help; }
.t0-hot { pointer-events: all; cursor: help; }
.t0-hot:hover { stroke-opacity: 1; }
.readout { display: flex; gap: 10px; align-items: baseline; min-height: 40px;
           border-left: 3px solid var(--accent); padding: 8px 0 8px 12px; font-size: 13px;
           line-height: 1.5; color: var(--ink); }
.readout .tag { font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted);
                font-weight: 600; flex: none; padding-top: 2px; }
.readout .val { min-width: 0; }
@media (prefers-reduced-motion: reduce) { .t0-stage, .s-step, .s-arrow, button { transition: none; } }

.note { border-top: 1px solid var(--rule); padding-top: 20px; display: flex; flex-direction: column; gap: 10px;
        font-size: 13.5px; line-height: 1.6; color: var(--muted); max-width: 80ch; }
.note h2 { font-family: var(--sans); font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase;
           color: var(--ink); margin: 0 0 2px; font-weight: 600; }
code { font-family: ui-monospace, "Cascadia Code", Consolas, monospace; font-size: 12.5px;
       background: var(--surface); border: 1px solid var(--rule); border-radius: 3px; padding: 1px 5px; }
@media (max-width: 640px) { .plate { padding: 12px; } }
</style>

<div class="wrap">
  <header>
    <div class="eyebrow">OfficeBench &middot; method figures</div>
    <h1>Where the runs come from, and how their failures are named</h1>
    <p class="standfirst">Four figures for the paper. The first is the general pipeline, step by step; the second walks one real
      subtask through it; the last two are the apparatus and the coding instrument in detail. Every number and
      every quoted string is from the runs themselves, as of 2026-10-04.</p>
  </header>

  <figure>
    <div class="controls">
      <span class="eyebrow" style="margin-right:4px">Steps</span>
      <button id="s-play" type="button">&#9654; Play</button>
      <button data-sstep="all" aria-pressed="true">All</button>
      <button data-sstep="1" aria-pressed="false">1 &middot; Collect</button>
      <button data-sstep="2" aria-pressed="false">2 &middot; Run</button>
      <button data-sstep="3" aria-pressed="false">3 &middot; Score</button>
      <button data-sstep="4" aria-pressed="false">4 &middot; Characterize</button>
      <button data-sstep="5" aria-pressed="false">5 &middot; Compare</button>
    </div>
    <div class="plate" id="steps">__FIGS__</div>
    <p class="readout"><span class="tag">Detail</span><span class="val" id="s-readout"></span></p>
    <figcaption><b>Figure 1. The pipeline, step by step.</b> <span>Tasks go in; each step turns the previous
      step&rsquo;s output into the next: a trace and final files, a pass or fail per run, one root-cause code per
      failure, and finally findings that say what to fix first.</span></figcaption>
  </figure>

  <figure>
    <div class="controls">
      <span class="eyebrow" style="margin-right:4px">Isolate a stage</span>
      <button data-stage="all" aria-pressed="true">All</button>
      <button data-stage="1" aria-pressed="false">1 &middot; Task</button>
      <button data-stage="2" aria-pressed="false">2 &middot; Run</button>
      <button data-stage="3" aria-pressed="false">3 &middot; Scoring</button>
      <button data-stage="4" aria-pressed="false">4 &middot; Code</button>
      <span class="sep"></span>
      <span class="eyebrow" style="margin-right:4px">Prompt language</span>
      <button data-lang="en" aria-pressed="true">English</button>
      <button data-lang="bn" aria-pressed="false" lang="bn">&#2476;&#2494;&#2434;&#2482;&#2494;</button>
    </div>
    <div class="plate" id="teaser">__FIG0__</div>
    <p class="readout"><span class="tag">Detail</span><span class="val" id="readout"></span></p>
    <figcaption><b>Figure 2. One subtask, four cells, four failures &mdash; and the answer was right.</b>
      <span>The agent lists both calendars, finds the only hour both are free and says so. Two of the four
      checks nonetheless require a calendar event named &ldquo;meeting&rdquo; that the task never asks anyone
      to create, so the run is scored FAIL. Nothing the agent could write would satisfy the task and the check
      at once, which is what the code BM records. This subtask fails in all four cells for exactly this reason.
      The Bangla run reaches the same hour and writes it in Bangla script &mdash; here that never gets to
      matter, because the check that decides the run never reads the answer.</span></figcaption>
  </figure>

  <figure>
    <div class="plate">__FIG1__</div>
    <figcaption><b>Figure 3. How the study works.</b> <span>The same 300 subtasks are run in four cells &mdash; two
      models crossed with an English and a machine-translated Bangla prompt &mdash; as a 20-step loop inside the
      benchmark&rsquo;s container. The agent sees what it did and what came back, never what it thought. Three
      scoring defects in the repository are repaired before anything is counted, which moves every run&rsquo;s
      score. Of 951 scored runs, 394 pass and 557 fail and need explaining.</span></figcaption>
  </figure>

  <figure>
    <div class="plate">__FIG2__</div>
    <figcaption><b>Figure 4. How we characterize failures.</b> <span>One question decides the branch: whether the
      final output is right for the task <i>as written</i>. A run that is right and still scored FAIL indicts the
      benchmark; a run that is wrong is traced to its decisive step. The tie-break keeps a benchmark defect from
      excusing an agent that would have failed anyway. Each run leaves with one primary code from six families
      and any number of contributing tags. The codebook was checked on a double-coded sample before it was
      applied at scale.</span></figcaption>
  </figure>

  <div class="note">
    <div>
      <h2>Using these in the paper</h2>
      The drawings are vector files, not screenshots: <code>analysis/figures/fig0_teaser.svg</code>,
      <code>fig1_study_design.svg</code> and <code>fig2_failure_coding.svg</code>. All three use
      <code>currentColor</code> for every line and label, so they print black on white without edits; the amber
      elements mark the path the paper argues about. The teaser is static and complete on its own &mdash; the
      interaction above is page JavaScript bound to ids inside it, so the file drops straight into LaTeX.
      Rebuild with <code>make_fig0_teaser.py</code>, then <code>build_figures_page.py</code>.
    </div>
    <div>
      <h2>Where the numbers come from</h2>
      The worked example is subtask <code>1-2/0</code>: task and checks from <code>tasks/1-2/subtasks/0.json</code>,
      busy blocks from the two <code>.ics</code> files in <code>tasks/1-2/testbed/calendar/</code>, the four steps
      and both answers from <code>tasks/1-2/outputs/0/gemma4_31b_{think,bn}/env_history.json</code>. Pass counts and
      root-cause totals: <code>analysis/failure_codes_all_runs.json</code> (557 coded failures: 149 gemma English,
      173 gemma Bangla, 214 gpt-oss English, 21 gpt-oss Bangla). Agreement: <code>analysis/agreement.py</code> over
      <code>labels_A.csv</code> and <code>labels_B.csv</code>, &kappa;&nbsp;=&nbsp;0.78 on the primary code and 0.64
      on the benchmark-versus-agent split, n&nbsp;=&nbsp;16. Coding rules: <code>analysis/codebook.md</code>. The
      gpt-oss Bangla cell is 51 of 300 subtasks and is still running.
    </div>
  </div>
</div>

<script>
(function () {
  var plate = document.getElementById('teaser');
  var readout = document.getElementById('readout');
  var REST = 'Hover a step, a calendar block or a check to see what it actually was.';

  var TEXT = {
    en: {
      task: ['Find a common time for Bob and Tom to have', 'an one hour zoom meeting on 5/1/2024', ''],
      answer: '\\u201cA common time for Bob and Tom to have a one-hour zoom meeting on 5/1/2024 is from 14:30 to 15:30.\\u201d',
      note: 'Bob is free 14:00\\u201316:00, Tom from 14:30 \\u2014 14:30\\u201315:30 is the only common hour.'
    },
    bn: {
      task: ['\\u09ab\\u09be\\u0987\\u09a8\\u09cd\\u09a1 \\u0995\\u09b0\\u09c1\\u09a8: \\u09eb/\\u09e7/\\u09e8\\u09e6\\u09e8\\u09ea \\u09a4\\u09be\\u09b0\\u09bf\\u0996\\u09c7 \\u09ac\\u09ac \\u098f\\u09ac\\u0982 \\u099f\\u09ae\\u09c7\\u09b0 \\u099c\\u09a8\\u09cd\\u09af',
             '\\u098f\\u0995 \\u0998\\u09a3\\u09cd\\u099f\\u09be\\u09b0 \\u098f\\u0995\\u099f\\u09bf \\u099c\\u09c1\\u09ae \\u09ae\\u09bf\\u099f\\u09bf\\u0982 \\u0995\\u09b0\\u09be\\u09b0 \\u099c\\u09a8\\u09cd\\u09af',
             '\\u098f\\u0995\\u099f\\u09bf \\u09b8\\u09be\\u09a7\\u09be\\u09b0\\u09a3 \\u09b8\\u09ae\\u09df \\u0996\\u09c1\\u0981\\u099c\\u09c7 \\u09ac\\u09c7\\u09b0 \\u0995\\u09b0\\u09c1\\u09a8\\u0964'],
      answer: '\\u201c\\u09ac\\u09ac \\u098f\\u09ac\\u0982 \\u099f\\u09ae\\u09c7\\u09b0 \\u099c\\u09a8\\u09cd\\u09af \\u09eb/\\u09e7/\\u09e8\\u09e6\\u09e8\\u09ea \\u09a4\\u09be\\u09b0\\u09bf\\u0996\\u09c7 \\u098f\\u0995\\u099f\\u09bf \\u09b8\\u09be\\u09a7\\u09be\\u09b0\\u09a3 \\u09b8\\u09ae\\u09df \\u09b9\\u09b2\\u09cb \\u09a6\\u09c1\\u09aa\\u09c1\\u09b0 \\u09e7\\u09ea:\\u09e9\\u09e6 \\u09a5\\u09c7\\u0995\\u09c7 \\u09e7\\u09eb:\\u09e9\\u09e6 \\u09aa\\u09b0\\u09cd\\u09af\\u09a8\\u09cd\\u09a4\\u0964\\u201d',
      note: 'The same hour, written in Bangla script and digits. Here it never matters: the check that decides this run never reads the answer.'
    }
  };

  function setLang(lang) {
    var t = TEXT[lang] || TEXT.en;
    var task = document.getElementById('t0-task');
    if (task) {
      var lines = task.querySelectorAll('tspan');
      for (var i = 0; i < lines.length; i++) lines[i].textContent = t.task[i] || '';
    }
    var a = document.getElementById('t0-answer'), n = document.getElementById('t0-answernote');
    if (a) a.textContent = t.answer;
    if (n) n.textContent = t.note;
    ['en', 'bn'].forEach(function (k) {
      var c = document.getElementById('t0-' + k);
      if (!c) return;
      var on = k === lang;
      c.setAttribute('fill', on ? 'currentColor' : 'none');
      c.setAttribute('fill-opacity', on ? '.12' : '0');
      c.setAttribute('stroke-opacity', on ? '.85' : '.3');
      c.setAttribute('stroke-width', on ? '1.5' : '1');
    });
    document.querySelectorAll('button[data-lang]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.lang === lang));
    });
  }

  function setStage(stage) {
    plate.querySelectorAll('.t0-stage').forEach(function (g) {
      g.classList.toggle('dim', stage !== 'all' && g.dataset.stage !== stage &&
                                 !(stage === '4' && g.dataset.stage === '5'));
    });
    document.querySelectorAll('button[data-stage]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.stage === stage));
    });
  }

  document.querySelectorAll('button[data-stage]').forEach(function (b) {
    b.addEventListener('click', function () { setStage(b.dataset.stage); });
  });
  document.querySelectorAll('button[data-lang]').forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.dataset.lang); });
  });

  plate.addEventListener('click', function (e) {
    var c = e.target.closest('.t0-chip');
    if (c) { setLang(c.dataset.lang); return; }
    var g = e.target.closest('.t0-stage');
    if (g) setStage(g.dataset.stage === '5' ? '4' : g.dataset.stage);
  });
  plate.addEventListener('pointerover', function (e) {
    var h = e.target.closest('.t0-hot');
    if (h) readout.textContent = h.getAttribute('data-detail');
  });
  plate.addEventListener('pointerleave', function () { readout.textContent = REST; });

  readout.textContent = REST;
  setLang('en');
  setStage('all');
})();
(function () {
  var box = document.getElementById('steps');
  var out = document.getElementById('s-readout');
  var play = document.getElementById('s-play');
  var REST = 'Click a step to isolate it, hover an output pill for why it matters, or press Play.';
  var timer = null, cur = 0;
  function show(step) {
    var n = step === 'all' ? 0 : +step;
    box.querySelectorAll('.s-step').forEach(function (g) {
      var on = +g.dataset.step === n;
      g.classList.toggle('dim', n !== 0 && !on);
      g.classList.toggle('on', on);
    });
    box.querySelectorAll('.s-arrow').forEach(function (a) {
      var i = +a.id.slice(3);
      var hit = n !== 0 && (i === n - 1 || i === n);
      a.classList.toggle('dim', n !== 0 && !hit);
      a.classList.toggle('on', hit);
    });
    document.querySelectorAll('button[data-sstep]').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.sstep === String(step)));
    });
  }
  function stop() { if (timer) { clearInterval(timer); timer = null; } play.innerHTML = '&#9654; Play'; }
  function start() {
    cur = 0; play.innerHTML = '&#9632; Stop';
    var tick = function () { cur += 1; if (cur > 5) { stop(); show('all'); return; } show(cur); };
    tick(); timer = setInterval(tick, 1600);
  }
  play.addEventListener('click', function () { if (timer) { stop(); show('all'); } else start(); });
  document.querySelectorAll('button[data-sstep]').forEach(function (b) {
    b.addEventListener('click', function () { stop(); show(b.dataset.sstep); });
  });
  box.addEventListener('click', function (e) {
    var g = e.target.closest('.s-step');
    if (g) { stop(); show(g.dataset.step); }
  });
  box.addEventListener('pointerover', function (e) {
    var h = e.target.closest('.s-out');
    if (h) out.textContent = h.getAttribute('data-detail');
  });
  box.addEventListener('pointerleave', function () { out.textContent = REST; });
  out.textContent = REST; show('all');
})();
</script>
"""

out = PAGE.replace('__FIGS__', FIGS).replace('__FIG0__', FIG0).replace('__FIG1__', FIG1).replace('__FIG2__', FIG2)
path = os.path.join(HERE, 'figures.html')
open(path, 'w', encoding='utf-8').write(out)
print('wrote', path, len(out), 'bytes')
