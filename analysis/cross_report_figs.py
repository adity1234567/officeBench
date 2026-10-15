"""Figures for the cross-benchmark failure report (all numbers transcribed from the four source reports)."""
import os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'
os.makedirs(OUT, exist_ok=True)

# reference categorical palette (light mode), fixed order
S = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']
EN, BN = S[0], S[1]
INK, INK2, MUTED, GRID, SURF = '#0b0b0b', '#52514e', '#8a8984', '#e4e3df', '#fcfcfb'

plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 9, 'axes.edgecolor': MUTED, 'axes.labelcolor': INK2,
    'xtick.color': INK2, 'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6, 'axes.axisbelow': True,
    'figure.facecolor': 'white', 'axes.facecolor': 'white', 'legend.frameon': False,
})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=220, bbox_inches='tight')
    plt.close(fig)


# ---------- F1: success EN vs BN, every run ----------
runs = [('OfficeBench\ngemma4:31b', 50.3, 42.3, 300), ('OfficeBench\ngpt-oss:20b', 28.7, 35.3, 300),
        ('τ²-bench\ngemma4:31b', 49.5, 38.1, 218), ('τ²-bench\ngpt-oss:20b', 38.9, 39.6, 149),
        ('WorkBench\ngemma4:31b', 81.1, 82.2, 90), ('WorkBench\ngpt-oss:20b', 58.9, 53.3, 90),
        ('TAC\ngemma4:31b', 39.1, 26.1, 23)]
fig, ax = plt.subplots(figsize=(7.2, 3.0))
w = 0.38
for i, (lab, e, b, n) in enumerate(runs):
    for x, v, c in ((i - w / 2 - 0.01, e, EN), (i + w / 2 + 0.01, b, BN)):
        ax.bar(x, v, w, color=c, edgecolor='white', linewidth=1.0)
        ax.text(x, v + 1.2, f'{v:.0f}', ha='center', va='bottom', fontsize=7.5, color=INK2)
ax.set_xticks(range(len(runs)))
ax.set_xticklabels([f'{r[0]}\nn = {r[3]}' for r in runs], fontsize=7.5)
ax.set_ylabel('Success rate (%)')
ax.set_ylim(0, 95)
ax.grid(axis='x', visible=False)
ax.bar(0, 0, color=EN, label='English'); ax.bar(0, 0, color=BN, label='Bangla')
ax.legend(loc='upper left', ncol=2, fontsize=8)
save(fig, 'f1_success.png')

# ---------- F2: forest plot, raw vs confound-filtered gap ----------
rows = [  # label, raw, lo, hi, filtered, lo, hi, filter name
    ('OfficeBench · gemma4:31b', 8.0, 3.0, 13.0, 1.9, -1.9, 5.6, 'S9'),
    ('OfficeBench · gpt-oss:20b', -6.7, -12.0, -1.3, -3.3, -7.7, 1.5, 'S6'),
    ('τ²-bench · gemma4:31b', 11.5, 5.0, 17.4, 5.8, -1.9, 12.8, 'S7'),
    ('τ²-bench · gpt-oss:20b', -0.7, -10.7, 8.7, -0.7, -10.5, 9.1, 'S7'),
    ('WorkBench · gemma4:31b', -1.1, -10.0, 7.8, -3.4, -11.4, 4.5, 'S4'),
    ('WorkBench · gpt-oss:20b', 5.6, -5.6, 16.7, 8.0, -2.3, 18.2, 'S4'),
    ('TAC · gemma4:31b', 13.0, 0.0, 26.1, 0.0, 0.0, 0.0, 'S5'),
]
fig, ax = plt.subplots(figsize=(7.2, 3.2))
for i, r in enumerate(rows):
    y = len(rows) - 1 - i
    ax.plot([r[2], r[3]], [y + 0.16] * 2, color=INK2, lw=1.4)
    ax.plot(r[1], y + 0.16, 'o', ms=7, color=INK, mec='white', mew=1.5)
    ax.plot([r[5], r[6]], [y - 0.16] * 2, color=S[2], lw=1.4)
    ax.plot(r[4], y - 0.16, 's', ms=7, color=S[2], mec='white', mew=1.5)
    ax.text(27.5, y, f'{r[1]:+.1f} → {r[4]:+.1f}  ({r[7]})', va='center', fontsize=7.5, color=INK2)
