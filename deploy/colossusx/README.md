# ColossusX Explorer Operations

The public URL is **https://colossusx.make-cph-great-again.community**. The server's public IPv4 address is `213.199.33.3`. Compose runs under the `colossusx` project.

| Item | Setting |
| --- | --- |
| RPC | `https://test2.make-cph-great-again.community` |
| Chain ID | `10101919` |
| Network display name | `ColossusX` |
| Native currency | `colossusX` / `CLX` / 18 decimal places |
| Public ports | TCP `80` / `443` (host Nginx), `18080` (container proxy) |
| Stats API | `/stats-service/` under the public URL |

The request path is Cloudflare → host Nginx (HTTPS) → `127.0.0.1:18080` → container proxy → frontend / backend / stats. The PostgreSQL, Redis, backend, frontend, and stats service ports are not published to the host.

`http://213.199.33.3:18080/` returns a 308 redirect to the public HTTPS domain, preserving the path and query string. Cloudflare does not proxy port 18080, so do not append a port number to the domain. HTTP requests to the domain also redirect to HTTPS.

## Starting, Checking, and Stopping Services

Run the following commands in `/root/blockscout/deploy/colossusx`. Both `compose.yml` and `compose.override.yml` are loaded automatically, applying the HTTPS domain, port 443, and WSS settings. Specifying only `compose.yml` uses the previous IP-based connection settings, so omit `-f` during normal operation.

```bash
cd /root/blockscout/deploy/colossusx
docker compose up -d
docker compose ps
docker compose logs --tail=100 backend frontend stats proxy
```

Use `docker compose logs -f --tail=100 backend stats` to follow logs, `docker compose stop` to stop services, and `docker compose start` to resume them.

Each service uses `restart: unless-stopped` to restart after an unexpected exit or a Docker restart. Services stopped manually remain stopped until explicitly resumed. Docker and host Nginx are enabled to start automatically.

## Host Nginx and HTTPS

Installed versions: Docker `29.1.3`, Compose `2.40.3`, and host Nginx `1.28.3`. The source configuration for host Nginx is `host-nginx/colossusx.conf`, installed at `/etc/nginx/sites-available/colossusx` and enabled through the `/etc/nginx/sites-enabled/colossusx` symlink. The package's default site is disabled.

- `host-nginx/bootstrap.conf`: HTTP configuration for initial certificate issuance. Not used during normal operation.
- `host-nginx/colossusx.conf`: HTTP-to-HTTPS redirects, TLS, WebSocket support, and forwarding to the internal proxy.
- `nginx.conf`: Routing within Docker and the additional information page. Docker DNS is resolved again every 10 seconds to follow changes to upstream IP addresses when containers are recreated.
- `host-nginx/renew-nginx.sh`: Configuration validation and Nginx reload after certificate renewal. Installed at `/etc/letsencrypt/renewal-hooks/deploy/colossusx-nginx`.

The Let’s Encrypt certificate is stored in `/etc/letsencrypt/live/colossusx.make-cph-great-again.community/`. The initially issued certificate expires on **2026-12-19**. `certbot.timer` is enabled, and the renewal dry run and deploy hook have been verified. The certificate was issued without an email address. If changing Cloudflare's SSL settings, Full (strict) can be used because the origin also has a valid certificate.

```bash
nginx -t
systemctl status docker nginx certbot.timer --no-pager
certbot certificates
certbot renew --dry-run --run-deploy-hooks
```

After changing the host configuration, run `install -m 644 host-nginx/colossusx.conf /etc/nginx/sites-available/colossusx`, then apply it with `nginx -t && systemctl reload nginx`. Validate and apply the container configuration with `docker compose exec -T proxy nginx -t && docker compose exec -T proxy nginx -s reload`.

## Images and Resources

The infrastructure service images are pinned by digest in `compose.yml`. Both application services use locally built GPL images with `pull_policy: never`. Build those images before starting a fresh deployment; their tags are not public registry downloads. The main components use the following versions.

| Component | Version | Local image ID or pinned registry digest (SHA-256) |
| --- | --- | --- |
| ColossusX backend | `10.2.6-colossusx` | `9f677ae4c109168e27d95cc85b99576aeb1094b5ce7bb522fdf8310d24a84046` (image ID) |
| ColossusX frontend | `2.7.2-colossusx` | `30f8e10bd8cdea5767c1ba33e38216e660fe68b18b794c6d6cad95846c606549` (image ID) |
| Blockscout stats | `2.15.0` | `d5a1ba8fbd10365b37cb056a395f8298b0a93802a4d84037bea07e3847b43a0a` (registry digest) |

