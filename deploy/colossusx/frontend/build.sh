#!/usr/bin/env bash
# Modified for ColossusX on 2026-09-21: preserve and identify build source.
set -euo pipefail

existing_image=
prepare_only=false
if (( $# > 0 )); then
  if [[ $# -eq 1 && "$1" == --prepare-only ]]; then
    prepare_only=true
  elif [[ $# -ne 2 || "$1" != --package-existing-image ]]; then
    printf 'Usage: %s [--prepare-only | --package-existing-image IMAGE]\n' "$0" >&2
    exit 2
  else
    existing_image=$2
  fi
fi

build_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# Keep build inputs on disk; /tmp can be tmpfs on production hosts.
mkdir -p "$build_dir/../.build"
source_dir=$(mktemp -d "$build_dir/../.build/frontend.XXXXXX")
trap 'rm -rf -- "$source_dir"' EXIT

curl --fail --silent --show-error --location --connect-timeout 15 --max-time 300 \
  https://codeload.github.com/blockscout/frontend/tar.gz/refs/tags/v2.7.2 \
  -o "$source_dir/source.tar.gz"
printf '%s  %s\n' \
  34f4758f639f029bfe91d47584e3dcdbd5033d72a6b32d0c93904a5e347f081f \
  "$source_dir/source.tar.gz" | sha256sum --check --status
tar -xzf "$source_dir/source.tar.gz" -C "$source_dir"
app_dir="$source_dir/frontend-2.7.2"

patch --directory "$app_dir" --strip=1 < "$build_dir/branding.patch"
mkdir -p "$app_dir/public/static/colossusx"
cp -a "$build_dir/assets/." "$app_dir/public/static/colossusx/"
cp "$build_dir/Dockerfile" "$app_dir/Dockerfile.colossusx"
cp "$build_dir/Dockerfile.deps" "$app_dir/Dockerfile.colossusx.deps"
cp "$build_dir/build-from-source.sh" "$app_dir/build-colossusx.sh"
cp "$build_dir/SOURCE-README.md" "$app_dir/COLOSSUSX_BUILD.md"
cp "$build_dir/../public-legal/Inter-OFL.txt" "$app_dir/public/static/fonts/Inter-OFL.txt"
mkdir -p "$app_dir/licenses"
cp "$build_dir/../public-legal/Poppins-OFL.txt" "$app_dir/licenses/Poppins-OFL.txt"
cp "$build_dir/../public-legal/CC0-1.0.txt" "$app_dir/licenses/CC0-1.0.txt"
# Distribution notices are preserved in source archives and served by the proxy.
# They do not affect the compiled frontend, so keep its Docker cache reusable.
printf '\n# ColossusX distribution-only notices, added 2026-09-21.\npublic/static/colossusx/LICENSE\nlicenses/CC0-1.0.txt\n' >> "$app_dir/.dockerignore"
chmod +x "$app_dir/build-colossusx.sh"

# Archive the clean build input, not a container filesystem or runtime .env.
tar --sort=name --mtime=2026-09-21T00:00:00Z --owner=0 --group=0 --numeric-owner \
  -czf "$source_dir/frontend-source.tar.gz" -C "$app_dir" .
source_sha256=$(sha256sum "$source_dir/frontend-source.tar.gz" | cut -d ' ' -f 1)
if [[ -n "$existing_image" ]]; then
  image_source=$(docker image inspect "$existing_image" --format '{{index .Config.Labels "org.colossusx.source.sha256"}}')
  if [[ "$image_source" != "$source_sha256" ]]; then
    printf 'Refusing to package source that differs from the image source label.\n' >&2
    exit 1
  fi
elif [[ "$prepare_only" == false ]]; then
  COLOSSUSX_SOURCE_SHA256="$source_sha256" "$app_dir/build-colossusx.sh"
fi

distribution_dir="$build_dir/../source-dist"
mkdir -p "$distribution_dir"
archive_name="colossusx-frontend-2.7.2-${source_sha256:0:16}.tar.gz"
install -m 644 "$source_dir/frontend-source.tar.gz" "$distribution_dir/$archive_name"
printf '%s  %s\n' "$source_sha256" "$archive_name" > "$distribution_dir/$archive_name.sha256"
if [[ "$prepare_only" == false ]]; then
  cp "$distribution_dir/$archive_name.sha256" "$distribution_dir/frontend.sha256"
  printf '%s\n' "$archive_name" > "$distribution_dir/current-frontend.txt"
  python3 "$build_dir/update-source-index.py"
else
  trap - EXIT
  printf 'Prepared build source: %s\n' "$app_dir"
fi
printf 'Source archive: %s\nSHA-256: %s\n' "$archive_name" "$source_sha256"
