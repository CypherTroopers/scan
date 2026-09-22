# GPL release status

Updated: 2026-09-21. Backend 10.2.6, frontend 2.7.2 and stats 2.15.0 are
deployed. Current build and acceptance evidence is recorded separately from the
earlier 9.0.2/2.3.0 release below. No GitHub push has been performed.

## Current selected sources and distribution scope

| Component | Selected source | License |
| --- | --- | --- |
| Backend | v10.2.6, `90f7dd8e9348123b74dfd23f69ab7da76191a820`, plus reviewed ColossusX changes | GPLv3 |
| Frontend | v2.7.2, `446c409eeb54274aab90ff371a705f9699cd84ef`, plus ColossusX changes | GPLv3 |
| Statistics | stats/v2.15.0, `3fb0afcbed1f6d4443f06d88e2f0a485adaf7659` | MIT |
| Custom mascot images | Supplied ColossusX assets and their size variants | CC0-1.0; no credit required |

The working checkout remains backend 11.3.1 under the separate Blockscout
Software Licence. It has not been relicensed. The upgrade's intended independent
output is `/root/blockscout/public-release/colossusx-10.2.6`; only that finalized
prepared tree is intended for a new public repository. The existing
`/root/blockscout/public-release/colossusx` is the historical 9.0.2/2.3.0 release.
Do not copy the working checkout's Git history or production secrets. The
assembler excludes installed dependencies and container images.

The upgraded backend is built from the prepared GPL source, including its
restricted-fixture exclusions and English edits. It does not use an unmodified
upstream image. Both application images must retain source-archive hashes that
match their published backend/frontend source downloads.

The GPL source route does not rely on a Blockscout commercial agreement. No
agreement has been obtained and the earlier inquiry has not been sent. Third-party
components keep their own terms, including the AGPLv3 option selected for Redis,
the PostgreSQL License, nginx's BSD license, and font OFL notices. The custom
artwork's CC0 terms do not apply to Blockscout names or artwork.

## Initial 10.2.6 upgrade preparation completed

- Pinned the exact GPL backend 10.2.6 and frontend 2.7.2 baselines. Stats 2.15.0
  is selected under MIT for the backend 10.2 database schema.
- Ported the backend's hash-checked Arbitrum metadata and UNLICENSED fixture/test
  exclusions, restored the Ace BSD notice, and reapplied the reviewed English
  edits. No 11.3.1 source files or license headers were copied into that baseline.
- Checked all retained backend SPDX declarations and scanned the prepared source
  for the targeted credential patterns and excluded paths.
- Ran `mix format` on the four changed Elixir files with the exact pinned Elixir
  1.19.4 toolchain. All four files remained unchanged. Dependency-related config
  warnings during this isolated formatting check were not compilation results.
- Added a backend Dockerfile with a pinned Elixir base, bounded compiler
  concurrency, and source/version/license labels. The source archive was verified
  against all 3,311 files in its canonical build directory.
- Updated independent-release templates and build instructions for both custom
  application images. Included the maintenance page and upgrade browser tests;
  excluded and explicitly rejected the maintenance activation flag.

The initial upgrade backend archive was
`colossusx-backend-10.2.6-4628d1a0c33d6771.tar.gz`, SHA-256
`4628d1a0c33d67711d2fbefb534e720e84bba83ac6b2b2edfc1a3f0ce4015ee5`.
Its canonical build source is
`deploy/colossusx/.build/backend.UFDgh4/backend`. Its full dependency, application
and release build completed successfully. The frontend production build also
completed, including lint/type checks, static pages, traces and all seven helper
tools. Artifacts are recorded below.

The [current backend dependency report](../release/patches/backend-dependency-review.json)
records 188 lockfile entries: nine additions, one removal, and 54 version/source
type changes from 9.0.2. All 63 new or changed Hex archives passed their outer
SHA-256 checks against `mix.lock`. The nine additions declare MIT or Apache-2.0.
The old `quantile_estimator` entry is removed, and the old `prometheus_ex` Git fork
is replaced by Hex 5.1.0 with an MIT notice in the exact archive. Those historical
findings must not be presented as unresolved dependencies of the current version.

## Current deployed artifacts and completed checks

