"""Retrieve missing notice text from npm's recorded Git commit; never assume HEAD."""
import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('inventory', type=pathlib.Path)
parser.add_argument('output', type=pathlib.Path)
args = parser.parse_args()
packages = json.loads(args.inventory.read_text())['packages']
selected = {(p['name'], p['version']): p for p in packages if not p['legalFiles'] and p['name'] and p['version']}

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'ColossusX-license-review/1.0'})
    with urllib.request.urlopen(req, timeout=12) as response:
        return response.read(1024 * 1024)

def inspect(pair):
    name, version = pair
    result = {'name': name, 'version': version}
    try:
        result['metadataUrl'] = 'https://registry.npmjs.org/' + urllib.parse.quote(name, safe='@') + '/' + urllib.parse.quote(version, safe='')
        metadata = json.loads(fetch(result['metadataUrl']))
        commit = metadata.get('gitHead')
        repository = metadata.get('repository')
        if isinstance(repository, dict):
            repository = repository.get('url', '')
        match = re.search(r'github\.com[/:]([^/]+/[^/#]+?)(?:\.git)?$', repository or '')
        if not commit or not re.fullmatch('[0-9a-f]{40}', commit) or not match:
            result['unresolved'] = 'No exact GitHub commit/repository pair in published npm metadata'
            return result
        result['repository'] = match.group(1)
        result['commit'] = commit
        base = 'https://raw.githubusercontent.com/' + match.group(1) + '/' + commit + '/'
        result['legalFiles'] = []
        for filename in ['LICENSE', 'LICENSE.md', 'LICENSE-MIT', 'LICENSE.txt', 'license', 'license.md', 'LICENCE']:
            try:
                data = fetch(base + filename)
            except Exception:
                continue
            result['legalFiles'].append({'file': filename, 'source': base + filename, 'sha256': hashlib.sha256(data).hexdigest(), 'text': data.decode('utf-8')})
            break
        if not result['legalFiles']:
            result['unresolved'] = 'No root license file at checked common names in recorded commit'
    except Exception as error:
        result['unresolved'] = type(error).__name__ + ': ' + str(error)
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    records = list(pool.map(inspect, sorted(selected)))
args.output.write_text(json.dumps({'scope': 'Supplemental upstream root notices at exact commits recorded in npm metadata. Verify applicability to any separately licensed subdirectory or bundled assets.', 'packages': records}, indent=2) + '\n')
print(json.dumps({'checked': len(records), 'resolved': sum(bool(p.get('legalFiles')) for p in records), 'unresolved': sum('unresolved' in p for p in records)}))
