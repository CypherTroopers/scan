# ColossusX deployment

This deployment builds the modified GPL backend v10.2.6 and frontend v2.7.2 from
`../backend` and `../frontend`, and selects MIT-licensed stats v2.15.0 for the
backend 10.2 database schema. The backend includes the documented third-party
exclusions and English edits. Both application images record the hash of their
complete source archive. Read `../NOTICE.md` and keep the visible attribution,
legal notices, and matching backend/frontend source downloads available.

## Requirements and configuration

Install Docker Engine with Compose and Buildx, Bash, GNU tar, gzip, and Python
3.12 or newer for source assembly, download-page generation, and random secrets.
Build both custom application images before starting the deployment. Builds need
network access for pinned base images and locked packages. The backend toolchain
is Elixir 1.19.4 with Erlang/OTP 27.3.4.6; the frontend Dockerfile pins Node.js
22.14.0. Container images and dependencies retain their separate licenses.

Initial builds are memory intensive. Use a separate build host or a Buildx
builder with memory/CPU limits and adequate swap; avoid compiling both applications
concurrently on a small production server. `BUILDX_BUILDER` can select an existing
builder configured for that host.

`backend.env` and `frontend.env` contain public ColossusX network settings and
nonsecret operational settings. Review the RPC endpoint, chain ID, network/currency
names, image versions, memory/CPU limits, and hostnames for your own installation.
`compose.override.yml` and the Nginx configurations describe the ColossusX HTTPS
domain; adapt them before deploying under a different host. The local `.env` is
never supplied by this release.

The ColossusX indexer memory monitor is limited to 2 GiB inside its 3 GiB
container. Ethereum Beacon blob/deposit/status fetchers are disabled because they
do not describe this network. Rewards use `FETCH_REWARDS_WAY=colossusx` and
`INDEXER_DISABLE_BLOCK_REWARD_FETCHER=false` with the configured genesis hash.
The FHS-D adapter verifies native production, Common miner PoW and Common RPC
payouts without adding Ethereum gas rewards. Historical rewards are backfilled
automatically, with no database reset. See [the rules and API](backend/REWARDS.md)
before changing the protocol or adapting this deployment to another chain.

Generate secrets from the `deployment` directory. Exclusive creation refuses to
overwrite an existing `.env`:

```sh
python3 - <<'PY'
import os
import secrets

fd = os.open('.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as handle:
    handle.write('PUBLIC_IP=127.0.0.1\n')
    handle.write('DB_PASSWORD=' + secrets.token_hex(32) + '\n')
    handle.write('STATS_DB_PASSWORD=' + secrets.token_hex(32) + '\n')
    handle.write('SECRET_KEY_BASE=' + secrets.token_hex(64) + '\n')
PY
```

Set `PUBLIC_IP` in your local `.env`. Do not commit this file, share expanded
Compose configuration, copy production volumes, or reuse another operator's
secrets. Certificate paths in `host-nginx/` refer to certificates that you obtain
for your own domain; no certificate or private key is bundled.

## Package sources, build, and start

Run this Bash block from the clean independent release root. Set the public
source URL to your own deployment. The code packages both source trees before any
build generates local output, then builds them sequentially:

