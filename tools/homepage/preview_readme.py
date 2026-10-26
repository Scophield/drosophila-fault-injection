"""Render this README's deliberately small Markdown subset for local visual QA.

No README CSS/JS is added, no web page is published, and no packages are needed.
GitHub's actual renderer is a separate post-publication check.
"""
from pathlib import Path
import html
import re
import argparse
import os

ROOT = Path(__file__).resolve().parents[2]


def slug(text):
    return re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')


def inline(text):
    chunks = []
    def hold(value):
        chunks.append(value)
        return f'@@SLOT{len(chunks)-1}@@'
    text = re.sub(r'`([^`]+)`', lambda m: hold('<code>'+html.escape(m[1])+'</code>'), text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: hold('<a href="'+html.escape(m[2], quote=True)+'">'+inline(m[1])+'</a>'), text)
    text = html.escape(text, quote=False)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    for i in reversed(range(len(chunks))):
        text = text.replace(f'@@SLOT{i}@@', chunks[i])
    return text


def render(text):
    lines = text.splitlines(); output = []; i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if line.startswith('```'):
            body = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                body.append(lines[i]); i += 1
            output.append('<pre><code>'+html.escape('\n'.join(body))+'</code></pre>'); i += 1; continue
        heading = re.match(r'^(#{1,6}) (.+)$', line)
        if heading:
            level, title = len(heading[1]), heading[2]
            output.append(f'<h{level} id="{slug(title)}">{inline(title)}</h{level}>'); i += 1; continue
        if line.startswith('<'):
            output.append(line); i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append([x.strip() for x in lines[i].strip('|').split('|')]); i += 1
            body = '<thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>'
            body += ''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in rows[2:])
            output.append('<div class="table-wrap"><table>'+body+'</tbody></table></div>'); continue
        if re.match(r'^(?:\d+\.|-) ', line):
            ordered = not line.startswith('-'); tag = 'ol' if ordered else 'ul'; body = []
            pattern = r'^\d+\. ' if ordered else r'^- '
            while i < len(lines) and re.match(pattern, lines[i]):
                body.append('<li>'+inline(re.sub(pattern, '', lines[i]))+'</li>'); i += 1
            output.append('<'+tag+'>'+''.join(body)+'</'+tag+'>'); continue
        body = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|<|\||```|\d+\. |\- )', lines[i]):
            body.append(lines[i]); i += 1
        output.append('<p>'+inline(' '.join(body))+'</p>')
    return '\n'.join(output)


CSS = '''
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}
:root{--bg:#fff;--fg:#1f2328;--muted:#59636e;--line:#d1d9e0;--wash:#f6f8fa;--link:#0969da;--code:#818b981f}
body.dark{--bg:#0d1117;--fg:#f0f6fc;--muted:#9198a1;--line:#3d444d;--wash:#151b23;--link:#4493f8;--code:#656c7633}
header{background:var(--wash);border-bottom:1px solid var(--line);padding:14px 24px;font-size:14px;color:var(--muted)}
header strong{color:var(--fg)}.preview-note{max-width:1012px;margin:16px auto 0;padding:0 24px;font-size:12px;color:var(--muted)}
article{max-width:1012px;margin:16px auto 40px;border:1px solid var(--line);border-radius:6px;padding:32px}
h1,h2,h3{line-height:1.25;font-weight:600}h1{font-size:32px;margin:0 0 16px;padding-bottom:.3em;border-bottom:1px solid var(--line)}
h2{font-size:24px;margin:24px 0 16px;padding-bottom:.3em;border-bottom:1px solid var(--line)}h3{font-size:20px;margin:24px 0 16px}
p,pre,ol,ul,details,.table-wrap{margin:0 0 16px}a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
img{max-width:100%;height:auto;background:#fff;vertical-align:middle}code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:85%;padding:.2em .4em;background:var(--code);border-radius:6px}
pre{padding:16px;overflow:auto;background:var(--wash);border-radius:6px;font-size:13px;line-height:1.45}pre code{padding:0;background:none;font-size:100%}
ol,ul{padding-left:2em}li+li{margin-top:.35em}.table-wrap{overflow-x:auto}table{border-spacing:0;border-collapse:collapse;font-size:15px}th,td{padding:6px 13px;border:1px solid var(--line)}tr:nth-child(2n){background:var(--wash)}
summary{cursor:pointer;color:var(--link)}details[open] summary{margin-bottom:16px}details img{margin-top:8px}
@media(max-width:767px){header{padding:12px 16px;font-size:12px}.preview-note{padding:0 16px}article{margin:12px 0 0;border:0;border-radius:0;padding:16px}h1{font-size:26px}h2{font-size:22px}h3{font-size:18px}th,td{padding:6px 10px}}
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT/'preview')
    args = ap.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    text = (ROOT/'README.md').read_text(encoding='utf-8')
    body = render(text)
    # Resolve file links while keeping fragment navigation in this document.
    prefix = Path(os.path.relpath(ROOT, args.out.resolve())).as_posix()+'/'
    body = re.sub(r'(href|src)="([^"]+)"', lambda m: m[0] if m[2].startswith(('#','https://')) else m[1]+'="'+prefix+m[2]+'"', body)
    assert '@@SLOT' not in body
    for dark in [False, True]:
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local README preview</title><style>'+CSS+'</style></head>'
        page += '<body'+(' class="dark"' if dark else '')+'><header><strong>Scophield / drosophila-fault-injection</strong> &nbsp; README</header><div class="preview-note">Local preview of the actual README · unpublished · GitHub rendering remains to be verified after publication</div><article>'+body+'</article></body></html>'
        (args.out/('readme-dark.html' if dark else 'readme.html')).write_text(page, encoding='utf-8')
    media_page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Local media check</title><style>body{max-width:1000px;margin:24px auto;padding:16px;font:16px/1.5 system-ui}video{display:block;width:100%;background:white}section{margin-bottom:32px}</style></head><body><h1>Local media check — unpublished</h1>'
    for key, name in [('a','demo-a-delay'),('b','demo-b-control'),('c','demo-c-horizon'),('overview','overview')]:
        media_page += f'<section><h2>{name}</h2><video id="video-{key}" controls muted playsinline preload="metadata" poster="{prefix}media/paper-v10.1/{name}.png"><source src="{prefix}media/paper-v10.1/{name}.mp4" type="video/mp4"></video></section>'
    (args.out/'media.html').write_text(media_page+'</body></html>', encoding='utf-8')
    print(args.out/'readme.html')


if __name__ == '__main__':
    main()