Each container has CPU and memory limits. For this host with 4 CPUs and approximately 7.8 GiB of memory, the combined limits are 4 CPUs and 5.9375 GiB. The backend indexer memory monitor is explicitly set to `INDEXER_MEMORY_LIMIT=2g`, below its 3 GiB container limit. Actual usage varies with workload. Docker logs are limited to 10 MB × 3 files per service. Monitor database disk usage separately.

Ethereum Beacon blob, deposit and deposit-status fetchers are disabled for this network. This prevents attempts to use an unrelated Beacon API at localhost:5052. Reward indexing uses the ColossusX FHS-D adapter instead of Ethereum reward rules.

## Licensing and Public Distribution

The working backend checkout remains 11.3.1 under the separate Blockscout Software Licence. The deployed applications and independent public source release use GPLv3 backend v10.2.6 and frontend v2.7.2, preserving their applicable notices. Stats v2.15.0 is MIT-licensed. Do not publish the working checkout or its history as if it were the GPL release.

Use the independent output at `/root/blockscout/public-release/colossusx-10.2.6`, produced by [the release assembler](release/README.md). The release includes both modified application source trees and their build instructions, documented backend exclusions, and public deployment templates. Production secrets, backups, installed dependencies, container images, and this checkout's Git history are excluded. The archives served at `/source/` cover the exact modified backend and frontend build inputs. The old `public-release/colossusx` output is the historical backend 9.0.2/frontend 2.3.0 release.

Read [the current release status](legal/RELEASE-STATUS.md) for the completed remediation, public validation, and scope limits. [The initial review](legal/REVIEW.md) and [component findings](legal/COMPONENTS.md) describe the state before remediation. Their descriptions of the old footer and pending fixes are historical, not the current implementation specification.

No separate Blockscout commercial agreement has been obtained. The selected GPL release permits commercial use subject to GPL conditions; it does not claim contractual permission for the newer 11.3.1 source. The prepared [commercial licensing inquiry](legal/COMMERCIAL-LICENSE-REQUEST.md) has not been sent. Third-party components retain their own licenses, and the source preparation is not a complete audit of redistributable binaries.

## Frontend Appearance and Rebuilding

`frontend/` contains the source patch, logos, Dockerfiles, and rebuild script. The upstream v2.7.2 source is downloaded and verified against its SHA-256 checksum before applying `branding.patch`. The Node base image is also pinned by digest.

The frontend image tag is `colossusx-frontend:2.7.2-branding`; the backend tag is `colossusx-backend:10.2.6`. After rebuilding, inspect their IDs and labels with:

```bash
docker image inspect colossusx-backend:10.2.6 colossusx-frontend:2.7.2-branding --format '{{.Id}} {{json .Config.Labels}}'
```

The frontend `org.colossusx.source.sha256` label must match its source archive SHA-256, currently `23a2b957cc443bd2a31ce2243895d6a95bd8dbed1bfd30f94e6ecee7e8d2264d`. The backend `community.colossusx.source.sha256` label must match its archive, currently `f6014b26b4560bae700c996192741a443f67ca67a468a4910dd15c1cb242c4da`. Both archives are linked from `/source/`. A tag alone does not identify a build. The pre-upgrade frontend image is retained as `colossusx-frontend:before-10.2.6`; the build immediately before the desktop logo refresh is retained as `colossusx-frontend:before-logo-20260921`. The application images preceding FHS-D reward support are retained under each application's `before-rewards-20260921` tag.