| Artifact | SHA-256 |
| --- | --- |
| Backend image `colossusx-backend:10.2.6` | `9f677ae4c109168e27d95cc85b99576aeb1094b5ce7bb522fdf8310d24a84046` |
| Backend source archive | `f6014b26b4560bae700c996192741a443f67ca67a468a4910dd15c1cb242c4da` |
| Frontend image `colossusx-frontend:2.7.2-branding` | `30f8e10bd8cdea5767c1ba33e38216e660fe68b18b794c6d6cad95846c606549` |
| Frontend source archive | `23a2b957cc443bd2a31ce2243895d6a95bd8dbed1bfd30f94e6ecee7e8d2264d` |
| Stats 2.15.0 image digest | `d5a1ba8fbd10365b37cb056a395f8298b0a93802a4d84037bea07e3847b43a0a` |

The backend archive is `colossusx-backend-10.2.6-f6014b26b4560bae.tar.gz` and
the frontend archive is `colossusx-frontend-2.7.2-23a2b957cc443bd2.tar.gz`.
Downloaded backend and frontend archives match the corresponding image source
labels. Both image version labels and the visible footer identify the new
ColossusX versions. Public `/source/` and `/legal/` pages were updated together.

The frontend passed TypeScript, ESLint on the 69 changed source files, and all
12 UTC daily-statistics Vitest tests, in addition to the complete production
build. Its exact dependency image was inventoried: 3,993 package instances and
2,514 distinct name/version pairs across the app and seven helper tools. The app's
3,535 instances match the validated working tree. Relative to upstream 2.7.2,
630 package/version pairs were removed, none added or upgraded, and 2,938 retained
lockfile selectors stayed unchanged. Optional Dynamic, Reown, Specify and
Multisender SDKs were removed; vendored MIT Wagmi hooks do not enable connectors.
Four absent license declarations were resolved from included MIT/BSD texts.
Public notices include 2,514 package notice sets and 88 exact-version supplements.
The audit explicitly records 92 remaining standalone-notice gaps and does not
claim a complete native, bundled-code or OS-package review. See
[the current inventory summary](dependencies/frontend-2.7.2-build-audit-summary.json).

The independent `public-release/colossusx-10.2.6` tree contains 8,158 files,
including 8,157 checksum entries. Its 3,325 backend files and 4,734 frontend files
match their canonical build sources byte for byte, including executable bits.
Targeted scans found no production secret values (raw, URL-encoded or base64),
private generated paths, maintenance activation flag or personal artwork
copyright/permission record. The final deployment configuration disables
unsupported Ethereum Beacon fetchers and bounds indexer memory to 2 GiB.

Private explorer and statistics database backups were taken and their dump
catalogues validated before the reset. After both replacement images completed,
the four `colossusx` explorer database, statistics database, Redis and backend DETS
volumes were removed and recreated. The new frontend and backend first started
with indexing disabled (`APPLICATION_MODE=api`); the backend version, frontend
HTTP 200 and empty block table were verified. Backend mode was then changed to
`all`, and stats 2.15.0 started against its fresh `stats_v2150` database.

Browser acceptance passed in desktop/mobile and light/dark configurations. It
checked API-first totals, UTC daily values even in Asia/Tokyo, 30-second automatic
refresh, the approved mascot without CSS inversion, Blockscout attribution and
versions, Donate/GitHub, legal/source navigation, and absence of advertising,
horizontal overflow and JavaScript errors. Six Hot contracts intervals and an
actual filter click passed against the live API. That chain currently has no
matching contracts or logs, so populated rankings, real contract search markers
and event-log timestamps were explicitly skipped; separate empty-state and new
contract-flag fixture checks passed without creating on-chain data. The report
contains four display profiles and 13 checks.

Both container and host `nginx -t` checks passed. At 08:52 UTC, independent
Globalping probes in Helsinki and Los Angeles confirmed port 18080 returns the
expected HTTPS redirect (308), and the public HTTPS homepage returns 200 with an
authorized TLS certificate. Measurement IDs are
`27nnas7w9LXRBQ1uM00021Avc` and `2ArOIMw1GzKRMvVzM00021Avc`.

The maintenance flag was removed after startup validation. The task's isolated
builder and dependency-only audit image were removed after acceptance, leaving
about 41 GiB free on the 96 GiB filesystem. Production images, backups and matching
sources are retained. The earlier OOM incident below predates this upgrade.

