"""Render analysis/failure_analysis_report.md to PDF (markdown -> HTML -> headless Edge/Chrome).

A browser engine is used because reportlab does not shape Bengali conjuncts. Only the markdown subset the report
uses is handled: headings, paragraphs, bullet/numbered lists, pipe tables, code fences, **bold**, *italic*, `code`.

    python analysis/fa_report_pdf.py [out.pdf]
"""
import html, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'failure_analysis_report.md')
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, 'failure_analysis_report.pdf')
BROWSERS = [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files\Google\Chrome\Application\chrome.exe']


def inline(t):
    codes = []

    def stash(m):
        codes.append(html.escape(m.group(1)))
        return '\x00%d\x00' % (len(codes) - 1)
    t = re.sub(r'`([^`]+)`', stash, t)
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*([^*\n]+?)\*(?![\w*])', r'<em>\1</em>', t)
    return re.sub(r'\x00(\d+)\x00', lambda m: '<code>%s</code>' % codes[int(m.group(1))], t)


def split_row(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def convert(md):
    out, i, lines = [], 0, md.split('\n')
    para = []

    def flush():
        if para:
            out.append('<p>%s</p>' % inline(' '.join(para)))
            para.clear()

    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```'):
            flush()
            j = i + 1
            buf = []
            while j < len(lines) and not lines[j].startswith('```'):
                buf.append(lines[j])
                j += 1
            out.append('<pre>%s</pre>' % html.escape('\n'.join(buf)))
            i = j + 1
            continue
        if ln.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:|-]+\|$', lines[i + 1].strip()):
            flush()
            head = split_row(ln)
            al = ['right' if c.endswith(':') and not c.startswith(':') else 'left' for c in split_row(lines[i + 1])]
            j = i + 2
            body = []
            while j < len(lines) and lines[j].startswith('|'):
                body.append(split_row(lines[j]))
                j += 1
            h = ''.join('<th style="text-align:%s">%s</th>' % (al[k], inline(c)) for k, c in enumerate(head))
            b = ''.join('<tr>%s</tr>' % ''.join('<td style="text-align:%s">%s</td>' % (al[k] if k < len(al) else 'left', inline(c))
                                                for k, c in enumerate(r)) for r in body)
            out.append('<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (h, b))
            i = j
            continue
        m = re.match(r'^!\[(.*)\]\((\S+?)(?: "(\w+)")?\)$', ln)
        if m:
            flush()
            cls = ' class="wide"' if m.group(3) == 'wide' else ''
            out.append('<figure%s><img src="%s" alt="%s"><figcaption>%s</figcaption></figure>' % (cls, html.escape(m.group(2)), html.escape(m.group(1)), inline(m.group(1))))
            i += 1
            continue
        m = re.match(r'^(#{1,3}) (.*)$', ln)
        if m:
            flush()
            out.append('<h%d>%s</h%d>' % (len(m.group(1)), inline(m.group(2)), len(m.group(1))))
            i += 1
            continue
        if re.match(r'^- ', ln) or re.match(r'^\d+\. ', ln):
            flush()
            tag = 'ul' if ln.startswith('- ') else 'ol'
            items = []
            j = i
            while j < len(lines) and (re.match(r'^- ', lines[j]) if tag == 'ul' else re.match(r'^\d+\. ', lines[j])):
                items.append(re.sub(r'^(- |\d+\. )', '', lines[j]))
                j += 1
            start = ' start="%s"' % re.match(r'^(\d+)\.', ln).group(1) if tag == 'ol' else ''
            out.append('<%s%s>%s</%s>' % (tag, start, ''.join('<li>%s</li>' % inline(x) for x in items), tag))
            i = j
            continue
        if not ln.strip():
            flush()
        else:
            para.append(ln.strip())
        i += 1
    flush()
    return '\n'.join(out)


CSS = """
@page { size: A4; margin: 16mm 15mm 17mm 15mm; }
html { font-family: "Segoe UI", "Nirmala UI", Arial, sans-serif; color: #18202c; font-size: 9.6pt; line-height: 1.5; }
body { margin: 0; }
h1 { font-size: 19pt; line-height: 1.2; margin: 0 0 6pt; }
h2 { font-size: 13.5pt; margin: 18pt 0 5pt; padding-top: 6pt; border-top: 1px solid #dce1e8; break-after: avoid; }
h3 { font-size: 10.6pt; color: #2d5a9b; margin: 11pt 0 3pt; break-after: avoid; }
p { margin: 0 0 6pt; }
em { color: #3a4456; }
code { font-family: Consolas, monospace; font-size: 8.6pt; background: #f1f3f6; padding: 0 2pt; border-radius: 2pt; }
pre { font-family: Consolas, monospace; font-size: 8.4pt; background: #f6f7f9; border: 1px solid #dce1e8; padding: 6pt 8pt; white-space: pre-wrap; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 9pt; font-size: 8.2pt; line-height: 1.35; break-inside: avoid; }
th[style*="right"], td[style*="right"] { white-space: nowrap; }
thead { display: table-header-group; }
th { background: #2d5a9b; color: #fff; padding: 3pt 5pt; vertical-align: bottom; }
td { padding: 2.6pt 5pt; border-bottom: 1px solid #dce1e8; vertical-align: top; overflow-wrap: anywhere; }
tr { break-inside: avoid; }
tbody tr:nth-child(even) td { background: #f6f7f9; }
ul, ol { margin: 0 0 7pt; padding-left: 15pt; }
li { margin: 0 0 1.6pt; }
li, p { orphans: 2; widows: 2; }
h3 + ul { break-before: avoid; }
figure { margin: 6pt 0 10pt; break-inside: avoid; }
figure img { width: 100%; display: block; }
figcaption { font-size: 8.4pt; color: #3a4456; margin-top: 3pt; line-height: 1.4; }
@page wide { size: A4 landscape; margin: 12mm 12mm 12mm 12mm; }
figure.wide { page: wide; break-before: page; break-after: page; margin: 0; }
figure.wide img { width: 100%; max-height: 165mm; object-fit: contain; }
"""


BASE = 'file:///' + HERE.replace(chr(92), '/') + '/'


def main():
    md = open(SRC, encoding='utf-8').read()
    doc = '<!doctype html><html><head><meta charset="utf-8"><base href="%s"><title>OfficeBench failure analysis</title><style>%s</style></head><body>%s</body></html>' % (BASE, CSS, convert(md))
    tmp = os.path.join(tempfile.gettempdir(), 'fa_report.html')
    open(tmp, 'w', encoding='utf-8').write(doc)
    exe = next((b for b in BROWSERS if os.path.exists(b)), None)
    if not exe:
        sys.exit('no Edge/Chrome found')
    if os.path.exists(OUT):
        os.remove(OUT)
    subprocess.run([exe, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--print-to-pdf=' + OUT,
                    'file:///' + tmp.replace('\\', '/')], check=True, timeout=180, capture_output=True)
    import time
    last, t0 = -1, time.time()
    while time.time() - t0 < 90:
        cur = os.path.getsize(OUT) if os.path.exists(OUT) else -1
        if cur > 0 and cur == last:
            break
        last = cur
        time.sleep(1.5)
    if not os.path.exists(OUT):
        sys.exit('browser produced no PDF')
    print('wrote', OUT, os.path.getsize(OUT), 'bytes')


main()
