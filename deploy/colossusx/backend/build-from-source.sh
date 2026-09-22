#!/usr/bin/env bash
# ColossusX backend source rebuild entry point. Created 2026-09-21; GPL-3.0-only.
set -euo pipefail
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source_sha=${COLOSSUSX_SOURCE_SHA256:-local-rebuild}
source_url=${COLOSSUSX_SOURCE_URL:-https://colossusx.make-cph-great-again.community/source/}
docker build --network=host --progress=plain \
  --file "$source_root/Dockerfile.colossusx" \
  --build-arg RELEASE_VERSION=10.2.6 \
  --build-arg BLOCKSCOUT_VERSION=v10.2.6-colossusx \
  --build-arg CHAIN_TYPE=ethereum \
  --build-arg COLOSSUSX_SOURCE_SHA256="$source_sha" \
  --build-arg COLOSSUSX_SOURCE_URL="$source_url" \
  --tag colossusx-backend:10.2.6 "$source_root"