At 09:04 UTC, the final independent chain check passed all 15 assertions. RPC,
database and API agreed on 1,100 canonical blocks (0 through 1099), 506
transactions, and zero transactions for the current UTC day. Both indexing
ratios were 1.00 with `finished_indexing: true`, and pending operations were zero.
The earlier complete RPC snapshot through 1078 was extended through 1099 with
every parent link and block hash checked. All seven services were running with
zero OOM events or automatic restarts; backend mode was `all` and there were no
Beacon errors after its configuration change. Evidence is recorded in
`.colossusx-build/upgrade-10.2.6/final-runtime-verification.json`.

A post-upgrade user report identified the default Blockscout browser tab icon.
The upstream favicon generator rejects the deployment's `file://` logo URL and
had left the default bundle. Nginx now serves the approved CypherTroopers bundle
from a read-only mount for all six linked icon sizes and `/favicon.ico`.
Revalidation headers and disabled time-only 304 responses prevent the older
approved assets' timestamps from retaining the newer default icon in a cache.
This deployment fix preserves both application source archives and image hashes.
Browser acceptance now verifies each favicon response against the approved
asset hash. The repeated four-profile browser run passed with all seven favicon
responses per profile (28 checks), no JavaScript errors, and all 13 other checks.
The proxy configuration and test are included in the independent source release. Browser, external-reachability and source-equality evidence is
in `.colossusx-build/upgrade-10.2.6/`.

## Transaction fee counter recovery, 2026-09-21

The transaction page displayed `NaN CLX (24h)` because the first
`TxnsStats24hGroup` update ran at 08:42:26 UTC against an empty explorer database
and failed to decode its null minimum block. The three enabled 24-hour counters
remained unpopulated until the bundled hourly schedule's next run at 09:30.
The frontend converted the absent fee value to `NaN`; transaction data and actual
on-chain fee amounts were not lost.

The deployment now explicitly schedules `TXNS_STATS_24H_GROUP` and
`PENDING_TXNS_30M_GROUP` every minute. Only the stats container was recreated;
existing databases and application images were retained. The forced startup
update succeeded at 09:28:06 UTC, followed by a scheduled update at 09:30:00 UTC.
The public API then returned a finite fee total of 8.151286192 CLX, 51,331
transactions in its 24-hour window, and a finite average fee. These are a timed
snapshot; ongoing activity changes them. Stats fee amounts are already in CLX,
while the separate backend transaction statistics API reports wei and retains
its own cache settings. An open transaction page needs reloading to request new
data; this change does not add browser polling to that page.

Evidence is in `.colossusx-build/transaction-fees-2026-09-21/`. The targeted
browser check `tests/transaction-fees-ui.mjs` covers desktop/mobile values from
the actual consumed API response and separately checks a zero-activity fixture.
All three checks passed at 09:34 UTC: desktop and mobile both displayed
8.18 CLX from the 8.179132192 CLX API value, the isolated zero-activity fixture
displayed 0 CLX, and there were no browser JavaScript errors. The scheduled
counter timestamp advanced to 09:34:00 UTC without another manual restart.
Deployment settings, the test, and updated instructions are included in the
independent GPL release; application source archive hashes remain unchanged.

## Desktop logo refresh, 2026-09-21

The frontend was rebuilt and deployed at 10:32 UTC with 40 px collapsed and
42 px expanded desktop navigation logos, larger desktop chart watermarks and
a 48 px desktop network-information logo. Mobile navigation retains 30/32 px,
and mobile chart sizes are unchanged. Browser favicons use a close-up mascot
composition recorded in `frontend/assets/FAVICON-EDIT.md`. A narrow desktop
homepage now keeps its transaction panel within the available column width.
Original Blockscout footer attribution and its wordmark are unchanged.

The complete production build passed type checking, linting, page generation,
tracing and helper builds. It emitted the existing `es-toolkit` Edge Runtime
warning. Dependency manifests, lockfiles and vendored dependency files are
unchanged from the previously inventoried build. The current image/source
identities are in the artifact table above; the previous image is retained as
`colossusx-frontend:before-logo-20260921`.

Browser acceptance completed at 10:41 UTC: 60 page cases across 12 viewport,
theme and sidebar profiles, four mobile menus, four live chart cases, and 372
favicon responses passed. It measured the requested logo sizes and checked
image hashes, clipping, footer identity and JavaScript errors (zero). Home and
network information pages had no horizontal overflow. Existing wide tables on
other 1024 px pages were checked for non-increasing overflow rather than claimed
to be fully repaired by this branding change.