```bash
set -euo pipefail
sha256sum --check SHA256SUMS
source_base_url=https://colossusx.make-cph-great-again.community/source
mkdir -p deployment/source-dist
for component in backend frontend; do
  if [[ $component == backend ]]; then version=10.2.6; else version=2.7.2; fi
  archive="deployment/source-dist/$component-source.tar.gz"
  tar --sort=name --mtime=2026-09-21T00:00:00Z --owner=0 --group=0 --numeric-owner \
    -C "$component" -cf - . | gzip -n > "$archive"
  digest=$(sha256sum "$archive" | cut -d ' ' -f 1)
  filename="colossusx-$component-$version-${digest:0:16}.tar.gz"
  mv "$archive" "deployment/source-dist/$filename"
  printf '%s  %s\n' "$digest" "$filename" > "deployment/source-dist/$filename.sha256"
  if [[ $component == backend ]]; then
    printf '%s\n' "$filename" > deployment/source-dist/backend-current.txt
  else
    cp "deployment/source-dist/$filename.sha256" deployment/source-dist/frontend.sha256
    printf '%s\n' "$filename" > deployment/source-dist/current-frontend.txt
  fi
done
for component in backend frontend; do
  if [[ $component == backend ]]; then
    filename=$(cat deployment/source-dist/backend-current.txt)
  else
    filename=$(cat deployment/source-dist/current-frontend.txt)
  fi
  digest=$(cut -d ' ' -f 1 "deployment/source-dist/$filename.sha256")
  COLOSSUSX_SOURCE_SHA256="$digest" \
  COLOSSUSX_SOURCE_URL="$source_base_url/$filename" \
    "./$component/build-colossusx.sh"
done
python3 deployment/frontend/update-source-index.py
cd deployment
docker compose config --quiet
docker compose up -d
docker compose ps
```

The expected image tags are `colossusx-backend:10.2.6` and
`colossusx-frontend:2.7.2-branding`. The full source build scripts above work from
this independent release. The deployment's upstream reconstruction wrappers have
additional prerequisites: the backend wrapper needs the pinned upstream Git
commit, while the frontend wrapper downloads its pinned upstream archive and
applies the reviewed branding patch.

Review source archives for secrets before starting public service. Keep archives
for previous deployed builds and use a new filename/checksum after source changes.
Do not archive an unrelated newer backend checkout or recursively include archive
outputs. Building from a tree containing local dependencies or credentials would
include those files; use a fresh verified release tree for packaging.

Configure host Nginx and HTTPS using the templates for your domain. Validate with
`nginx -t` before reloading. The container stack exposes port 18080; databases,
backend, frontend, Redis, and stats listen only on the internal Docker network.

Nginx serves the reviewed CypherTroopers favicon bundle from a read-only mount
at `/assets/favicon/` and `/favicon.ico`, with cache revalidation headers. This
also avoids the upstream favicon generator's unsupported `file://` input path.
Keep the `frontend/assets/favicons` mount when adapting the proxy configuration.

Desktop navigation logos use 40 px when collapsed and 42 px when expanded;
mobile navigation retains 30/32 px. Tab icons use the close-up mascot composition
recorded in `frontend/assets/FAVICON-EDIT.md`. The network information page shares
the same favicon bundle and uses a 48 px desktop logo.

## Operations and reset

Use `docker compose logs --tail=100 backend frontend stats proxy` for diagnostics.
Use `docker compose stop` and `docker compose start` for ordinary maintenance;
persisted volumes survive a stop. A fresh-chain reset deletes the explorer's
indexed data and derived statistics. Reset only the intended Compose project's
explorer, stats and cache volumes when requested; do not delete a chain node's data.
Prepare and verify both new application images before starting the new indexer.

The transaction-page 24-hour statistics and pending-transaction groups are
scheduled every minute. Keep these explicit group schedule overrides: the
upstream 24-hour group's hourly schedule can leave fee counters absent for up
to an hour if its first update encounters an empty database. Stats fees are
already denominated in CLX. Reload an open transaction page to fetch fresh data.

`network-info/maintenance.html` is the public maintenance page. A local
`network-info/maintenance.flag` activates maintenance routing where configured;
the activation flag is intentionally excluded from this source release. Create it
only for an intended maintenance window and remove it after startup checks pass.

After deployment, check `/api/v2/main-page/indexing-status`, `/api/v2/stats`,
`/stats-service/`, the footer, legal/source pages, and the source archive hashes
against image labels. The browser checks in `tests/upgrade-ui.mjs` require
Playwright and Chromium; they distinguish live-data checks from synthetic browser
fixtures and do not create chain transactions. A source release alone does not
prove RPC compatibility, a successful image build, or completed indexing.