ax.axvline(0, color=MUTED, lw=1)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=8)
ax.set_xlim(-14, 27)
ax.set_xlabel('English minus Bangla success, percentage points (95% CI). Positive = Bangla worse.')
ax.grid(axis='y', visible=False)
ax.plot([], [], 'o', color=INK, label='As scored')
ax.plot([], [], 's', color=S[2], label='Benchmark-side confounds removed (symmetric where available)')
ax.legend(loc='lower center', bbox_to_anchor=(0.45, 1.0), ncol=2, fontsize=8)
save(fig, 'f2_forest.png')

# ---------- F3: confound class per analysis ----------
an = ['OfficeBench gemma (42)', 'OfficeBench gpt-oss (25)', 'τ² gemma (40)', 'τ² gpt-oss (26)',
      'WorkBench gemma (7)', 'WorkBench gpt-oss (15)', 'TAC gemma (8)*']
C = {  # C1..C7
    'OfficeBench gemma (42)': [6, 0, 6, 5, 15, 3, 7], 'OfficeBench gpt-oss (25)': [7, 0, 0, 2, 6, 1, 9],
    'τ² gemma (40)': [6, 19, 1, 0, 0, 14, 0], 'τ² gpt-oss (26)': [2, 16, 0, 0, 0, 7, 1],
    'WorkBench gemma (7)': [2, 0, 1, 0, 1, 3, 0], 'WorkBench gpt-oss (15)': [1, 0, 0, 0, 0, 14, 0],
    'TAC gemma (8)*': [0, 0, 1, 1, 0, 3, 3]}
cn = ['C1 Genuine Bangla agent failure', 'C2 User simulator / NPC', 'C3 Translation / localization',
      'C4 Tool / environment', 'C5 Checker or task ambiguity', 'C6 General weakness (both languages)', 'C7 Unclear / noise']
fig, ax = plt.subplots(figsize=(7.2, 3.4))
for i, a in enumerate(an):
    y = len(an) - 1 - i
    tot = sum(C[a]); left = 0
    for k, v in enumerate(C[a]):
        if not v:
            continue
        wv = 100 * v / tot
        ax.barh(y, wv, left=left, color=S[k], edgecolor='white', linewidth=1.2, height=0.62)
        if wv >= 7:
            ax.text(left + wv / 2, y, str(v), ha='center', va='center', fontsize=7.5,
                    color='white' if k in (0, 1, 5, 6) else INK)
        left += wv
ax.set_yticks(range(len(an))); ax.set_yticklabels(an[::-1], fontsize=8)
ax.set_xlim(0, 100); ax.set_xlabel('Share of analysed EN-pass/BN-fail cases (%)')
ax.grid(axis='y', visible=False)
for k, n in enumerate(cn):
    ax.barh(0, 0, color=S[k], label=n)
ax.legend(loc='upper center', bbox_to_anchor=(0.45, -0.18), ncol=3, fontsize=7.5)
save(fig, 'f3_confound.png')

# ---------- F4: where failures originate ----------
orig = ['Task-level reasoning', 'Execution-level (tool choice, args, execution)', 'Control (verification, termination)',
        'Final response only', 'Unclear']
O = {'OfficeBench gemma (42)': [18, 6, 3, 15, 0], 'OfficeBench gpt-oss (25)': [13, 3, 6, 3, 0],
     'τ² gemma (40)': [17, 10, 12, 1, 0], 'τ² gpt-oss (26)': [16, 3, 4, 0, 3],
     'WorkBench gemma (7)': [5, 2, 0, 0, 0], 'WorkBench gpt-oss (15)': [2, 12, 1, 0, 0],
     'TAC gemma (8)*': [2, 2, 3, 0, 1]}