- Banner ads, text ads, and Sponsored sections are disabled.
- Hot contracts is enabled with the v2.7.2 frontend and v10.2.6 API. Displayed rankings depend on indexed contract activity; an empty chain result is not replaced with sample data.
- The GPL footer restores “Made with” and the original Blockscout wordmark, the upstream description, backend/frontend versions, and Blockscout Limited copyright. It adds Legal notices (`/legal/`) and Source code (`/source/`). GitHub remains `https://github.com/CypherTroopers`; Donate links to the address details for `0x7d7cC2AbEB8256d11E9Ec63C13782E77300c7e30` on this chain.
- Desktop navigation uses 40 px collapsed and 42 px expanded mascot logos; mobile retains 30/32 px. Desktop chart watermarks and the 48 px network-information logo are enlarged. Favicons use a close-up composition; its prompt and provenance are recorded in `frontend/assets/FAVICON-EDIT.md`. The narrow homepage transaction panel scrolls within the available column width.
- The display name, logo, favicon, and social sharing image use ColossusX branding. The logo uses the specified original CYPHERTROOPER mascot with a chest label and white background, not the circular Wrapped CPH logo. The source is `CypherTroopers/logo` at commit `45563d754dc544d4d05d29d5a588adec97637520`. File URLs and SHA-256 checksums are recorded in `frontend/assets/sources.json`.
- Header assets use the 128px and 64px versions at the responsive display sizes above. Favicons use the approved close-up variants at 16, 32, 48, 180 and 192px; sharing cards retain the original 512px version. The upstream license is also retained in the runtime image.
- The custom mascot images use CC0-1.0 without a credit requirement. Upstream Blockscout artwork is separate and retains its notices.
- Nginx serves the approved favicon bundle at `/assets/favicon/` and `/favicon.ico` from a read-only mount, with cache revalidation headers. The upstream frontend generator cannot read `file://` logo URLs and otherwise leaves the default Blockscout icons. Browser acceptance checks all six linked icon sizes and the root ICO against the approved asset hashes.
- Wallet connection, optional ad SDKs, and the CloudNouns integration are removed from the release dependency graph. The MIT-licensed Wagmi hooks remain as reviewed vendor source; read-only contract queries remain available. See [the dependency review](legal/dependencies/README.md).

Rebuild and deploy the frontend:

```bash
cd /root/blockscout/deploy/colossusx
./frontend/build.sh
docker compose config --quiet
docker compose up -d --no-deps frontend proxy
docker compose logs --tail=80 frontend
```

The build uses Docker Buildx, which is installed on this server. It creates a deterministic source archive, checksum, and download page in `source-dist/`, then records the archive hash in the image. Nginx serves this directory at `/source/` and `public-legal/` at `/legal/`, both through read-only mounts. Recreate the proxy when adding or changing these mounts. The first build takes time to download dependencies and compile the application. Recreate the frontend only after the build succeeds. Logo settings and similar entries in `frontend.env` reference files inside the custom image, so this configuration requires that image.

For the backend, follow [backend/SOURCE-README.md](backend/SOURCE-README.md) or the independent release's `deployment/README.md`. Build from the prepared v10.2.6 source, not the working 11.3.1 checkout. Both complete production image builds have passed for this upgrade; runtime acceptance results are recorded separately in [RELEASE-STATUS.md](legal/RELEASE-STATUS.md).

Build work directories use `deploy/colossusx/.build/` on disk. Do not move large frontend builds or browser downloads onto this host's memory-backed `/tmp`; compilation and indexing share the host's memory. The source archive can also be built directly after extraction using its included `build-colossusx.sh`.

During historical frontend v2.3.0 deployment verification on 2026-09-20, the production build and type checks passed. The 7 pages—home, block list, block details, transaction list, address, tokens, and API—were checked on desktop and mobile in light and dark themes, for 28 screens in total. There were no advertising requests, API failures, or JavaScript runtime errors. The then-current two footer links, specified logo, favicons, and sharing image were also verified. This historical check predates the GPL footer changes. Existing upstream behavior that omits OG images on detail pages and certain other pages is preserved.

Those historical checks also covered the watermarks on the statistics overview and individual charts, the mobile menu, and the logo and favicon on the additional information page. That page uses the same original artwork, installed as `network-info/logo.png` and related files.

## Homepage Statistics and Refresh Intervals

- **Total blocks**: The number of indexed blocks on the canonical chain. This includes Genesis (block 0), so it equals the latest height + 1 when no blocks are missing.
- **Total txns**: The total number of transactions stored by the explorer, including successful, failed, and pending transactions.
- **Today's transactions (UTC)**: The number of transactions included in canonical blocks since 00:00 UTC today. The current day's point is taken from the regular `newTxns` daily chart, and the same data is used for the headline and graph. The graph covers 30 days including today. Today's value increases while the day is in progress. Missing data is not treated as a confirmed zero.

Totals prioritize `/api/v2/stats`; the stats service supplies only fields unavailable from that API. The backend's `CACHE_BLOCK_COUNT_PERIOD` and `CACHE_TXS_COUNT_PERIOD` are fixed at `30s`. The browser also refetches the relevant data every 30 seconds and refreshes stale cached data when returning to the tab or revisiting the page.

