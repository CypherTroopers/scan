# ColossusX modification record

Prepared on 2026-09-21. Upstream copyright and license notices are retained.

## Backend v10.2.6

The files in `backend/` originate from upstream commit `90f7dd8e9348123b74dfd23f69ab7da76191a820`, then receive the changes recorded in `backend/LICENSE-PREPARATION.md`: remove the restricted Arbitrum precompile metadata; omit the UNLICENSED issue_4758 contract fixture and its single test, including embedded bytecode; restore the BSD 3-Clause notice for the vendored Ace 1.4.14 code. The selected deployment builds its backend from this modified source. The custom Dockerfile pins the Elixir build base, limits compiler concurrency, and records GPL, version, upstream revision and corresponding-source hash labels.

`patches/backend-english.patch` is applied to the known GPL baseline by the assembler. These edits were prepared on 2026-09-21: two Wei Dai link labels use English, and one Japanese Unicode test fixture is replaced with English text and an emoji while preserving the UTF-8 byte-length test and its encoded ABI input. The three modified files carry dated notices, and `SOURCE-PROVENANCE.json` records their before/after hashes. No complete files or later backend license headers are copied from 11.3.1. Four changed Elixir files passed formatting with the exact Elixir 1.19.4 toolchain; full backend image compilation and runtime acceptance are separate checks.

The 2026-09-21 FHS-D reward patch adds a genesis-pinned protocol adapter, exact
block-production/Common miner/Common RPC payouts, historical reward backfill,
canonical-data validation, and API reward status and distribution fields. It
preserves verified zero blocks and retries incomplete data. Both import paths
bypass Ethereum gas additions. Parser/RPC, persistence, API and schema regression
tests accompany the patch. See `backend/COLOSSUSX_REWARDS.md` and
`patches/backend-colossusx-rewards.json` for the rules and per-file hashes.

## Frontend v2.7.2

ColossusX modifications made on 2026-09-20 and 2026-09-21 include product branding and artwork, removal of advertising integrations from the visible interface, custom donation and GitHub links, corrected homepage statistics and daily UTC transaction calculations, and restoration of Blockscout attribution and legal/source links. These modifications are ported to frontend v2.7.2 for the selected backend's APIs. The full source, tests, and build materials are included.

The 2026-09-21 logo refresh enlarges desktop navigation and chart branding while preserving mobile logo dimensions. Browser favicons use a close-up mascot composition. The homepage transaction panel scrolls within narrow desktop layouts, and the shared main column can shrink to the available width. The original Blockscout footer attribution is retained.

The FHS-D reward integration adds exact totals, category amounts, recipient links,
and pending-state refresh to block details, homepage cards, block lists and address
validated-block lists. It does not use Ethereum fee arithmetic for these rewards.

The generated `SOURCE-PROVENANCE.json` lists every changed, added, and removed frontend file, with original and resulting SHA-256 hashes. It compares this source with the verified upstream archive whose SHA-256 is `34f4758f639f029bfe91d47584e3dcdbd5033d72a6b32d0c93904a5e347f081f`. Individual modification notices and upstream notices must be retained when making further changes.

## Deployment and source distribution

The ColossusX deployment configuration, reverse-proxy integration, validators/common-miners information page, maintenance page, tests, resource limits, source archive tooling, and public legal pages were prepared or modified on 2026-09-19 through 2026-09-21. The custom frontend Dockerfiles derive from the GPL frontend v2.7.2 build workflow. Stats v2.15.0 is selected under MIT for the backend 10.2 schema. The maintenance activation flag, private environment, databases and backups are not distributed. Original ColossusX software contributions in this distribution use GPL version 3; third-party and artwork licenses remain separate.

Production secrets, certificate/private-key material, databases, backups, the newer backend working tree, and private licensing correspondence are excluded. Fresh installations must generate their own secrets.
