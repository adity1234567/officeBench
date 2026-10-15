"""Result charts for the failure-analysis report, as standalone print-ready SVG (white ground, no scripts).

Called from fa_report.py (needs the scenario results and the case-label counts) and writes analysis/figures/res_*.svg.
Colours are fixed per run in every chart: gemma English blue, gemma Bangla amber, gpt-oss English slate, gpt-oss Bangla teal.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, 'figures')
INK, MUTED, GRID = '#1b2330', '#5e6675', '#e2ded7'
BLUE, AMBER, SLATE, TEAL = '#2d5a9b', '#d97706', '#8a93a3', '#1f8a8a'
PALE_BLUE, PALE_GREY = '#c9d6ea', '#dcdfe5'
FONT = 'ui-sans-serif, system-ui, Segoe UI, Helvetica, Arial, sans-serif'
RUNCOL = {'EN': BLUE, 'BN': AMBER, 'GO': SLATE, 'GB': TEAL}
RUNLAB = {'EN': 'gemma4:31b English', 'BN': 'gemma4:31b Bangla', 'GO': 'gpt-oss:20b English', 'GB': 'gpt-oss:20b Bangla'}
esc = lambda s: str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


class Svg:
    def __init__(self, w, h, label):
        self.w, self.h, self.o = w, h, []
        self.label = label

    def t(self, x, y, s, size=13, anchor='start', weight=None, fill=INK, op=None, mono=False):
        a = 'x="%g" y="%g" font-size="%g" text-anchor="%s" fill="%s"' % (x, y, size, anchor, fill)
        if weight: a += ' font-weight="%s"' % weight
        if op: a += ' fill-opacity="%s"' % op
        if mono: a += ' font-family="ui-monospace, Consolas, monospace"'
        self.o.append('<text %s>%s</text>' % (a, esc(s)))

    def r(self, x, y, w, h, fill='none', stroke=None, sw=1, rx=0, op=None):
        a = 'x="%g" y="%g" width="%g" height="%g" rx="%g" fill="%s"' % (x, y, w, h, rx, fill)
        if stroke: a += ' stroke="%s" stroke-width="%g"' % (stroke, sw)
        if op: a += ' fill-opacity="%s"' % op
        self.o.append('<rect %s/>' % a)

    def l(self, x1, y1, x2, y2, stroke=GRID, sw=1, dash=None):
        a = 'x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="%g"' % (x1, y1, x2, y2, stroke, sw)
        if dash: a += ' stroke-dasharray="%s"' % dash
        self.o.append('<line %s/>' % a)

    def c(self, x, y, r, fill='none', stroke=None, sw=1.6):
        a = 'cx="%g" cy="%g" r="%g" fill="%s"' % (x, y, r, fill)
        if stroke: a += ' stroke="%s" stroke-width="%g"' % (stroke, sw)
        self.o.append('<circle %s/>' % a)

    def save(self, name):
        s = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" role="img" font-family="%s" aria-label="%s">\n'
             '<rect width="%d" height="%d" fill="#ffffff"/>\n%s\n</svg>\n'
             % (self.w, self.h, FONT, esc(self.label).replace('"', '&quot;'), self.w, self.h, '\n'.join(self.o)))
        os.makedirs(FIG, exist_ok=True)
        open(os.path.join(FIG, name), 'w', encoding='utf-8').write(s)
        return 'figures/' + name


pct = lambda a, b: '%.1f%%' % (100 * a / b) if b else '–'


def success_by_size(R):
    """Grouped bars: success rate by task size for the four complete runs."""
    rt = R['rate']
    s = Svg(860, 430, 'Success rate by task size for the four complete runs. All 300 subtasks: gemma4:31b English %s, gemma4:31b Bangla %s, gpt-oss:20b English %s, gpt-oss:20b Bangla %s.'
            % tuple(pct(*rt[k][None]) for k in ('EN', 'BN', 'GO', 'GB')))
    x0, x1, yt, yb = 64, 840, 62, 350
    Y = lambda v: yb - (yb - yt) * v
    for v in (0, .25, .5, .75, 1):
        s.l(x0, Y(v), x1, Y(v), GRID if v else MUTED)
        s.t(x0 - 8, Y(v) + 4, '%d%%' % (100 * v), 12, 'end', fill=MUTED)
    runs = ['EN', 'BN', 'GO', 'GB']
    lx = x0
    for k in runs:
        s.r(lx, 20, 14, 14, RUNCOL[k])
        s.t(lx + 20, 32, RUNLAB[k], 13)
        lx += 195
    groups = [(1, 'Single-app'), (2, 'Two-app'), (3, 'Three-app'), (None, 'All 300')]
    gw = (x1 - x0) / 4
    bw, gap = 40, 5
    for gi, (a, name) in enumerate(groups):
        cx = x0 + gw * gi + gw / 2
        left = cx - (4 * bw + 3 * gap) / 2
        for ri, k in enumerate(runs):
            p, n = rt[k][a]
            h = (yb - yt) * p / n
            bx = left + ri * (bw + gap)
            s.r(bx, yb - h, bw, h, RUNCOL[k])
            s.t(bx + bw / 2, yb - h - 18, '%.1f%%' % (100 * p / n), 11.5, 'middle', '700')
            s.t(bx + bw / 2, yb - h - 5, '%d/%d' % (p, n), 10, 'middle', fill=MUTED)
        s.t(cx, yb + 22, name, 14, 'middle', '700')
        s.t(cx, yb + 40, 'n = %d' % rt['EN'][a][1], 12, 'middle', fill=MUTED)
    s.t(x0, 410, 'Corrected scores. gemma is lower in Bangla on short tasks; gpt-oss is higher in Bangla at every task size.', 12, fill=MUTED)
    return s.save('res_success_by_size.svg')


def paired(R, key='pair', fname='res_paired.svg', who='gemma4:31b', note=None):
    """100% stacked bars of the paired outcome (English run against Bangla run)."""
    d0 = R[key][None]
    s = Svg(860, 330, 'Paired outcome of %s English against Bangla. Overall %d subtasks pass in both, %d only in English, %d only in Bangla and %d fail in both.'
            % (who, d0['PP'], d0['PF'], d0['FP'], d0['FF']))
    x0, x1 = 120, 800
    cols = [('PP', 'both pass', PALE_BLUE, INK), ('PF', 'English only passes', AMBER, '#ffffff'),
            ('FP', 'Bangla only passes', TEAL, '#ffffff'), ('FF', 'both fail', PALE_GREY, INK)]
    lx = x0
    for k, lab, col, _ in cols:
        s.r(lx, 14, 14, 14, col)
        s.t(lx + 20, 26, lab, 13)
        lx += 160
    for i, (a, name) in enumerate([(None, 'All 300'), (1, 'Single-app'), (2, 'Two-app'), (3, 'Three-app')]):
        y = 56 + i * 58
        d = R[key][a]
        n = sum(d.values())
        s.t(x0 - 12, y + 24, name, 14, 'end', '700')
        s.t(x0 - 12, y + 40, 'n = %d' % n, 11, 'end', fill=MUTED)
        x = x0
        for k, lab, col, tc in cols:
            w = (x1 - x0) * d[k] / n
            s.r(x, y, w, 34, col)
            if w >= 22:
                s.t(x + w / 2, y + 22, str(d[k]), 14, 'middle', '700', tc)
            else:
                s.t(x + w / 2, y - 4, str(d[k]), 12, 'middle', '700')
            x += w
    s.t(x0, 306, note or 'Amber is English-only passes, teal is Bangla-only passes.', 12, fill=MUTED)
    return s.save(fname)


FAMILIES = [('Benchmark defect', ('BM',), AMBER, '#ffffff'),
            ('Wrong content or task misread', ('WC', 'TR'), BLUE, '#ffffff'),
            ('Out of steps or output loops', ('SB', 'TL', 'DL'), SLATE, '#ffffff'),
            ('No valid action, gave up', ('ER', 'PF', 'CAP', 'FMT'), '#7a5ea8', '#ffffff'),
            ('Language-specific (Bangla)', ('AL', 'NC', 'WD', 'TX'), TEAL, '#ffffff'),
            ('Other or infrastructure', ('OTH', 'INF'), PALE_GREY, INK)]


def causes(R):
    """100% stacked bars of primary failure cause per run (three runs with full root-cause coding)."""
    s = Svg(860, 340, 'Primary root cause of failed runs. Benchmark defects are 31.5% of gemma English failures, 22.5% of gemma Bangla failures and 8.9% of gpt-oss English failures; '
                      'gpt-oss English is dominated by no-valid-action failures at 50.0%; language-specific causes are 15.6% of gemma Bangla failures.')
    x0, x1 = 190, 800
    for i, (lab, _, col, _) in enumerate(FAMILIES):
        lx = 20 + (i % 3) * 280
        ly = 20 + (i // 3) * 22
        s.r(lx, ly, 14, 14, col)
        s.t(lx + 20, ly + 12, lab, 12.5)
    for i, k in enumerate(('EN', 'BN', 'GO')):
        y = 92 + i * 62
        cnt = R['cat'][k]
        n = sum(cnt.values())
        s.t(x0 - 12, y + 20, RUNLAB[k], 14, 'end', '700')
        s.t(x0 - 12, y + 37, '%d failures' % n, 11.5, 'end', fill=MUTED)
        x = x0
        for lab, codes, col, tc in FAMILIES:
            v = sum(cnt.get(c, 0) for c in codes)
            w = (x1 - x0) * v / n
            if v:
                s.r(x, y, w, 36, col, '#ffffff', 1)
                if w >= 26:
                    s.t(x + w / 2, y + 22, str(v), 13, 'middle', '700', tc)
            x += w
    s.t(20, 296, 'Counts inside segments; widths are shares of each run’s failures (primary root cause from the trace-by-trace classification).', 12, fill=MUTED)
    s.t(20, 314, 'gpt-oss English fails mostly because it cannot produce a valid action in the benchmark’s format (54 failures coded FMT).', 12, fill=MUTED)
    s.t(20, 332, 'gpt-oss Bangla is not shown: only 21 of its 194 failures have a root-cause code (see the behaviour signals in Figure 7).', 12, fill=MUTED)
    return s.save('res_causes.svg')


def patterns(R):
    """Dot matrix of pass patterns across the four complete runs."""
    s = Svg(860, 540, 'How the four complete runs agree. %d subtasks fail in all four and %d pass in all four. The remaining 14 patterns each account for 2 to 28 subtasks.'
            % (R['fail_all4'], R['pass_all4']))
    cols = [('gemma', 'EN', 190), ('gemma', 'BN', 250), ('gpt-oss', 'EN', 320), ('gpt-oss', 'GB', 380)]
    for (m, k, cx), lab in zip(cols, ('English', 'Bangla', 'English', 'Bangla')):
        s.t(cx, 30, m, 11.5, 'middle', '700', fill=RUNCOL[k])
        s.t(cx, 46, lab, 11.5, 'middle', fill=RUNCOL[k])
    s.t(470, 40, 'subtasks (of 300)', 12.5, 'start', '700')
    pat = sorted(R['pattern4'].items(), key=lambda kv: -kv[1])
    mx = max(v for _, v in pat)
    notes = {(False, False, False, False): 'fail in all four', (True, True, True, True): 'pass in all four',
             (True, True, False, False): 'gemma only, both languages',
             (True, True, False, True): 'only gpt-oss English fails',
             (True, False, False, False): 'only gemma English passes',
             (False, True, False, False): 'only gemma Bangla passes'}
    for i, (pt, v) in enumerate(pat):
        y = 64 + i * 28
        if i % 2 == 0:
            s.r(20, y - 4, 820, 28, '#f6f7f9')
        for (m, k, cx), ok in zip(cols, pt):
            if ok:
                s.c(cx, y + 10, 7.5, RUNCOL[k])
            else:
                s.c(cx, y + 10, 7.5, '#ffffff', MUTED, 1.3)
        w = 140 * v / mx
        s.r(470, y + 1, w, 18, AMBER if not any(pt) else SLATE if all(pt) else BLUE)
        s.t(470 + w + 8, y + 15, str(v), 12.5, weight='700')
        if pt in notes:
            s.t(664, y + 15, notes[pt], 11, fill=MUTED)
    s.t(20, 528, 'Filled dot = passes, open dot = fails; rows sorted by number of subtasks.', 12, fill=MUTED)
    return s.save('res_patterns.svg')


def signals(R):
    """gpt-oss English against Bangla: how often the run produced invalid actions and how it ended."""
    sg = json.load(open(os.path.join(HERE, 'fa_signals.json'), encoding='utf-8'))
    go, gb = sg['GO'], sg['GB']
    n = len(go)
    rows = [('Invalid (malformed) actions', sum(v['malformed'] for v in go.values()), sum(v['malformed'] for v in gb.values())),
            ('Calls to built-in tools (container.exec, …)', sum(v['builtin'] for v in go.values()), sum(v['builtin'] for v in gb.values())),
            ('Steps with no action at all', sum(v['empty'] for v in go.values()), sum(v['empty'] for v in gb.values())),
            ('Runs ended as stuck', sum(v['end'] == 'stuck' for v in go.values()), sum(v['end'] == 'stuck' for v in gb.values())),
            ('Runs ended at the 20-step limit', sum(v['end'] == 'budget' for v in go.values()), sum(v['end'] == 'budget' for v in gb.values())),
            ('Runs that finished with an answer', sum(v['end'] == 'finish' for v in go.values()), sum(v['end'] == 'finish' for v in gb.values()))]
    s = Svg(860, 80 + len(rows) * 52 + 30, 'gpt-oss:20b English against Bangla behaviour over %d runs each: malformed actions %d against %d, built-in tool calls %d against %d, '
            'runs ended as stuck %d against %d, runs that finished %d against %d.'
            % (n, rows[0][1], rows[0][2], rows[1][1], rows[1][2], rows[3][1], rows[3][2], rows[5][1], rows[5][2]))
    for i, (lab, col) in enumerate((('English', SLATE), ('Bangla', TEAL))):
        s.r(300 + i * 110, 16, 14, 14, col)
        s.t(320 + i * 110, 28, lab, 13)
    x0, x1 = 300, 780
    for i, (lab, a, b) in enumerate(rows):
        y = 50 + i * 52
        mx = max(a, b, 1)
        s.t(x0 - 12, y + 20, lab, 13, 'end')
        for j, (v, col) in enumerate(((a, SLATE), (b, TEAL))):
            w = (x1 - x0 - 50) * v / mx
            s.r(x0, y + j * 22, max(w, 1.5), 18, col)
            s.t(x0 + w + 8, y + j * 22 + 14, str(v), 12.5, weight='700')
    s.t(20, 80 + len(rows) * 52 + 12, '%d runs per column (one subtask in each run has no recorded action history). Each row is scaled to its own larger value.' % n, 12, fill=MUTED)
    return s.save('res_signals.svg')


def forest(SC, short=None, fname='res_sensitivity.svg', who='gemma4:31b'):
    """Gap with 95% interval for each sensitivity scenario."""
    short = short or {'S0': 'As scored', 'S1': 'Drop translation cases (C3)', 'S3': 'Drop tool/environment cases (C4)',
                      'S4': 'Drop answer-language cases (C5)', 'S5': 'Drop C3 + C4 + C5', 'S6': 'Drop C3 + C4 + C5 + C6',
                      'S7': 'Credit correct Bangla-script answers', 'S8': 'Credit answers, drop C3 + C4',
                      'S9': 'S5, plus drop 7 English-trap subtasks (symmetric)'}
    rows = [(n.split()[0], short[n.split()[0]], d) for n, d in SC if n.split()[0] in short]
    s = Svg(860, 80 + 36 * len(rows) + 50, '%s English minus Bangla success gap with 95 percent intervals under each sensitivity scenario. As scored the gap is %+.1f percentage points.'
            % (who, 100 * rows[0][2]['gap']))
    vals = [100 * d['gap_ci'][0] for _, _, d in rows] + [100 * d['gap_ci'][1] for _, _, d in rows]
    lo = int(min(min(vals) - 2, -8) // 4 * 4)
    hi = int(max(max(vals) + 2, 16) // 4 * 4 + 4)
    x0, x1 = 400, 810
    X = lambda v: x0 + (x1 - x0) * (v - lo) / (hi - lo)
    for v in range(lo, hi + 1, 4):
        s.l(X(v), 52, X(v), 52 + 36 * len(rows), GRID if v else MUTED, 1 if v else 1.6)
        s.t(X(v), 70 + 36 * len(rows), '%+d' % v if v else '0', 12, 'middle', fill=MUTED)
    s.t((x0 + x1) / 2, 92 + 36 * len(rows), 'English minus Bangla success rate, percentage points (95% bootstrap interval)', 12, 'middle', fill=MUTED)
    s.t(20, 36, 'Scenario', 12.5, weight='700')
    s.t(x1 + 36, 36, 'n', 12.5, 'end', '700')
    for i, (key, lab, d) in enumerate(rows):
        y = 52 + i * 36
        if i % 2 == 0:
            s.r(10, y, 850, 36, '#f6f7f9')
        g, (a, b) = 100 * d['gap'], (100 * d['gap_ci'][0], 100 * d['gap_ci'][1])
        incl = a <= 0 <= b
        col = MUTED if incl else AMBER
        s.t(20, y + 23, '%s  %s' % (key, lab), 12.5, weight='700' if key in ('S0', 'S9') else None)
        s.l(X(max(a, lo)), y + 18, X(min(b, hi)), y + 18, col, 2.4)
        s.l(X(a), y + 11, X(a), y + 25, col, 2.4)
        s.l(X(b), y + 11, X(b), y + 25, col, 2.4)
        s.c(X(g), y + 18, 5.5, col)
        s.t(X(b) + 10, y + 22, '%+.1f' % g, 12, weight='700', fill=INK)
        s.t(x1 + 36, y + 22, str(d['n']), 11.5, 'end', fill=MUTED)
    return s.save(fname)


def confounds(R, names, by_apps, order, fname='res_confounds.svg', total=42, who='gemma4:31b'):
    """Stacked bars: confound class of the EN-pass/BN-fail cases, by app count."""
    s = Svg(860, 80 + 46 * len(order), 'Confound class of the %d English-pass Bangla-fail cases of %s, split by number of apps.' % (total, who))
    x0, x1 = 360, 800
    shades = [('1-app', '#1f3f6e'), ('2-app', '#4f7fbf'), ('3-app', '#a9c1e3')]
    for i, (lab, col) in enumerate(shades):
        s.r(20 + i * 100, 16, 14, 14, col)
        s.t(40 + i * 100, 28, lab, 12.5)
    mx = max(sum(by_apps[a].get(k, 0) for a in (1, 2, 3)) for k in order)
    for i, k in enumerate(order):
        y = 50 + i * 46
        tot = sum(by_apps[a].get(k, 0) for a in (1, 2, 3))
        s.t(x0 - 12, y + 19, '%s  %s' % (k, names[k]), 13, 'end', '700' if k == 'C1' else None)
        x = x0
        for (lab, col), a in zip(shades, (1, 2, 3)):
            v = by_apps[a].get(k, 0)
            w = (x1 - x0) * v / mx
            if v:
                s.r(x, y, w, 30, col, '#ffffff', 1)
                if w >= 20:
                    s.t(x + w / 2, y + 20, str(v), 13, 'middle', '700', '#ffffff' if a < 3 else INK)
            x += w
        s.t(x + 8, y + 20, str(tot), 13, weight='700')
    return s.save(fname)