The stats service uses `STATS_UPDATE_GROUPS__SCHEDULES__` to update `TOTAL_BLOCKS_GROUP`, `TOTAL_TXNS_GROUP`, `TOTAL_ADDRESSES_GROUP`, `NEW_TXNS_GROUP`, `TXNS_STATS_24H_GROUP`, and `PENDING_TXNS_30M_GROUP` every minute. Other aggregates retain their previous schedules. `STATS__DEFAULT_SCHEDULE` alone does not override the bundled schedules for individual groups.

The transaction page reads rolling 24-hour fees, average fees and transaction counts from `/stats-service/api/v1/pages/transactions`. On an empty database the first aggregation can fail; its bundled hourly schedule previously left these counters missing and the UI displayed `NaN CLX`. The one-minute group schedule retries promptly, while `FORCE_UPDATE_ON_START` recalculates at startup. Stats fee values already use CLX; the backend's separate `/api/v2/transactions/stats` values use wei and have their own cache. Reload an already-open transaction page to request fresh data; the homepage refresh settings do not apply to that page. `tests/transaction-fees-ui.mjs` checks actual desktop/mobile fee values against the response consumed by the browser and tests a zero-activity fixture separately.

Previously, totals showed aggregates updated approximately every 2 hours, and Daily transactions showed yesterday's UTC count. In backend v9.0.2, `transactions_today` also returns yesterday's value, so it is not used for today's display. Short delays remain due to indexing, server aggregation, and browser refetch intervals.

The frontend patch includes 12 Vitest tests covering UTC date boundaries, recovery after suspended timers, the 30-day range, counts of 0, and missing values. All 12 passed for the upgrade. Run them in the prepared frontend source with its locked dependencies installed:

```bash
yarn test:vitest run ui/home/indicators/useDailyTransactions.spec.ts ui/home/indicators/utils/dailyTransactions.spec.ts
```

The deployment acceptance script `tests/upgrade-ui.mjs` uses Playwright and Chromium to check the public site in desktop/mobile and light/dark profiles, compare counters to APIs, verify source downloads and branding, and exercise the upgraded contract UI. Synthetic browser fixtures are reported separately from live chain data. See [RELEASE-STATUS.md](legal/RELEASE-STATUS.md) for the completed results; the historical measurements below do not establish acceptance of the new versions.

During historical backend 9.0.2/frontend 2.3.0 verification on 2026-09-20 at 11:36–11:37 UTC, the API, database, and public UI all reported **713 blocks (height 712), 506 total transactions, and 506 transactions for the current UTC day**. The latest block hash matched the RPC, and both block and internal transaction indexing were 100% complete. The display was checked in 4 configurations: desktop/mobile × light/dark. The UTC date range remained unchanged in the Tokyo timezone. Browser refetch intervals on the public site were 30.406 seconds for totals and 31.394 seconds for daily data. There were no JavaScript or API errors, and the logo and GitHub/Donate links matched the expected versions.

## Data and Secrets

Data is stored in the Compose named volumes `db-data`, `stats-db-data`, `redis-data`, and `backend-dets` and is retained during normal stops, restarts, and container recreation. **Do not use `docker compose down -v` for a normal shutdown. It deletes all stored data and must only be used when deletion is explicitly requested as part of a chain reset.**

The stats service uses the `stats_v2150` database. The `stats` database in the same stats PostgreSQL instance is created during initialization and is unused. The deployed backend image was built from the independent GPL v10.2.6 source; the working checkout's 11.3.1 source is not deployed.

For the 10.2.6 upgrade, both new application images were built before resetting the four explorer volumes. The new backend was first started in API-only mode to verify its version against an empty database alongside the new frontend. Indexing was then enabled and stats v2.15.0 started. Verified pre-upgrade PostgreSQL dumps are retained privately in `backups/before-10.2.6/`. Runtime synchronization and public acceptance results are recorded in [RELEASE-STATUS.md](legal/RELEASE-STATUS.md).

`.env` contains the public IP address, database passwords, and `SECRET_KEY_BASE`. This file has permissions `600` and is excluded from version control by `.gitignore`. Keep it confidential and do not display its contents in logs or chats. The configuration from before the server migration is stored in `backups/before-server-move-20260920T073438Z/`; it contains secrets and requires the same protection. `docker compose config` also prints expanded secrets, so do not share its output. Use `docker compose config --quiet` when only checking syntax.

