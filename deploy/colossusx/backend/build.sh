#!/usr/bin/env bash
# Prepare and optionally build the exact ColossusX backend source. GPL-3.0-only.
# Created 2026-09-21. Does not alter production containers or databases.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
deploy_dir=$(cd -- "$script_dir/.." && pwd)
repo_dir=$(cd -- "$deploy_dir/../.." && pwd)
if [[ $# -gt 1 || (${1:-} != '' && ${1:-} != --prepare-only) ]]; then
  echo "Usage: $0 [--prepare-only]" >&2
  exit 2
fi
mkdir -p "$deploy_dir/.build" "$deploy_dir/source-dist"
work_dir=$(mktemp -d "$deploy_dir/.build/backend.XXXXXX")
source_dir="$work_dir/backend"
python3 -B - "$deploy_dir/release/assemble.py" "$repo_dir" "$source_dir" <<'PY'
import importlib.util
from pathlib import Path
import subprocess
import sys
script, repository, target = map(Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location('colossusx_release', script)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
archive = target.parent / 'upstream.tar'
with archive.open('wb') as handle:
    subprocess.run(['git', '-C', str(repository), 'archive', '--format=tar', release.BACKEND_COMMIT], stdout=handle, check=True)
release.safe_extract(archive, target)
archive.unlink()
release.prepare_backend(target)
release.scan_local_material(target)
PY
archive="$work_dir/backend.tar.gz"
tar --sort=name --mtime=2026-09-21T00:00:00Z --owner=0 --group=0 --numeric-owner \
  -C "$source_dir" -cf - . | gzip -n > "$archive"
source_sha=$(sha256sum "$archive" | cut -d ' ' -f 1)
filename="colossusx-backend-10.2.6-${source_sha:0:16}.tar.gz"
target="$deploy_dir/source-dist/$filename"
cp "$archive" "$target"
printf '%s  %s\n' "$source_sha" "$filename" > "$target.sha256"
printf 'Prepared source: %s\nArchive: %s\nSHA256: %s\n' "$source_dir" "$target" "$source_sha"
if [[ ${1:-} != --prepare-only ]]; then
  COLOSSUSX_SOURCE_SHA256="$source_sha" \
  COLOSSUSX_SOURCE_URL="https://colossusx.make-cph-great-again.community/source/$filename" \
    "$source_dir/build-colossusx.sh"
  printf '%s\n' "$filename" > "$deploy_dir/source-dist/backend-current.txt"
fi
