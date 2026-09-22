"""Read exact-version Hex package archive metadata without installing dependencies."""
import concurrent.futures
import json
import pathlib
import re
import tarfile
import urllib.request

DEST = pathlib.Path(__file__).parent / 'backend-mix-lock.json'
data = json.loads(DEST.read_text())

def inspect(package):
    if package['type'] != 'hex':
        return package
    package['metadataUrl'] = 'https://repo.hex.pm/tarballs/{}-{}.tar'.format(package['hexName'], package['version'])
    try:
        request = urllib.request.Request(package['metadataUrl'], headers={'User-Agent': 'ColossusX-license-review/1.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            with tarfile.open(fileobj=response, mode='r|') as archive:
                for member in archive:
                    if member.name == 'metadata.config':
                        metadata = archive.extractfile(member).read(2 * 1024 * 1024).decode('utf-8')
                        match = re.search(r'\{<<"licenses">>,\s*\[(.*?)\]\}', metadata, re.S)
                        package['license'] = re.findall(r'<<"([^"]+)">>', match.group(1)) if match else []
                        package['licenseEvidence'] = 'licenses field from exact-version Hex tarball metadata.config; package bytes were not fully downloaded or independently checksum verified'
                        return package
                package['metadataError'] = 'metadata.config not found'
    except Exception as error:
        package['metadataError'] = type(error).__name__ + ': ' + str(error)
    return package

with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    data['packages'] = list(pool.map(inspect, data['packages']))
DEST.write_text(json.dumps(data, indent=2) + '\n')
print(json.dumps({'entries': len(data['packages']), 'metadataRetrieved': sum('licenseEvidence' in p for p in data['packages']), 'errors': sum('metadataError' in p for p in data['packages'])}))
