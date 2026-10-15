"""Cross-tabulate first failure point (RQ2) against cause (RQ3) for the 163 EN-pass/BN-fail cases.

Source: the per-case trace notes in the appendices of the four failure-analysis reports
(sobhar_kaj/*_FAILURE_ANALYSIS.pdf), extracted to text. Worked examples in the report bodies are
skipped; only appendix notes are counted, so each case is counted once.

    python analysis/acl_stage_by_cause.py <dir with OFFICEBENCH.txt TAU2.txt WORKBENCH.txt TAC.txt>
"""
import json, os, re, sys
from collections import Counter, defaultdict

D = sys.argv[1] if len(sys.argv) > 1 else 'sobhar_kaj_txt'

STAGE = {
    'Instruction understanding': 'task', 'Entity or slot grounding': 'task', 'Task constraint preservation': 'task',
    'Planning': 'task', 'Tool selection': 'exec', 'Tool-argument construction': 'exec', 'Tool execution': 'exec',
    'Result verification': 'control', 'Premature termination': 'control', 'Final response only': 'final',
    'Unclear': 'unclear'}


def cause(text):
    t = text.lower()
    if 'genuine' in t: return 'C1'
    if 'simulator' in t or 'npc' in t: return 'C2'
    if 'translation' in t: return 'C3'
    if 'tool/environment' in t or 'tool / env' in t: return 'C4'
    if 'benchmark' in t and 'ambiguity' in t: return 'C5'
    if 'general model weakness' in t: return 'C6'
    if 'unclear' in t or 'noise' in t: return 'C7'
    raise ValueError(text)


def stage(text):
    for k, v in STAGE.items():
        if text.strip().startswith(k):
            return k, v
    raise ValueError(text)


def notes(block):
    """Yield (first failure point, confound text, header text) for every note in a block."""
    flat = re.sub(r'\s+', ' ', block)
    ffp = [m for m in re.finditer(r'First failure point: (.*?) · Type:', flat)]
    for i, m in enumerate(ffp):
        end = ffp[i + 1].start() if i + 1 < len(ffp) else len(flat)
        seg = flat[m.end():end]
        c = re.search(r'Confound: (.*?)(?:\(| · |Evidence:|$)', seg)
        head = flat[max(0, m.start() - 1500):m.start()]
        yield m.group(1), c.group(1), head


def read(name):
    return open(os.path.join(D, name), encoding='utf-8', errors='replace').read()


rows = []  # (benchmark, model, stage_label, stage_group, cause)
ob = read('OFFICEBENCH.txt')
a, dd, c_ = ob.index('Appendix A. Trace notes for all 42'), ob.index('Appendix D. Trace notes for the 25'), ob.index('Appendix C. Reproduce')
for blk, model in ((ob[a:ob.index('Appendix B. Comparison groups')], 'gemma'), (ob[dd:c_], 'gpt-oss')):
    for f, c, _ in notes(blk):
        s, g = stage(f); rows.append(('OB', model, s, g, cause(c)))

tau = read('TAU2.txt')
blk = tau[tau.index('Appendix A. Trace notes for all 66'):tau.index('Appendix B. Comparison groups')]
flat = re.sub(r'\s+', ' ', blk)
heads = [(m.start(), m.group(1)) for m in re.finditer(r'· (gemma4:31b|gpt-oss:20b) · C\d', flat)]
for m in re.finditer(r'First failure point: (.*?) · Type:', flat):
    model = [h for h in heads if h[0] < m.start()][-1][1]
    seg = flat[m.end():m.end() + 600]
    c = re.search(r'Confound: (.*?)(?:\(| · |Evidence:|$)', seg).group(1)
    s, g = stage(m.group(1)); rows.append(('tau2', 'gemma' if 'gemma' in model else 'gpt-oss', s, g, cause(c)))

wb = read('WORKBENCH.txt')
ia, ib, ic = (wb.index('Appendix A. Trace notes for the 7'), wb.index('Appendix B. Trace notes for the 15'),
              wb.index('Appendix C. EN-fail/BN-pass'))
for blk, model in ((wb[ia:ib], 'gemma'), (wb[ib:ic], 'gpt-oss')):
    for f, c, _ in notes(blk):
        s, g = stage(f); rows.append(('WB', model, s, g, cause(c)))

tac = read('TAC.txt')
blk = tac[tac.index('Appendix A. Trace notes for the 8'):tac.index('Appendix B. Every paired task-run')]
for f, c, _ in notes(blk):
    s, g = stage(f); rows.append(('TAC', 'gemma', s, g, cause(c)))

out = {'n_cases': len(rows)}
# marginals per analysis, to check against the paper's Tables 3 (stage) and 4 (cause)
marg = defaultdict(lambda: {'stage': Counter(), 'cause': Counter(), 'n': 0})
for b, m, s, g, c in rows:
    k = f'{b} {m}'; marg[k]['stage'][g] += 1; marg[k]['cause'][c] += 1; marg[k]['n'] += 1
out['marginals'] = {k: {'n': v['n'], 'stage': dict(v['stage']), 'cause': dict(v['cause'])} for k, v in marg.items()}
# stage x cause cross-tab, all cases
ct = defaultdict(Counter)
for b, m, s, g, c in rows:
    ct[g][c] += 1
out['stage_by_cause'] = {g: dict(ct[g]) for g in ['task', 'exec', 'control', 'final', 'unclear']}
# where the checker (C5) and simulator (C2) cases sit, by benchmark
out['C5_stages'] = dict(Counter(f'{b}:{s}' for b, m, s, g, c in rows if c == 'C5'))
out['C2_stages'] = dict(Counter(f'{b}:{s}' for b, m, s, g, c in rows if c == 'C2'))
out['final_response_causes'] = dict(Counter(f'{b}:{c}' for b, m, s, g, c in rows if g == 'final'))
out['premature_termination_causes'] = dict(Counter(f'{b}:{c}' for b, m, s, g, c in rows if s == 'Premature termination'))
json.dump(out, open('analysis/acl_stage_by_cause.json', 'w', encoding='utf-8'), indent=1)
print(json.dumps(out, indent=1))
