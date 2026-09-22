# Dependency and asset review

Review date: 2026-09-21.

This directory records a bounded technical review, not a legal opinion or a
certificate that all dependencies can be relicensed. Third-party components keep
their own terms. Declared package metadata alone does not establish compatibility.

## Evidence and scope

- `frontend-build-npm.json`: historical inventory from the original
  `colossusx-frontend-deps:2.3.0` cache, image
  `sha256:745f8621d16a69edbf57c66972f06ba069c0d46e85b78c3da0e7dd8033aeceea`.
  It covers 3,825 installed package instances in the main app and five build or
  runtime tools, including nested `node_modules`. It retains detected top-level
  license/notice texts and their SHA-256 hashes.
- `frontend-runtime-npm.json`: historical inventory of 1,376 installed package
  instances in the frontend before the 2026-09-21 remediation. Next.js standalone
  output omits many package legal files, so this is not a substitute for the
  notices retained from the dependency build image.
- `backend-mix-lock.json`: all 180 dependency entries from the exact GPL backend
  commit `ed93c12dc1835ec0e7fb3e4be3504ceb7061610e` (v9.0.2), including optional,
  development and test dependencies. All 175 Hex package declarations were read
  from exact-version tarball `metadata.config` files. Five Git declarations were
  reviewed at their locked commits. This is not an inventory of all deployed
  native libraries or a claim that every locked package is used at runtime.
- `backend-special-license-evidence.json`: pinned license texts and explanations
  for ambiguous declarations. Native-code and Rust/Cargo dependency trees remain
  outside this bounded review.
- `secret-scan.json`: no matches for the three live deployment secret values and
  no private-key PEM headers were found in the tracked/nonignored candidate
  files. The real `.env` and six backup files are ignored. This check does not
  scan all Git history or prove the absence of every possible secret.

`inventory-npm.cjs` reads installed metadata without executing package scripts.
`enrich-backend.py` retrieves exact Hex archive metadata without installing it.
`enrich-npm-notices.py` retrieves missing notices from the exact GitHub commit
recorded by npm. `npm-supplemental-upstream-notices.json` recovered 109 of 195
package/version pairs missing a top-level notice in the historical cache; the
remaining 86 records explicitly state why no notice was recovered. These are
evidence gaps, not automatic findings that their declared OSS licenses are false.
`render-npm-notices.py --supplemental <file>` can include those notices only for
matching versions actually present in the input inventory. It renders collected
license notices; use the inventory of
an actual final build, not the historical inventories, for release notices.

## Validated replacement dependency image

`frontend-release-npm.json` records the completed replacement dependency image
`sha256:35137b69f3a163b370a6a75984943300abad81c8877bd96295d5498b3991e589`.
It contains 3,463 installed package instances. All identified restricted or
unverified wallet/ad/identicon packages are absent. Compared with the original
image, 258 package/version pairs were removed and no new registry package/version
pairs were introduced. The five remaining empty license metadata fields all
have actual MIT or BSD license files. `frontend-release-audit-summary.json`
records remaining notice-recovery gaps. `frontend-release-NOTICES.txt` contains
2,377 collected package/version/notice sets, including applicable supplemental
upstream notices. These results validate the replacement dependency graph, not
a claim that every native dependency or final browser bundle has been audited.

## Frontend remediation performed in the source

The original graph included three packages with the ConsenSys MetaMask SDK
license: `@metamask/sdk`, `@metamask/sdk-install-modal-web`, and
`@metamask/sdk-communication-layer`, all version 0.32.0. Their terms restrict
resulting programs to defined non-commercial uses, including a monthly-user
threshold, and are not an unrestricted OSS grant. The path was
`wagmi@2.14.15 -> @wagmi/connectors@5.7.11 -> @metamask/sdk@0.32.0`.

The release source now selects `file:vendor/wagmi`: the exact MIT-licensed
`wagmi@2.14.15` package with its TypeScript source and compiled hooks retained,
its connector dependency/export/files removed, and a dated modification notice.
The upstream npm archive SHA-512 is recorded in that notice and was verified.
React hooks and the separately MIT-licensed `@wagmi/core` remain.

The source also removes Reown AppKit and its Wagmi adapter, the HypeLab React ad
SDK, and the CloudNouns kit. The latter two had no license declaration or license
file in the exact installed packages; no redistribution grant was established
by the checked upstream locations. Wallet connections are disabled in the
ColossusX release. The lockfile was regenerated and contains none of the removed
package paths. The replacement dependency image and its inventory verify the resulting
installed graph; historical image reports are intentionally not relabeled.
The parent deployment workflow separately validates the application build.

Other empty npm license fields were not automatically treated as proprietary:
`@pandacss/is-valid-prop`, `cli-table`, `process`, and `tiny-parse-argv` carry MIT
license files; `ansi-color` carries a BSD-style license. The old MetaMask JSON-RPC
provider lacked a root license file; it was in the removed wallet dependency
path. SPDX alternatives and multiple licenses require interpreting their actual
texts, not replacing them with a single project-wide license.

## Fonts and artwork