## Manual Backups

Scheduled backups are not configured. The following commands save the 2 active databases in PostgreSQL custom format.

```bash
cd /root/blockscout/deploy/colossusx
umask 077
mkdir -p backups
docker compose exec -T db pg_dump -U blockscout -d blockscout -Fc > "backups/blockscout-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T stats-db pg_dump -U stats -d stats_v2150 -Fc > "backups/stats_v2150-$(date -u +%Y%m%dT%H%M%SZ).dump"
```

`backups/` is excluded from Git. Confirm that each command succeeds, and also keep the backups and `.env` in separate storage with restricted access. These commands do not include the unused `stats` database.

## Historical GPL Release Validation and Build Incident (2026-09-21)

This section describes backend 9.0.2/frontend 2.3.0 before the 10.2.6 upgrade. It is not the current build or acceptance record.

The remediated frontend completed its production build and type checks. Staging browser checks passed for desktop/mobile in light/dark themes, including attribution, links, Donate, legal/source navigation, API responses, and absence of advertising labels or JavaScript errors. The final CC0 source was assembled and deployed. The public HTTPS site passed the same four browser profiles and seven route/link checks. The full source archive downloaded from `/source/` matched the deployed image label. Final artifact hashes and scope limits are recorded in [RELEASE-STATUS.md](legal/RELEASE-STATUS.md).

During compilation at 06:41:58 UTC, host memory pressure caused one automatic backend restart (Docker recorded an OOM event and exit 137). The databases remained running and stored data was not reset. Large temporary assets were moved from memory-backed `/tmp` onto disk, and subsequent build work directories also use disk. After recovery, the API returned 1,058 blocks and 506 transactions, with block and internal-transaction indexing ratios of 1.00 and `finished_indexing: true`.

The four altered Elixir files in the prepared GPL backend passed syntax parsing using the official v9.0.2 runtime. A complete backend dependency build and compilation was not performed. The source package does not bundle those dependencies or the deployed upstream backend image. See the dependency review for exact-version license/notice gaps relevant before redistributing combined binaries.

## FHS-D Reward Indexing

`FETCH_REWARDS_WAY=colossusx` enables the adapter for the configured chain ID and genesis. Block details, lists, homepage cards and address validated-block lists show exact totals. The distribution separates block production, Common miner PoW and Common RPC payments, with links to the actual recipients. Verified empty-block rewards remain zero; missing or inconsistent node data stays pending and is retried. Pending browser results refresh automatically.

The reward worker starts automatically with the Geth variant when `INDEXER_DISABLE_BLOCK_REWARD_FETCHER=false`. Its normal limits are one block per batch and one concurrent worker. Existing blocks without a verified reward row are backfilled without deleting the database. No Ethereum gas fees are added to these native payouts. See [the supported rules and API contract](backend/REWARDS.md), including the distinction between the RPC's general miner field and actual payout recipients.

The change passed 40 backend regression tests, 13 frontend reward tests, frontend lint/type checks and both production builds. Browser acceptance checked five representative blocks in desktop and mobile views, homepage/list rendering and the pending-to-complete refresh. The independent GPL source release includes these changes and tests; detailed deployment and backfill evidence is recorded in [RELEASE-STATUS.md](legal/RELEASE-STATUS.md).

## Current Limitations

- The public site uses HTTPS. Wallet connections are disabled in the GPL frontend source and their connector integrations have been removed. Account features remain disabled.
- Native rewards target the reviewed FHS-D rules at source commit `64c12623`. Future protocol changes require an adapter review; historical backfill requires the node's original block/header/receipt/Key-block data.
- Indexing depends on the configured RPC. RPC outages or compatibility issues can delay updates to the displayed data.

## Validators / Common Miners Information and Transaction Lookup

An information page is available at `https://colossusx.make-cph-great-again.community/network-info/`. Open it from **Other → Validators & Common Miners** in the explorer.

- Explains roles, HotStuff finality, and TxQUIC authentication and local filtering based on the provided network specification.
- Explains Common RPC signer A, a separate recipient B, the 20% reward and burning of the remainder, and the 10 RPC fields.
- Entering a transaction hash makes the browser read from the configured HTTPS RPC and display the signer, recipient, reward, burn, and proof fields. Share a link to the lookup result with `?tx=<hash>`.
- Checks the allocation using integer arithmetic in wei. It does not fall back to A when B is missing, infer payouts for unconfirmed transactions, or treat an entire balance as a reward. Cryptographic verification of signatures and roots is the validators' responsibility; the page checks only the arithmetic of the amounts.

