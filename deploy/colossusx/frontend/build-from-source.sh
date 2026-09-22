#!/usr/bin/env bash
# ColossusX source rebuild entry point. Created 2026-09-21; GPL-3.0-only.
set -euo pipefail
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
docker buildx version >/dev/null
builder_args=()
if [[ -n "${BUILDX_BUILDER:-}" ]]; then
  builder_args=(--builder "$BUILDX_BUILDER" --allow network.host)
fi
docker buildx build "${builder_args[@]}" --load --network=host --progress=plain \
  --file "$source_root/Dockerfile.colossusx" --target deps \
  --tag colossusx-frontend-deps:2.7.2 "$source_root"
docker buildx build "${builder_args[@]}" --load --network=host --progress=plain \
  --file "$source_root/Dockerfile.colossusx" \
  --build-arg GIT_TAG=v2.7.2-colossusx \
  --build-arg GIT_COMMIT_SHA=446c409eeb54274aab90ff371a705f9699cd84ef \
  --build-arg COLOSSUSX_SOURCE_SHA256="${COLOSSUSX_SOURCE_SHA256:-local-rebuild}" \
  --tag colossusx-frontend:2.7.2-branding "$source_root"