Public HTTPS requests returned 200 for the homepage, favicon and source routes.
The downloaded frontend source hash matches the deployed image label. The
independent release has 8,133 files and 8,132 verified checksum entries; its
4,729 frontend and 3,311 backend files match the canonical sources, including
executable bits. Targeted production-secret scans found no matches. Its
`SHA256SUMS` hash is
`2216da53c71dda4fb9e78e4e43022dcc212dba981733c296e88dfe973270e7da`.

Only the frontend service was recreated. All seven services are running, both
databases are healthy, and no OOM events or automatic restarts occurred. The
temporary 2 GiB build swap and dependency-only image were removed; the stopped
builder cache is retained for subsequent builds. Approximately 25 GiB remains
free. Private evidence is in `.colossusx-build/logo-refresh/`. No GitHub push was
performed.

## FHS-D native reward support, 2026-09-21

The previous Geth configuration ignored beneficiary fetching and disabled its
reward worker. Blocks therefore had no reward records and the frontend rendered
their empty sums as zero. The selected GPL sources now include the opt-in
ColossusX adapter documented in [backend/REWARDS.md](../backend/REWARDS.md), pinned
to this chain's genesis and the reviewed FHS-D source `64c12623`.

Block production, Common miner PoW and Common RPC payouts are calculated in
integer wei and shown with the actual recipients. The adapter validates key-block
relationships, receipt amounts and chain identity, and rechecks the canonical
header after fetching data. Both indexing paths avoid Ethereum gas additions.
Verified zero blocks are distinct from pending data, which is retried. The
legacy block reward API preserves its production-only field and adds the complete
distribution. The general RPC miner field retains its original semantics.

Historical balance changes independently confirmed block production in block 1,
both 100,000 CLX payouts in block 57, and the 0.0000042 CLX Common RPC payment to
recipient B in block 64; the admission signer received no such payout. Genesis,
empty block 58 and high-transaction blocks 2120/2200 were checked separately.

Forty backend regression tests passed: 17 adapter/RPC tests, six exact-summary
tests, three database/import tests, ten API/schema tests and four supervisor
startup tests. Thirteen frontend reward tests, changed-file ESLint, full
TypeScript checking and both production image builds passed. Changed Elixir
files were formatted with the pinned Elixir 1.19.4 toolchain. Dependency manifests
and lockfiles remain unchanged.

Desktop and mobile browser acceptance passed for blocks 1, 57, 58, 64 and 2120,
their payout links, homepage/list rendering and pending-to-complete polling.
There were no browser JavaScript errors. Public HTTPS checks passed for seven
representative block responses, the legacy block 57 response, the source index
and both complete source downloads. Downloaded hashes match the deployed image
labels in the artifact table. Both ordinary indexing ratios were 1.00.

The independent GPL release was replaced with the verified reward-enabled tree,
preserving the previous output privately. All 8,157 checksum entries passed;
the complete backend/frontend trees match the image build inputs and source
archives, including executable bits. Targeted production-secret scans passed.
Its `SHA256SUMS` hash is
`9ec178d9abbac38a57f5db19dac59b02b91869187ebff7907956d896130bb191`.
The original Blockscout footer and the approved CypherTroopers logos are retained.

Only the application containers were recreated for this change. No database
reset or migration was required. After the final backend recreation, its reward
worker started automatically with the Geth variant, `disabled: false`, one block
per batch and one worker; four workers were used temporarily for historical
backfill. Private evidence is in `.colossusx-build/fhs-d-rewards/`. No GitHub push
was performed.

Final acceptance at 12:34:39 UTC found all 2,600 canonical blocks (0 through
2599) with a verified reward marker and zero missing rewards. There were 1,536
positive production payouts, 152 Common miner payouts and 1,335 aggregated
Common RPC payout rows. No duplicate producer markers, invalid amounts or
unexpected reward categories were found. The latest block hash matched the node
and public API. The worker was restored to its normal one-block/one-worker limits;
both indexing ratios remained 1.00. All seven production services were running,
both databases were healthy, and there were no OOM events or automatic restarts.
Temporary test containers, their network, unused test/intermediate images and the
2 GiB build swap were removed. The stopped builder retains its original CPU limit
and cache. Approximately 24 GiB of disk space remains free.

## Historical release: backend 9.0.2/frontend 2.3.0

