"""Check README/doc links, their exact Git objects, and optional public HTTP links.

No changes are made to GitHub. Local media are unpublished candidate files.
"""
from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import subprocess
import urllib.request
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
COMMIT = '22999d28d8fe22f863fc8f62eaa45a57256083d0'


def slug(text):
    return re.sub(r'[^\w\- ]', '', text.lower()).replace(' ', '-')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-root', type=Path, required=True)
    ap.add_argument('--online', action='store_true')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    local, anchors, remote = [], [], {}
    files = [ROOT/'README.md']+sorted((ROOT/'docs/homepage').glob('*.md'))+sorted((ROOT/'docs/homepage-animation').glob('*.md'))
    for file in files:
        text = file.read_text(encoding='utf-8')
        links = re.findall(r'\]\(([^\s)]+)\)', text)+re.findall(r'(?:href|src)="([^\"]+)"', text)
        for link in links:
            url = urlsplit(link)
            if url.scheme:
                assert url.scheme == 'https', link
                remote[link] = dict(url=link)
                continue
            target = (file.parent/unquote(url.path)).resolve() if url.path else file
            assert target.is_file(), (file, link)
            if url.fragment and target.suffix == '.md':
                target_text = target.read_text(encoding='utf-8')
                ids = {slug(m[1]) for m in re.finditer(r'^#{1,6} (.+)$', target_text, re.M)}
                assert url.fragment in ids, (file, link, ids)
                anchors.append(dict(document=file.relative_to(ROOT).as_posix(), link=link, passed=True))
            local.append(dict(document=file.relative_to(ROOT).as_posix(), link=link, file_exists=True))
    for item in remote.values():
        parts = urlsplit(item['url']).path.strip('/').split('/')
        assert parts[:2] == ['Scophield', 'drosophila-fault-injection'], item
        if len(parts)>4 and parts[2] in ['blob','tree'] and re.fullmatch(r'[0-9a-f]{40}',parts[3]):
            commit = parts[3]; suffix = '/'.join(parts[4:])
            spec = commit+(':'+suffix if suffix else '^{commit}')
            found = any(subprocess.run(['git','cat-file','-e',spec],cwd=folder,capture_output=True).returncode==0 for folder in [args.data_root,ROOT])
            assert found, (item, spec)
            item['exact_git_object_verified'] = True
    if args.online:
        def check(item):
            req = urllib.request.Request(item['url'], method='HEAD', headers={'User-Agent':'research-homepage-check/1.0'})
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    item.update(http_status=response.status, final_url=response.url)
            except Exception as e:
                item['network_error'] = str(e)
            return item
        with ThreadPoolExecutor(max_workers=3) as pool:
            checked = list(pool.map(check, remote.values()))
        pdf_url = f'https://raw.githubusercontent.com/Scophield/drosophila-fault-injection/{COMMIT}/paper/iscas2027-v10.1-count-candidate.pdf'
        with urllib.request.urlopen(pdf_url, timeout=45) as response:
            data = response.read()
        actual = hashlib.sha256(data).hexdigest()
        expected = hashlib.sha256((args.data_root/'paper/iscas2027-v10.1-count-candidate.pdf').read_bytes()).hexdigest()
        assert actual == expected
        pdf = dict(url=pdf_url, sha256=actual, local_public_bytes_equal=True)
    else:
        checked = list(remote.values()); pdf = dict(online_checked=False)
    report = dict(local_file_links=len(local), local_anchors=len(anchors), external_links=len(checked),
                  links=local, anchors=anchors, remote=checked, public_pdf=pdf,
                  all_http_links_passed=all(r.get('http_status')==200 for r in checked) if args.online else None,
                  github_default_homepage_updated=False, github_candidate_media_rendering_verified=False)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['links','anchors','remote']},indent=2))
    if args.online and not report['all_http_links_passed']:
        raise RuntimeError('Some public links need review; see report.')


if __name__ == '__main__':
    main()