fig, ax = plt.subplots(figsize=(7.2, 3.3))
for i, a in enumerate(an):
    y = len(an) - 1 - i
    tot = sum(O[a]); left = 0
    for k, v in enumerate(O[a]):
        if not v:
            continue
        wv = 100 * v / tot
        ax.barh(y, wv, left=left, color=S[k], edgecolor='white', linewidth=1.2, height=0.62)
        if wv >= 7:
            ax.text(left + wv / 2, y, str(v), ha='center', va='center', fontsize=7.5,
                    color='white' if k in (0, 1) else INK)
        left += wv
ax.set_yticks(range(len(an))); ax.set_yticklabels(an[::-1], fontsize=8)
ax.set_xlim(0, 100); ax.set_xlabel('Share of analysed cases by first failure point (%)')
ax.grid(axis='y', visible=False)
for k, n in enumerate(orig):
    ax.barh(0, 0, color=S[k], label=n)
ax.legend(loc='upper center', bbox_to_anchor=(0.45, -0.18), ncol=3, fontsize=7.5)
save(fig, 'f4_origin.png')

# ---------- F5: OfficeBench success by number of apps ----------
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)
sizes = ['1 app\n(n=93)', '2 apps\n(n=95)', '3 apps\n(n=112)']
data = {'gemma4:31b': ([67.7, 63.2, 25.0], [51.6, 53.7, 25.0]), 'gpt-oss:20b': ([44.1, 38.9, 7.1], [53.8, 43.2, 13.4])}
for ax, (m, (e, b)) in zip(axs, data.items()):
    for j in range(3):
        for x, v, c in ((j - 0.2, e[j], EN), (j + 0.2, b[j], BN)):
            ax.bar(x, v, 0.38, color=c, edgecolor='white', linewidth=1)
            ax.text(x, v + 1.5, f'{v:.0f}', ha='center', fontsize=7.5, color=INK2)
    ax.set_xticks(range(3)); ax.set_xticklabels(sizes, fontsize=8)
    ax.set_title(f'OfficeBench · {m}', fontsize=9, color=INK)
    ax.grid(axis='x', visible=False); ax.set_ylim(0, 80)
axs[0].set_ylabel('Success rate (%)')
axs[0].bar(0, 0, color=EN, label='English'); axs[0].bar(0, 0, color=BN, label='Bangla')
axs[0].legend(loc='upper right', fontsize=8)
save(fig, 'f5_obsize.png')

# ---------- F6: tau2 automatic failure signals ----------
sig = ['Simulator\nended early', 'Write never\ncalled', 'Write with\nwrong args', 'Device action\nnot done']
T = {'gemma4:31b (failures: EN 110, BN 135)': ([26, 39, 19, 22], [46, 37, 19, 24]),
     'gpt-oss:20b (failures: EN 91, BN 90)': ([3, 34, 25, 17], [3, 43, 21, 13])}
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
for ax, (m, (e, b)) in zip(axs, T.items()):
    for j in range(4):
        for x, v, c in ((j - 0.2, e[j], EN), (j + 0.2, b[j], BN)):
            ax.bar(x, v, 0.38, color=c, edgecolor='white', linewidth=1)
            ax.text(x, v + 0.8, str(v), ha='center', fontsize=7, color=INK2)
    ax.set_xticks(range(4)); ax.set_xticklabels(sig, fontsize=7.5)
    ax.set_title(f'τ²-bench · {m}', fontsize=8.5, color=INK)
    ax.grid(axis='x', visible=False); ax.set_ylim(0, 52)
axs[0].set_ylabel('Failed runs')
axs[0].bar(0, 0, color=EN, label='English'); axs[0].bar(0, 0, color=BN, label='Bangla')
axs[0].legend(loc='upper right', fontsize=8)
save(fig, 'f6_tau2signals.png')