Static files are maintained in `network-info/`, and public routes are configured in `nginx.conf`. This does not change the database or existing transaction API formats and uses no additional ports. Browser lookups require the RPC to allow CORS.

Regression tests for arithmetic, missing values, and mismatches:

```bash
node --test deploy/colossusx/tests/admission.test.mjs
```

Run the test above from the repository root, `/root/blockscout`.

## Historical Deployment Verification (2026-09-20)

- All 7 containers were running, and both PostgreSQL instances were healthy. Docker, Nginx, and certbot.timer were confirmed enabled and active.
- Chromium checks covered the HTTPS home page, block 0, the latest block at the time (2), and the additional information page. The main APIs, stats, and WSS heartbeat succeeded. There were no Mixed Content or JavaScript runtime errors. The daily transaction chart correctly displayed 0.
- Before switching to HTTPS, TCP connections and HTTP 200 responses on the IP's port 18080 were verified from external locations in Germany, Japan, and the United States. The 308 redirect after the switch was also verified. [TCP report](https://check-host.net/check-report/4c6e2cc1k9f2) / [HTTP report](https://check-host.net/check-report/4c6e2f0ek343).
- During setup, the upstream RPC's latest height changed from 789 to 0, then advanced to 2. At the final UI check, the explorer matched the RPC with 3 blocks including Genesis, 0 transactions, and 100% block indexing. The Genesis hash was `0x9db1f5364ca33eb1a6c261f83e6eab2b76e4a65a665fe5d9ba517782acc9d213`.
- The internal transaction indexing ratio was 0.66 at the time because of the small chain and how Genesis is handled. There were no transactions, and the API's `finished_indexing` was true. The previous sample transaction also returned null from the upstream RPC, so a successful transaction details view could not be verified on the chain at that time.
- The above records the initial public deployment. The user subsequently reported that the chain had been rebuilt from scratch, and the stored data was reset as described below. The old-server history that follows does not represent the current chain state.

## Historical Reindexing After the Chain Reset (2026-09-20)

- At the user's explicit request, the ColossusX-specific volumes `colossusx_db-data`, `colossusx_stats-db-data`, `colossusx_redis-data`, and `colossusx_backend-dets` were deleted, and all 7 containers were recreated.
- The new Genesis hash was `0x2d8c7bd7411c3ba344c78cca3499ed6bfb9f5889a1d0ef70a7ae2768c20495c8`. Its match across the RPC, indexed API, and database was verified, along with the absence of the previous Genesis.
- The HTTPS domain, Nginx, certificates, and connection settings were retained. The stats service was also restarted with a new database.

## Historical Chain Reset (2026-09-20 08:13 UTC)

- Following another reset request, the same 4 ColossusX-specific volumes were deleted again, and all 7 containers were recreated.
- The Genesis hash for this reset was `0xe69022ef43f6d238846015e0a4e7cdd190cf45e9fd98cfa0666acb482a05017e`. The absence of the previous 2 Genesis blocks from the new database was verified.
- At verification, there were 63 blocks up to height 62, 0 transactions, and 100% block indexing. The latest block hash matched the RPC, and the stats service was restarted after indexing completed and recalculated the count as 63 blocks.

## Public Deployment Verification on the Previous Server (2026-09-19, Historical)

The public URL at the time was `http://13.140.169.170:18080`.

- The HTTP UI, API, search, and stats responded successfully through the public IP.
- Chromium checks covered the home page, `/block/4`, and an actual transaction details page.
- At verification, 497 blocks from Genesis through block 496 had been indexed, matching the RPC's latest height. Both block and internal transaction indexing were 100% complete.
- Transaction `0xc376f07d78ce2eb9d3e79c4264d8d76d5814196fcaa2b887b2b0fd8d4b51c9ca` in block 4 successfully transferred 2 CLX. The 0.000021 CLX fee, receipt, and simple CALL trace matched the RPC.
- The stats service was aligned to version 2.9.2, resolving database compatibility errors in contract statistics. The currency unit was CLX.
- The existing RPC's Chain ID response was also rechecked. The existing nginx configuration for 80/443 was not changed.

Check indexing status at `/api/v2/main-page/indexing-status` and the overview at `/api/v2/stats`.
