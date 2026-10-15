"""Cohen's kappa between two annotators' primary codes (and the benchmark/agent grouping)."""
import csv, sys, collections

def load(path):
    return {r['id']: r for r in csv.DictReader(open(path, encoding='utf-8'))}

def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca = collections.Counter(a for a, _ in pairs)
    cb = collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return po, pe, (po - pe) / (1 - pe) if pe < 1 else 1.0

def side(code):
    return 'agent' if code.startswith('A-') else 'benchmark'

a, b = load(sys.argv[1]), load(sys.argv[2])
ids = [i for i in a if i in b]
fine = [(a[i]['primary'], b[i]['primary']) for i in ids]
coarse = [(side(x), side(y)) for x, y in fine]
for name, pairs in [('primary code', fine), ('benchmark vs agent', coarse)]:
    po, pe, k = kappa(pairs)
    print(f'{name}: n={len(pairs)} observed={po:.3f} chance={pe:.3f} kappa={k:.3f}')
print('disagreements:')
for i in ids:
    if a[i]['primary'] != b[i]['primary']:
        print(f"  {i}: A={a[i]['primary']}  B={b[i]['primary']}  | B says: {b[i]['rationale']}")
