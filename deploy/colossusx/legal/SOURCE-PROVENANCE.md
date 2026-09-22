# Source provenance and publication audit

Audit date: 2026-09-21. Repository: `/root/blockscout`.

This report records local Git and file evidence. No checkout, application version, license text, running service, database, or repository file was changed during this audit. Environment-file values, backups, credentials, and certificate material were not inspected. Component licenses for the deployed frontend, stats service, infrastructure images, and artwork are covered by the separate component audit.

The user has stated that they want both commercially usable open-source publication and a separately negotiated Blockscout commercial license, and that they have not obtained such an agreement or permission. No additional agreement is assumed here.

## Findings

The current backend source tree and the deployed backend are different versions with different upstream license records. The checked-out source identifies itself as 11.3.1 and carries the Blockscout Software Licence. Deployment configuration references the pinned backend image documented as 9.0.2; the corresponding upstream 9.0.2 source explicitly declares GPL v3.0.

The three local tracked edits can be isolated from the newer source tree. Their original target text exists unchanged in upstream v9.0.2. Reapplying those small edits to files obtained from that old GPL-tagged source is technically straightforward and does not require copying complete 11.3.1 files or their newer headers. No such port or replacement checkout was created in this audit.

The deployment directory can also be separated technically from the 11.3.1 backend source: Compose runs pinned images, while the frontend build downloads its own v2.3.0 source archive. This makes a standalone publication bundle a practical candidate, subject to identifying the origins and publication terms of its individual scripts, copied build files, patch, assets, and configuration examples. Being untracked in Git does not establish authorship or permission.

## Repository identity and license history

| Item | Verified value |
| --- | --- |
| Current HEAD | `b7671f6cef934eb6940c20bc8c0be336fee45f9c` |
| HEAD date | `2026-09-17T18:07:22+03:00` |
| HEAD subject | `fix: increase beacon RPC client response timeout to 30s (#14840)` |
| Fetch and push remote | `https://github.com/blockscout/blockscout.git` |
| Shallow clone | No; local history is available |
| Current version and Elixir requirement | `11.3.1`, `~> 1.19`, in `mix.exs` |
| Current license identifier | `LicenseRef-Blockscout` |
| Current license effective date | `2026-04-22`, version `1.0` |
| Upstream v9.0.2 commit | `ed93c12dc1835ec0e7fb3e4be3504ceb7061610e` |
| v9.0.2 commit date | `2025-08-14T14:44:29+03:00` |
| v9.0.2 version and Elixir requirement | `9.0.2`, `~> 1.17` |

Remote output was sanitized before inspection; no credentials were present in the displayed URL.

The relevant history is:

1. `0b0ae2ca392dffc3d18f502404cb04a01c6f5a17`, 2018-02-15: added the GPL3 license.
2. `ed93c12dc1835ec0e7fb3e4be3504ceb7061610e`, tag `v9.0.2`, 2025-08-14: root `LICENSE` contains GNU GPL version 3. `README.md:49-51` explicitly describes the project as GPL v3.0; the two application package manifests say `GPL-3.0`, and their Mix package metadata says `GPL 3.0`.
3. `1a6d9c3b953ce41473676366c5b381c188d04dec`, 2026-04-22, PR #14201: replaced the license and updated eight other files, including README and package metadata. The commit changes nine files, with 142 insertions and 683 deletions.
4. `8c563561a3d8e66f9715c06274a4697235a96023`, 2026-05-12, PR #14359: reformatted the main license document to remove horizontal scrolling.
5. `34f4dcf895b17ba230a5357add0ef84bf6c78474`, 2026-05-12, PR #14360: added SPDX attribution across 2,425 files.

The parent of the license-transition commit is `c196b3707ca788ef86df6a2b94c20511d4ca83e8`; its `mix.exs` already says `11.0.0`. However, the actual `v11.0.0` tag contains the transition commit. A version string alone therefore does not prove the applicable historical license; a precise commit or tag and its license record are necessary. The current HEAD has 938 commits reachable beyond v9.0.2.

Pinned upstream references corresponding to the locally inspected Git objects:

