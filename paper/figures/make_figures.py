"""Figures for main.tex (vector PDF, Times to match the ACL template).

    python figures/make_figures.py        # from paper/, writes figures/*.pdf

All numbers are the ones reported in the paper's tables and the four failure-analysis reports.
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.dirname(os.path.abspath(__file__))
plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
    'mathtext.fontset': 'stix', 'font.size': 8, 'pdf.fonttype': 42, 'ps.fonttype': 42,
    'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#333333', 'xtick.color': '#333333',
    'ytick.color': '#333333', 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': '#e4e3df', 'grid.linewidth': 0.5, 'axes.axisbelow': True,
    'legend.frameon': False,
})
# reference categorical palette, fixed order (validated: adjacent CVD dE >= 9)
BLUE, ORANGE, AQUA, YELLOW, PINK, GREEN, VIOLET, RED = (
    '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948')
EN, BN = BLUE, ORANGE
GEMMA, GPTOSS = BLUE, ORANGE
INK, INK2, MUTED, FILL = '#111111', '#444444', '#8a8984', '#f4f3ef'


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


def box(ax, x, y, w, h, text, ec=MUTED, fc='white', fs=6.6, weight='normal', lw=0.9, ha='center'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0,rounding_size=0.012',
                                fc=fc, ec=ec, lw=lw, mutation_aspect=1))
    tx = x + w / 2 if ha == 'center' else x + 0.012
    ax.text(tx, y + h / 2, text, ha=ha, va='center', fontsize=fs, color=INK, weight=weight,
            linespacing=1.15)


def arrow(ax, p, q, color=MUTED, lw=0.9, style='-|>', rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=7, color=color, lw=lw,
                                 connectionstyle=f'arc3,rad={rad}', shrinkA=0, shrinkB=0))


# ============ Figure 1: study overview ============
def fig_overview():
    fig = plt.figure(figsize=(6.3, 2.35))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    panels = [(0.000, 0.235, '(a) Paired protocol'), (0.255, 0.235, '(b) One agent episode'),
              (0.510, 0.205, '(c) Scoring and pairing'), (0.735, 0.265, '(d) Root-cause analysis')]
    for x, w, t in panels:
        ax.add_patch(FancyBboxPatch((x, 0.0), w, 0.90, boxstyle='round,pad=0,rounding_size=0.015',
                                    fc=FILL, ec='none'))
        ax.text(x + 0.012, 0.955, t, fontsize=7.6, weight='bold', va='center', color=INK)
    for a, b in [(0.235, 0.255), (0.49, 0.51), (0.715, 0.735)]:
        arrow(ax, (a + 0.002, 0.45), (b - 0.002, 0.45), color=INK2, lw=1.1)

    # (a)
    box(ax, 0.012, 0.70, 0.095, 0.15, 'Task\n(English)', ec=EN, lw=1.2)
    box(ax, 0.128, 0.70, 0.095, 0.15, 'Task\n(Bangla)', ec=BN, lw=1.2)
    arrow(ax, (0.107, 0.775), (0.128, 0.775))
    ax.text(0.117, 0.655, 'translate; names, files,\nliterals, digits protected', fontsize=5.6,
            ha='center', va='top', color=INK2)
    box(ax, 0.012, 0.30, 0.211, 0.20,
        'Held fixed: environment, seeded files,\ntool schema (English), step budget,\ndecoding, checkers',
        fs=6.0)
    box(ax, 0.012, 0.06, 0.211, 0.20,
        'Varied: language of the instruction\nand of the simulated user or\ncoworkers (τ²-bench, TAC)', fs=6.0,
        ec=BN)

    # (b) agent loop with layers
    bx = 0.268
    box(ax, bx, 0.70, 0.21, 0.13, 'Prompt: system + task + history', fs=6.2)
    box(ax, bx, 0.43, 0.21, 0.18, 'Model: ##Thought → ##Command\n{"app", "action", args}\n', fs=6.2)
    box(ax, bx, 0.16, 0.21, 0.18, 'Tool executes → observation\n(or user / coworker replies)\n', fs=6.2)
    arrow(ax, (bx + 0.105, 0.70), (bx + 0.105, 0.61))
    arrow(ax, (bx + 0.105, 0.43), (bx + 0.105, 0.34))
    arrow(ax, (bx + 0.21, 0.25), (bx + 0.21, 0.765), rad=0.6)
    ax.text(bx + 0.105, 0.065, 'until finish_task, stuck, or step limit', fontsize=5.6, ha='center',
            color=INK2)
    tags = [(0.722, 'L1 ground, L2 plan'), (0.455, 'L3 format, L4 args, L6 answer'),
            (0.185, 'L5 verify, recover, stop')]
    for y, t in tags:
        ax.text(bx + 0.006, y, t, fontsize=5.2, color=VIOLET, va='center', style='italic')

    # (c) scoring + 2x2
    cx = 0.522
    box(ax, cx, 0.66, 0.18, 0.16, 'Benchmark checks on the\nfinal state (files, DB, answer)', fs=6.0)
    arrow(ax, (cx + 0.09, 0.66), (cx + 0.09, 0.59))
    ax.text(cx + 0.09, 0.555, 'pass / fail, per language', fontsize=6.0, ha='center', color=INK2)
    gx, gy, cw, ch = cx + 0.035, 0.10, 0.07, 0.17
    ax.text(gx + cw, gy + 2 * ch + 0.04, 'Bangla', fontsize=6.0, ha='center', color=BN, weight='bold')
    ax.text(gx - 0.03, gy + ch, 'English', fontsize=6.0, ha='center', va='center', rotation=90,
            color=EN, weight='bold')
    ax.text(gx - 0.012, gy + 1.5 * ch, 'pass', fontsize=5.4, ha='center', va='center', rotation=90,
            color=INK2)
    ax.text(gx - 0.012, gy + 0.5 * ch, 'fail', fontsize=5.4, ha='center', va='center', rotation=90,
            color=INK2)
    cells = [(0, 1, 'PP', 'white'), (1, 1, 'PF', '#fde3d6'), (0, 0, 'FP', 'white'), (1, 0, 'FF', 'white')]
    for i, j, t, fc in cells:
        box(ax, gx + i * cw, gy + j * ch, cw, ch, t, fc=fc, fs=6.6, weight='bold' if t == 'PF' else 'normal')
    ax.text(gx + 0.5 * cw, gy + 2 * ch + 0.012, 'pass', fontsize=5.4, ha='center', color=INK2)
    ax.text(gx + 1.5 * cw, gy + 2 * ch + 0.012, 'fail', fontsize=5.4, ha='center', color=INK2)

    # (d) decision tree
    dx = 0.745
    box(ax, dx, 0.78, 0.245, 0.085, 'PF case: read EN and BN traces side by side', fs=6.0)
    steps = [('0  Output already correct?', 'C5'), ('1  Translation valid?', 'C3'),
             ('2  Simulated user behaved?', 'C2'), ('3–5  Understood, right tool, args?', 'C1 / C6'),
             ('6  Environment executed?', 'C4'), ('7  Verified, did not give up?', 'C1 / C6 / C7')]
    y = 0.69
    for t, c in steps:
        ax.text(dx + 0.006, y, t, fontsize=5.8, va='center', color=INK)
        ax.text(dx + 0.243, y, c, fontsize=5.8, va='center', ha='right', color=RED, weight='bold')
        y -= 0.088
    ax.text(dx + 0.006, 0.10, 'first failing step → one confound class;\nsymmetric sensitivity analysis',
            fontsize=5.6, va='center', color=INK2, style='italic')
    save(fig, 'fig_overview.pdf')


# ============ Figure 2: layer of first failure, by model ============
def fig_layers():
    rows = [  # label, gemma %, gpt-oss %, note
        ('L1–L2 content / task reading', 29, 23, 'OB, EN failures'),
        ('L3 action format', 8, 50, 'OB, EN failures'),
        ('L4 tool arguments', 33, 51, 'WB, all failures'),
        ('L5 control: budget, loops', 28, 11, 'OB, EN failures'),
        ('L6 answer in Bangla script', 36, 12, 'OB, BN-only failures'),
    ]
    fig, ax = plt.subplots(figsize=(3.03, 1.7))
    h = 0.36
    for i, (lab, g, o, note) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.barh(y + h / 2 + 0.01, g, h, color=GEMMA, edgecolor='white', linewidth=0.5)
        ax.barh(y - h / 2 - 0.01, o, h, color=GPTOSS, edgecolor='white', linewidth=0.5)
        ax.text(g + 1, y + h / 2 + 0.01, f'{g}', va='center', fontsize=6.2, color=INK2)
        ax.text(o + 1, y - h / 2 - 0.01, f'{o}', va='center', fontsize=6.2, color=INK2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f'{r[0]}\n({r[3]})' for r in rows][::-1], fontsize=6.3)
    ax.set_xlim(0, 60); ax.set_xlabel('Share of failures (%)', fontsize=7)
    ax.tick_params(axis='x', labelsize=6.5); ax.grid(axis='y', visible=False)
    ax.barh(0, 0, color=GEMMA, label='gemma4:31b'); ax.barh(0, 0, color=GPTOSS, label='gpt-oss:20b')
    ax.legend(fontsize=6.5, loc='lower right', handlelength=1.0)
    save(fig, 'fig_layers.pdf')


# ============ Figure 3: gap before / after confound removal ============
def fig_forest():
    rows = [('OB gemma', 8.0, 3.0, 13.0, 1.9, -1.9, 5.6), ('OB gpt-oss', -6.7, -12.0, -1.3, -3.3, -7.7, 1.5),
            ('τ² gemma', 11.5, 5.0, 17.4, 5.8, -1.9, 12.8), ('τ² gpt-oss', -0.7, -10.7, 8.7, -0.7, -10.5, 9.1),
            ('WB gemma', -1.1, -10.0, 7.8, -3.4, -11.4, 4.5), ('WB gpt-oss', 5.6, -5.6, 16.7, 8.0, -2.3, 18.2),
            ('TAC gemma', 13.0, 0.0, 26.1, 0.0, 0.0, 0.0)]
    fig, ax = plt.subplots(figsize=(3.03, 1.7))
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([r[2], r[3]], [y + 0.15] * 2, color=INK2, lw=1.0)
        ax.plot(r[1], y + 0.15, 'o', ms=4.2, color=INK, mec='white', mew=0.8)
        ax.plot([r[5], r[6]], [y - 0.15] * 2, color=AQUA, lw=1.0)
        ax.plot(r[4], y - 0.15, 's', ms=4.0, color=AQUA, mec='white', mew=0.8)
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=6.8)
    ax.set_xlim(-13, 27); ax.tick_params(axis='x', labelsize=6.5)
    ax.set_xlabel('English − Bangla pass rate (points, 95% CI)', fontsize=7)
    ax.grid(axis='y', visible=False)
    ax.plot([], [], 'o', color=INK, ms=4, label='as scored')
    ax.plot([], [], 's', color=AQUA, ms=4, label='benchmark-side confounds removed')
    ax.legend(fontsize=6.3, loc='lower center', bbox_to_anchor=(0.45, 1.0), ncol=2, handletextpad=0.3,
              columnspacing=0.8)
    save(fig, 'fig_forest.pdf')


# ============ Figure 4 (appendix): failure propagation case studies ============
def fig_chains():
    K = {'task': BLUE, 'exec': ORANGE, 'ctrl': AQUA, 'ext': VIOLET, 'out': RED}
    chains = [
        ('OfficeBench 1-20/3, gemma4:31b, Bangla (C1, name case)', [
            ('task', 'Name appears only in\nBangla script; agent\nwrites "bob"'),
            ('exec', 'list_emails("bob")\n→ "No emails found"'),
            ('ctrl', 'Empty result accepted;\nno retry with "Bob"'),
            ('out', 'Answers "no, 0"\n→ fail')]),
        ('OfficeBench 1-15/0, gemma4:31b, Bangla (C4, reply cap)', [
            ('task', 'Plans to resend the\nwhole 12.9k-character\ndocument'),
            ('exec', 'Action exceeds the\nreply cap → rejected\nas malformed'),
            ('ctrl', 'Same long write\nretried 14 times'),
            ('out', 'Step limit, no write\n→ fail')]),
        ('WorkBench email:41, gemma4:31b, Bangla (C1, relative date)', [
            ('task', '"Last week" grounded\nas rolling 7 days'),
            ('exec', 'Windowed searches\nreturn nothing'),
            ('ctrl', 'Undated search finds\nboth emails; agent\nrejects them'),
            ('out', 'No forward_email\n→ fail')]),
        ('τ²-bench airline 19, gemma4:31b, Bangla (C2, simulated user)', [
            ('task', 'Plan and policy check\nmatch the English run'),
            ('exec', 'Agent asks the user\nto confirm'),
            ('ext', 'Simulated user confirms\nand ends the chat in\nthe same turn'),
            ('out', 'cancel_reservation\nnever called → fail')]),
    ]
    fig = plt.figure(figsize=(6.3, 4.1))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    rh, bw, bh = 0.225, 0.215, 0.13
    for r, (title, steps) in enumerate(chains):
        y0 = 1 - (r + 1) * rh + 0.01
        ax.text(0.005, y0 + bh + 0.035, title, fontsize=7.2, weight='bold', color=INK, va='center')
        for k, (kind, t) in enumerate(steps):
            x0 = 0.005 + k * 0.25
            ax.add_patch(FancyBboxPatch((x0, y0), bw, bh, boxstyle='round,pad=0,rounding_size=0.01',
                                        fc='white', ec=K[kind], lw=1.3))
            ax.text(x0 + bw / 2, y0 + bh / 2, t, ha='center', va='center', fontsize=6.4, color=INK,
                    linespacing=1.15)
            if k < 3:
                arrow(ax, (x0 + bw + 0.004, y0 + bh / 2), (x0 + 0.25 - 0.004, y0 + bh / 2), color=INK2)
    leg = [('task', 'task-level step'), ('exec', 'execution-level step'), ('ctrl', 'control (verify, retry)'),
           ('ext', 'simulated user'), ('out', 'outcome')]
    for i, (k, t) in enumerate(leg):
        x = 0.005 + i * 0.2
        ax.add_patch(FancyBboxPatch((x, 0.035), 0.022, 0.022, boxstyle='square,pad=0', fc='white',
                                    ec=K[k], lw=1.3))
        ax.text(x + 0.03, 0.046, t, fontsize=6.4, va='center', color=INK2)
    ax.set_ylim(0.02, 1)
    save(fig, 'fig_chains.pdf')


if __name__ == '__main__':
    fig_overview(); fig_layers(); fig_forest(); fig_chains()
    print('figures written to', OUT)
