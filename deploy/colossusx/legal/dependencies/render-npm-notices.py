"""Render collected npm legal notices without changing their text."""
import argparse
import json
import pathlib

parser = argparse.ArgumentParser()
parser.add_argument('inventory', type=pathlib.Path)
parser.add_argument('output', type=pathlib.Path)
parser.add_argument('--supplemental', type=pathlib.Path)
args = parser.parse_args()
data = json.loads(args.inventory.read_text())
supplemental = {}
if args.supplemental:
    supplemental = {(p['name'], p['version']): p for p in json.loads(args.supplemental.read_text())['packages']}
parts = [
    'ColossusX third-party npm notices\n',
    'These notices were collected from the installed dependency manifests and',
    'license files identified by the accompanying inventory. Dependencies retain',
    'their own licenses. This collection does not relicense any dependency.',
    'Build/development tools may be included; inclusion is not a claim that every',
    'listed dependency is shipped to browser clients.\n',
]
seen = set()
for package in sorted(data['packages'], key=lambda p: (p['name'] or '', p['version'] or '', p['path'])):
    notices = package['legalFiles'] or supplemental.get((package['name'], package['version']), {}).get('legalFiles', [])
    signature = (package['name'], package['version'], tuple((f['file'], f['sha256']) for f in notices))
    if signature in seen:
        continue
    seen.add(signature)
    parts.extend(['=' * 78, f"{package['name']}@{package['version']}",
                  'Declared license: ' + json.dumps(package['declaredLicense'], ensure_ascii=True)])
    if not notices:
        parts.append('No top-level license/notice file was present in the scanned package.\n')
    for notice in notices:
        if notice.get('source'):
            parts.append('Supplemental upstream notice: ' + notice['source'])
        parts.extend(['\n--- ' + notice['file'] + ' ---\n', notice['text'].rstrip(), ''])
args.output.write_text('\n'.join(parts) + '\n')
print(f'Wrote {len(seen)} package/version/notice sets to {args.output}')