- [Current source LICENSE](https://github.com/blockscout/blockscout/blob/b7671f6cef934eb6940c20bc8c0be336fee45f9c/LICENSE)
- [v9.0.2 source LICENSE](https://github.com/blockscout/blockscout/blob/ed93c12dc1835ec0e7fb3e4be3504ceb7061610e/LICENSE)
- [v9.0.2 README declaration](https://github.com/blockscout/blockscout/blob/ed93c12dc1835ec0e7fb3e4be3504ceb7061610e/README.md#L49-L51)
- [License transition commit](https://github.com/blockscout/blockscout/commit/1a6d9c3b953ce41473676366c5b381c188d04dec)
- [SPDX-header commit](https://github.com/blockscout/blockscout/commit/34f4dcf895b17ba230a5357add0ef84bf6c78474)

## Reach of the current SPDX headers

There are 3,480 tracked files. The content scan excluded seven tracked environment files. The actual declaration is `SPDX-License-Identifier: LicenseRef-Blockscout`, rather than the shorthand `SPDX-LicenseRef-Blockscout`.

That identifier appears in 2,481 Elixir source, test, or configuration files, plus root `LICENSE`, for 2,482 files total. The source split is 1,458 `.ex` files and 1,023 `.exs` files; each source declaration is a leading comment within the first 20 lines.

| Source location | Files |
| --- | ---: |
| `apps/explorer` | 1,303 |
| `apps/block_scout_web` | 687 |
| `apps/indexer` | 321 |
| `apps/ethereum_jsonrpc` | 140 |
| `apps/utils` | 11 |
| `apps/nft_media_handler` | 8 |
| `config` | 9 |
| Root `mix.exs` | 1 |
| `rel` | 1 |

Representative files are `apps/explorer/lib/explorer/application.ex:1`, `apps/indexer/lib/indexer/application.ex:1`, and `config/runtime.exs:1`.

Other identifiers occur in Solidity fixtures, embedded contract source, or JSON data: MIT in 12 files, GPL-3.0 in four, and Apache-2.0, BUSL-1.1, CC0-1.0, GPL-2.0-or-later, and UNLICENSED in one each. Counts overlap. There are 2,497 distinct tracked files containing an SPDX marker. For example, `config/assets/precompiles-arbitrum.json` contains Apache-2.0 and BUSL-1.1 identifiers; `factory.ex` has embedded contract licenses in addition to its own leading Blockscout header. These are not alternative licenses for the entire repository. SPDX counting is not a complete third-party license inventory.

## Why changing only the root LICENSE is not a publication solution

The current document records a different grant from historical GPL v3.0. Its relevant provisions include:

- Section 2(a) reserves rights not expressly granted and describes a non-sublicensable grant.
- Sections 2(b)-(c) require preservation of notices and interface attribution.
- Section 3(a) limits this license to the distributed version and expressly excludes Prior Software.
- Sections 4(a)-(b) restrict specified commercial or monetized uses and require a written commercial agreement for additional permissions.
- Sections 5(a)-(b) limit derivative works to internal use and condition third-party distribution on a commercial license.
- Section 7 addresses ownership and component-specific third-party licenses; section 12(f) addresses the effect of a separate commercial agreement.

These provisions are recorded in the checked-out `LICENSE`, not introduced by this audit. The user reports no commercial agreement. Replacing the file with GPL, MIT, or a newly written commercial license would not remove later upstream code, reconcile the thousands of existing headers, or supply missing permission for that code. The three local edits are not a license grant for the upstream repository.

Conversely, the present headers do not by themselves establish that the previously released GPL version lost its historical permissions. Section 3(a) itself distinguishes Prior Software. A publication based on the old GPL source should retain that source's own upstream license record and evaluate any added material by provenance, rather than relabeling the current mixed-history tree.

## Local tracked changes and a prospective GPL-base port

`git status --short` shows exactly three modified tracked files, no staged changes, and the untracked `deploy/` directory. The tracked diff is five insertions and six deletions. No license file or SPDX header has been edited.

| File | Local change | Evidence at v9.0.2 |
| --- | --- | --- |
| `apps/block_scout_web/lib/block_scout_web/graphql/schema/scalars.ex` | Use the English link label `Wei Dai` | Original edited line exactly matches the pre-edit HEAD line |
| `apps/explorer/lib/explorer/chain/wei.ex` | Same link-label adjustment | Original edited line exactly matches the pre-edit HEAD line |
| `apps/explorer/test/explorer/token/metadata_retriever_test.exs` | Replace a Japanese Unicode fixture with English text plus an emoji, update ABI bytes, and describe the limit as 255 bytes | Entire original test block exactly matches between v9.0.2 and pre-edit HEAD |

The new fixture expects `String.duplicate("Token 🚀 ", 23)`: 253 UTF-8 bytes and 184 graphemes. Its decoded ABI input appends `🚀 metadata`, producing 266 bytes and 194 graphemes. Independent validation confirmed ABI round-trip and the current truncation implementation's expected output. The local diff contains no SPDX-header changes.

A future approved port can therefore start from the exact GPL-tagged source and reapply these three edits to the existing old-version text. The current complete files should not be used as replacements because they also contain other upstream history and current headers. This audit verified the matching source snippets; it did not run a v9.0.2 project build or create a replacement checkout.

## Separating a deployment publication bundle

There are no currently tracked files under `deploy/`. At the initial inventory, before the separate review added the two `legal/` documents, the ColossusX directory contained 39 untracked, non-ignored files:

| Group | Count | Publication review scope |
| --- | ---: | --- |
| Deployment root | 7 | Compose files, proxy config, README, ignore rules, and two environment files |
| `frontend` | 21 | Two Dockerfiles, build script, source patch, and 17 asset/provenance files |
| `host-nginx` | 3 | Bootstrap/virtual-host config and renewal script |
| `network-info` | 7 | Application assets and three images |
| `tests` | 1 | Admission behavior test |

Another seven files are ignored: the deployment `.env` and six backup files. Their contents were not read. `backend.env` and `frontend.env` appear in the non-ignored filename inventory, so a future public bundle needs deliberate example configuration instead of treating the whole directory as already ready to publish.

Technical separation is directly supported by these files:

- `deploy/colossusx/compose.yml:42` references backend image digest `sha256:7659f168e4e2f6b73dd559ae5278fe96ba67bc2905ea01b57a814c68adf5a9dc`. The Compose files have image references and no backend build context referencing this 11.3.1 source tree. The README identifies the pinned backend as 9.0.2.
- `frontend/build.sh:8-15` downloads upstream frontend tag v2.3.0 and verifies archive SHA-256 `d7647463634e2f54ac481f23e0a37d51ef61bb5eddb320b53f10975807948391`.
- `frontend/build.sh:22-29` applies the local frontend patch and builds that extracted frontend. It does not compile the checked-out backend source.
- `frontend/branding.patch` touches 58 frontend files and changes no path named LICENSE, COPYING, or NOTICE. It is a patch against the independently fetched frontend version, not against backend 11.3.1.

These facts support reviewing a standalone orchestration-and-patch bundle without including the current backend source tree. They do not establish a single license covering the bundle. Session-created orchestration or network-info code, copied frontend Dockerfiles, the frontend patch, logo images, and third-party test data need separate provenance and notice decisions. A license chosen for original deployment code cannot automatically relicense copied frontend code, upstream images, or artwork. The separate component audit is needed before claiming the entire public package is commercially usable open source.

No publication, license replacement, service migration, database action, commit, or push was performed.

## Reproduction commands

The principal read-only checks were `git status --short`, `git rev-parse HEAD`, `git log --follow -- LICENSE`, `git show <commit>:LICENSE`, `git show v9.0.2:<path>`, `git log -S 'SPDX-License-Identifier: LicenseRef-Blockscout' -- mix.exs`, and a tracked-file SPDX scan excluding environment-file contents. Original target snippets were compared as exact strings between `git show v9.0.2:<path>` and `git show HEAD:<path>`. Deployment environment values and backups were excluded from inspection.