The following results describe the earlier completed 2026-09-21 remediation,
not the current upgrade. That release used backend
`ed93c12dc1835ec0e7fb3e4be3504ceb7061610e`, frontend
`e1111ee2f89af699e53f441340f5149ec153f6f3`, and stats 2.9.2 at
`bbf2d71618e39d61edb2ada7ad7ab19cf06ae586`.

The footer restored the original Blockscout wordmark, attribution, description,
copyright and version links while retaining ColossusX branding, GitHub and Donate.
Legal/source links, full GPL text, font notices, CC0 artwork terms and dated
modification records were provided. The MetaMask SDK path, Reown AppKit, HypeLab
and CloudNouns were removed; MIT Wagmi hooks remained and wallet connection was
disabled. That release's dependency inventory contained 3,463 package instances,
with 258 old package/version pairs removed and no new or upgraded registry pairs.
Those inventory numbers do not describe the 2.7.2 build.

The frontend production build and type checks passed. Original archive integrity,
patch application, retained GPL/MIT texts and the replacement dependency graph
were checked. The candidate source archive was regenerated and matched the image
label. Staging and public browser checks passed in four configurations:
desktop/mobile and light/dark. They covered attribution, versions, GitHub, Donate,
legal/source navigation and API responses, with no advertising labels, JavaScript
errors or horizontal overflow. Compose syntax and nginx configuration passed.
The public run also passed seven route/link checks.

The downloaded 40,582,428-byte source archive matched the deployed image's hash.
The API reported 1,064 blocks and 506 transactions; both indexing ratios were
1.00 and indexing was complete. All seven services were running, both PostgreSQL
services were healthy, and temporary staging containers were removed. The four
modified backend files passed syntax parsing with the official 9.0.2 runtime;
the prepared backend was not compiled during that earlier remediation. Its
unmodified upstream runtime was therefore distinct from the prepared source.

Historical artifacts:

- Frontend image: `sha256:e66b2418cd8f251df50cd948bb991bf451c554def454569b8ace7051eb02b685`.
- Frontend source: `colossusx-frontend-2.3.0-dc610241708e02e0.tar.gz`.
- Source SHA-256: `dc610241708e02e0317052eb20bb5a49cff9562ad6f6e282611725ae28a287d6`.
- Independent tree: `/root/blockscout/public-release/colossusx`.

That tree passed all 7,278 file checksums; its 4,100 frontend files matched the
build source byte for byte. Production secrets, private keys, the excluded
restricted fixture and personal artwork copyright/permission records were absent.
Only standard CC0 asset terms were included for the custom mascot. The earlier
deployment updated frontend and proxy only; databases, indexer and stats were not
recreated. This statement does not apply to the newly requested reset/upgrade.

At 06:41:58 UTC on 2026-09-21, memory pressure during that frontend build caused
one backend restart; Docker recorded an OOM event and exit 137. Databases stayed
running and no stored data was deleted. Large browser/build temporary files were
moved from memory-backed `/tmp` to disk, and future build work directories use
`deploy/colossusx/.build/`. After recovery, the API reported 1,058 blocks,
506 transactions, indexing ratios of 1.00 and `finished_indexing: true`.

## Publication locations and remaining scope limits

- Public site: https://colossusx.make-cph-great-again.community/
- Notices: https://colossusx.make-cph-great-again.community/legal/
- Matching source: https://colossusx.make-cph-great-again.community/source/

The current backend dependency report is a bounded metadata/source review.
`ex_eth_bls` 0.1.0 declares MIT but its exact Hex archive has no top-level license
file; upstream notice provenance and Rust/native dependencies need separate
review before binary redistribution. `bcrypt_elixir` 3.3.2 retains the historical
four-clause BSD notice; the [earlier dependency evidence](dependencies/README.md)
retains the author's advertising-clause waiver for the Blowfish code, whose
applicability and notices must be preserved when bundling. Installed dependency
implementations are not included in the prepared source release.

Collected frontend notices and declared license metadata do not certify every
native library, operating-system package, browser bundle, trademark or future
dependency combination. Do not describe all files or images as relicensed under a
single license. A source release and a later binary distribution have different
review scopes.

[REVIEW.md](REVIEW.md), [COMPONENTS.md](COMPONENTS.md), the initial
[source history](SOURCE-PROVENANCE.md), and the original
[dependency evidence](dependencies/README.md) preserve earlier findings. Claims
there about missing attribution, the 9.0.2 dependency graph, or an unmodified
backend runtime describe their recorded historical state. This document separates
that history from the current upgrade's selected artifacts and actual checks.
