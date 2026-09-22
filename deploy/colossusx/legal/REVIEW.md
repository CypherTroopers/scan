# ColossusX License Review

Review date: 2026-09-21.

**Historical review:** The findings below describe the state before the GPL
release remediation. See [RELEASE-STATUS.md](RELEASE-STATUS.md) for the selected
GPL baselines, restored footer, modified-source packaging, dependency changes,
and current verification status. Statements below about pending work are not a
claim that the later remediation has not occurred.

This document records technical evidence and release issues. It is not a legal opinion, a license grant, or a substitute for a signed agreement. The operator confirmed that no Blockscout commercial agreement or individual permission has been obtained. A qualified licensing lawyer should review the publication and notice requirements before release.

## Scope and Status

The requested outcome is an open-source release that permits commercial use, together with any separate commercial permission needed from Blockscout. These are distinct rights. A commercial contract cannot be created by renaming a license file, and a contract with one supplier does not automatically replace other copyright holders' licenses.

No upstream license has been replaced, no commercial permission is claimed, and this review does not authorize publication of the current checkout. The production application has not been relicensed or rebuilt as part of this review.

Detailed source history and the exact scope of local edits are recorded in [SOURCE-PROVENANCE.md](SOURCE-PROVENANCE.md).

The running stack and frontend-notice evidence are recorded in [COMPONENTS.md](COMPONENTS.md). Its component licenses are not a complete inventory of transitive dependencies.

## Source and Deployment Are Different Versions

| Component | Reviewed version | License evidence |
| --- | --- | --- |
| Current backend source checkout | 11.3.1; commit `b7671f6cef934eb6940c20bc8c0be336fee45f9c` | [Blockscout Software Licence](https://github.com/blockscout/blockscout/blob/b7671f6cef934eb6940c20bc8c0be336fee45f9c/LICENSE), `LicenseRef-Blockscout`, effective 2026-04-22 |
| Deployed backend | v9.0.2; commit `ed93c12dc1835ec0e7fb3e4be3504ceb7061610e` | [GNU GPL version 3](https://github.com/blockscout/blockscout/blob/ed93c12dc1835ec0e7fb3e4be3504ceb7061610e/LICENSE) |
| Customized frontend | Upstream v2.3.0 plus `../frontend/branding.patch` | [GNU GPL version 3](https://github.com/blockscout/frontend/blob/v2.3.0/LICENSE) |
| Deployed statistics service | stats-v2.9.2; commit `bbf2d71618e39d61edb2ada7ad7ab19cf06ae586` | [MIT license](https://github.com/blockscout/blockscout-rs/blob/bbf2d71618e39d61edb2ada7ad7ab19cf06ae586/LICENSE-MIT) |

The current checkout must not be described as the source corresponding to the deployed v9.0.2 backend. Replacing its LICENSE with the older GPL text would not establish permission for the later changes.

The current source license requires preservation of branding and attribution in sections 2(b) and 2(c), limits the commercial uses described in section 4, and requires a commercial license for distribution of derivative works in section 5(b). Section 3(a) distinguishes earlier releases from this license. These provisions must not be applied indiscriminately to the separately licensed older components.

## Findings About Removed Blockscout Notices

The frontend patch removes the original footer's Blockscout attribution, its displayed Blockscout Limited copyright notice, and the frontend version/source links. The current footer contains only a GitHub account link and Donate. Product names and other user-facing strings were also changed to ColossusX.

The custom frontend image still contains the upstream GPL text at `/app/LICENSE`; the Dockerfile explicitly copies it. This is useful evidence of preservation inside the image, but it does not by itself demonstrate that browser recipients receive suitable notices or access to the corresponding modified source.

GPLv3 permits commercial activity subject to its conditions. Its sections 4 and 5 address preservation of legal notices, marking modifications, and interactive legal notices; section 6 addresses corresponding source when object code is conveyed. Section 5(d) includes an exception concerning upstream interfaces without appropriate legal notices, so this review does not declare that a particular footer design is automatically unlawful. Copyright removal and source availability require review. Serving backend functionality over a network and sending frontend JavaScript to browsers are different distribution facts. See the [frontend GPL text](https://github.com/blockscout/frontend/blob/v2.3.0/LICENSE).

There is no basis here to require every product label, every social link, or every advertisement to revert to Blockscout. Branding changes and removal of copyright or license information must be assessed separately. The current 11.3.1 source license has additional explicit branding requirements that are not inferred from the older GPL text.

## Concrete Remediation to Prepare for Release

1. Select and record a legally usable source baseline. A candidate for a GPL-based release is the exact backend v9.0.2 source already used in production, with the frontend v2.3.0 source and its modifications. Reapply original project changes to that baseline instead of copying newer restricted source files wholesale. This is a release plan, not a completed source migration or a recommendation about the older version's security support.
2. Preserve applicable upstream licenses and copyright notices, and record modification dates. Keep third-party components under their own applicable licenses rather than asserting that every dependency has one new license.
3. Prepare a visible legal-notices entry that identifies the upstream authors, applicable license, warranty disclaimer, and source location. Review the final display against the selected license and any signed agreement. Restore the removed copyright attribution as part of that work; preserving the ColossusX product identity does not require deleting the upstream authorship information.
4. Publish the exact modified frontend source and build materials at a stable URL or provide another applicable compliant source mechanism. A generic GitHub account link and an upstream-only source link do not establish availability of ColossusX's modified source.
5. Inventory runtime and bundled dependency licenses. The component audit verified Redis 8.10.1 (RSALv2, SSPLv1, or AGPLv3), PostgreSQL 17.11 (PostgreSQL License), and the nginx 1.31.6 container (BSD-2-Clause). Record which Redis alternative the release relies on; AGPLv3 is its open-source option. Operating-system packages, bundled libraries, the host nginx installation, and JavaScript/Elixir/Rust dependencies still require inventory. This review is not a complete transitive dependency audit or software bill of materials.
6. Confirm the distribution license for the mascot artwork from `CypherTroopers/logo`. `../frontend/assets/sources.json` records provenance and hashes but is not itself an artwork license grant.
7. Validate the public release in a clean environment. The ColossusX deployment directory is currently untracked, and its first-run configuration and build steps still need publication preparation.

## Separate Commercial Agreement

A request for commercial terms is prepared in [COMMERCIAL-LICENSE-REQUEST.md](COMMERCIAL-LICENSE-REQUEST.md). It has not been sent, and no terms or fees have been accepted. Any agreement must explicitly cover the chosen versions, public source distribution, downstream rights, paid uses, and the intended attribution changes. Payment alone must not be assumed to grant all of those rights.

The current Blockscout license directs commercial inquiries to [Blockscout's contact form](https://eaas.blockscout.com/#contact). An executed agreement and a review of its scope are external prerequisites for claiming additional contractual permission.

Open-source and commercial use are compatible; the Open Source Initiative explains this in its [FAQ](https://opensource.org/faq). A release should not be labeled open source merely because its files are visible on GitHub.