# ---------- F7: trajectory propagation chains ----------
CLR = {'task': S[0], 'exec': S[1], 'ctrl': S[2], 'ext': S[6], 'out': S[7]}
chains = [
    ('OfficeBench 1-20/3 · gemma · Bangla', [
        ('task', 'Step 1: name from\nBangla script\nlower-cased: "bob"'),
        ('exec', 'list_emails("bob")\n→ "No emails found"\n(case-sensitive)'),
        ('ctrl', 'Empty result\naccepted, no retry\nwith "Bob"'),
        ('out', 'Answers "no, 0"\n→ FAIL')]),
    ('OfficeBench 1-15/0 · gemma · Bangla', [
        ('task', 'Plan: re-send the\nwhole 12.9k-char\ndocument + sentence'),
        ('exec', 'Action exceeds\n512-token reply cap\n→ "Malformed action!"'),
        ('ctrl', 'Same long write\nretried 14 times,\nno chunking'),
        ('out', 'Step limit (20),\nno write → FAIL')]),
    ('WorkBench email:41 · gemma · Bangla', [
        ('task', 'Step 2: "last week"\ngrounded as rolling\n7 days (11-23..29)'),
        ('exec', 'Two windowed\nsearches return []'),
        ('ctrl', 'Undated search finds\nboth emails; agent\nrejects them'),
        ('out', 'No forward_email\n→ FAIL')]),
    ('τ²-bench airline 19 · gemma · Bangla', [
        ('task', 'Agent plan and\npolicy check match\nEnglish run'),
        ('exec', 'Agent asks user to\nconfirm cancellation'),
        ('ext', 'Simulated user:\n"yes … ###STOP###"\nin the same turn'),
        ('out', 'cancel_reservation\nnever called → FAIL')]),
    ('τ²-bench telecom · gemma · Bangla', [
        ('exec', 'Agent calls device\ntools itself\n→ "not found"'),
        ('exec', 'Falls back to vague\nfree-text instructions'),
        ('ext', 'Simulated user toggles\nwrong settings, skips\ndevice tools'),
        ('out', 'Device state not\nreached; transfer\n→ FAIL')]),
    ('TAC admin-remove-pages-pdf · Bangla', [
        ('exec', 'wget on WebDAV URL\n→ 401'),
        ('ctrl', 'Retries the same\nauthenticated URLs'),
        ('task', 'No alternative plan\n(English found the\npublic-share link)'),
        ('out', 'Gives up, no output\nfile → 0/3')]),
]
fig, ax = plt.subplots(figsize=(7.4, 8.4))
ax.set_xlim(0, 100); ax.set_ylim(0, len(chains) * 14 + 2); ax.axis('off')
bw, bh = 21.5, 8.2
for r, (title, steps) in enumerate(chains):
    y0 = (len(chains) - 1 - r) * 14 + 1.5
    ax.text(0.5, y0 + bh + 1.6, title, fontsize=8.5, color=INK, weight='bold', va='bottom')
    for k, (kind, txt) in enumerate(steps):
        x0 = 0.5 + k * 25.2
        ax.add_patch(FancyBboxPatch((x0, y0), bw, bh, boxstyle='round,pad=0.25,rounding_size=1.2',
                                    fc='white', ec=CLR[kind], lw=1.8))
        ax.add_patch(FancyBboxPatch((x0, y0 + bh - 1.1), bw, 1.1, boxstyle='square,pad=0',
                                    fc=CLR[kind], ec=CLR[kind], lw=0))
        ax.text(x0 + bw / 2, y0 + (bh - 1.1) / 2, txt, ha='center', va='center', fontsize=6.9, color=INK)
        if k < len(steps) - 1:
            ax.add_patch(FancyArrowPatch((x0 + bw + 0.4, y0 + bh / 2), (x0 + 25.2 - 0.4, y0 + bh / 2),
                                         arrowstyle='-|>', mutation_scale=9, color=MUTED, lw=1.1))
leg = [('task', 'Task-level reasoning'), ('exec', 'Execution-level action'), ('ctrl', 'Control: verify / retry / stop'),
       ('ext', 'External: user simulator'), ('out', 'Final outcome')]
for k, (kind, name) in enumerate(leg):
    x, y = 0.5 + (k % 3) * 33, -2.2 - (k // 3) * 3.0
    ax.add_patch(FancyBboxPatch((x, y), 2.4, 1.6, boxstyle='square,pad=0', fc=CLR[kind], ec=CLR[kind]))
    ax.text(x + 3.2, y + 0.8, name, fontsize=7, va='center', color=INK2)
ax.set_ylim(-6, len(chains) * 14 + 2)
save(fig, 'f7_chains.png')
print('figures written to', OUT)