The bundled `public/static/fonts/Inter-fallback.sfd` identifies the Inter font
as version `4.001;git-9221beed3`, copyright 2016 The Inter Project Authors. Its
exact upstream OFL-1.1 text is retained in `Inter-OFL.txt`; include it with the
fallback font in source and served assets. The checked notice has no reserved
font-name declaration. `Poppins-OFL.txt` covers the default Poppins family loaded
through Google Fonts. `font-license-sources.json` records where these notices
were retrieved; a live external Google Fonts response is not byte-pinned by this
review.

The operator-provided CypherTrooper artwork has a repository/commit/hash
manifest. That provenance does not itself establish a copyright license for
unrelated recipients or trademark rights. It must keep its separately stated
artwork terms; it must not be silently described as GPL-covered third-party art.

## Backend findings and distribution boundaries

A GPL source checkout that contains references to dependencies is different
from a bundled distribution of those dependencies. This audit does not vendor
the locked dependency implementations into the public backend source. The
following upstream questions therefore remain relevant to binary builds and
combined works, rather than being silently declared solved by choosing GPLv3:

- `bcrypt_elixir@3.3.2` includes a four-clause BSD notice for Niels Provos's
  Blowfish implementation in its exact package LICENSE. A published permission
  from Niels Provos to remove the advertising clause is linked by the
  [upstream bcrypt change](https://github.com/pyca/bcrypt/pull/170).
  The published email record is preserved as
  `Blowfish-cypher-license-change.pdf`. Verify applicability to the copied files
  and retain the appropriate notices when preparing a combined binary release;
  this review does not silently rewrite that dependency's license.
- `quantile_estimator@0.2.1` declares `N/A` and its exact package contains no
  license grant in a license file, README, or inspected Erlang source headers.
  Later versions have an [MIT license](https://quantile-estimator.hexdocs.pm/license.html).
  Establish the grant for the exact selected source or select and validate a
  properly licensed release before redistributing its implementation.
- The pinned `prometheus_ex` fork declares MIT in `mix.exs`, but no license-text
  file was found in the pinned repository tree. Preserve the declaration and
  establish the required upstream copyright/permission notice before bundling.
- `metrics@1.0.1` declares only `BSD`; its exact LICENSE is the three-clause BSD
  text. `siwe` provides separate MIT and Apache license files; the MIT option was
  read at the exact pinned commit.

No complete OS/container, native-library, Cargo, browser-bundle reachability,
trademark, security, or patent audit was performed. In particular, packages
containing LGPL/Mozilla/OFL/Creative Commons components retain their own
attribution or source obligations. Publishing only the operator's source and
build instructions does not license unrelated upstream images or imply that
all future combinations are covered by a single license.

## Backend 10.2.6 / Frontend 2.7.2 upgrade

The preceding inventories describe the historical 9.0.2/2.3.0 deployment.
The current backend review is in
`../../release/patches/backend-dependency-review.json`; it covers all 188 locked
entries and verifies the exact archives for new or updated Hex packages.
`quantile_estimator` is absent and `prometheus_ex` is now the Hex 5.1.0 release
with its MIT notice. The upgrade builds the prepared backend source directly.

The new frontend vendors MIT wagmi 2.19.5 hooks, removes its connectors and
optional Dynamic, Reown, Specify and Multisender integrations, and retains the
upstream 2.7.2 versions of all other retained registry packages. Its lockfile has
630 fewer unique package/version pairs than the unmodified 2.7.2 baseline, with
no added or upgraded registry pairs. Wallet signing and accounts remain disabled.
The final build inventory and corresponding notice collection are versioned
separately below when the image build completes. Native/OS binary audit limits
continue to apply; source publication does not relicense third-party components.

### Verified frontend 2.7.2 dependency image

The completed `colossusx-frontend-deps:2.7.2` image is identified by
`sha256:e233637a88f45690a2cc195e45687fb85292232843bc419f6ee271ddaee8eb54`.
`frontend-2.7.2-build-npm.json` inventories 3,993 installed package instances
across the main application and all seven helper tools (2,514 unique
package/version pairs). `frontend-2.7.2-build-audit-summary.json` records the
per-tool counts, image identity, inventory and notice hashes, and remaining gaps.
The main application's 3,535 package paths, versions, declared licenses and
notice-file hashes match the independently validated development workspace.

The excluded Dynamic, Reown, MetaMask SDK, Specify, Multisender and wagmi
connector packages are absent. No restrictive declared license was detected by
the documented metadata review. All four empty license declarations have actual
license files: `ansi-color@0.2.1` has BSD-3-Clause; `cli-table@0.3.11`,
`process@0.10.1` and `tiny-parse-argv@2.4.0` have MIT notices.

The rendered collection contains 2,514 package/version/notice sets and includes
88 exact-version supplemental upstream notices. There are 92 remaining
package/version pairs without a collected standalone notice; their names and
versions remain listed in the summary. These are evidence gaps, not a finding
that their declared OSS grants are invalid. The renderer used the actual build
inventory and the existing supplemental file without transferring notices
between different versions.

GPL, LGPL, MPL and Creative Commons dependencies retain their respective
conditions, including the Nouns packages, libvips, MPL-covered libraries, and
build-time data or dictionaries. This inventory does not audit every native
library, operating-system component, bundled source file or final browser-bundle
reachability, and does not relicense third-party components. The notices were
staged for the deployment workflow; the audit did not alter the live legal page.
