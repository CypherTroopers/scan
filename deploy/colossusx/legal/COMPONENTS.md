# Deployed component and frontend notice audit

**Historical audit:** The image IDs and footer observations below were recorded
before the GPL release remediation. See [RELEASE-STATUS.md](RELEASE-STATUS.md)
for the subsequent build, source packaging, restored notices, and current
verification status. Links into the evolving patch identify the original audit
locations and may no longer point to the same changes.

Audit date: 2026-09-21. Scope: the running `deploy/colossusx` deployment, its selected image metadata, version-specific upstream license files, and the local frontend patch. This is a technical evidence record, not a legal compliance opinion. No license, source, configuration, image, or running service was changed for this audit. The operator reports that no separate Blockscout commercial license or permission has been obtained.

## Verified component licenses

These are the licenses of the named upstream projects at the deployed versions. They are not a complete license inventory of every library, asset, operating-system package, or binary included in each Docker image.

| Component | Deployed version and source provenance | Verified project license and primary source |
| --- | --- | --- |
| Backend | `v9.0.2`; image OCI revision `ed93c12dc1835ec0e7fb3e4be3504ceb7061610e` | GPL version 3 text; OCI license label `GPL-3.0`. [Exact revision LICENSE](https://github.com/blockscout/blockscout/blob/ed93c12dc1835ec0e7fb3e4be3504ceb7061610e/LICENSE). |
| Frontend | Upstream `v2.3.0`, tag resolving to commit `e1111ee2f89af699e53f441340f5149ec153f6f3`, plus the local `branding.patch` and assets | GPL version 3 text. [Exact revision LICENSE](https://github.com/blockscout/frontend/blob/e1111ee2f89af699e53f441340f5149ec153f6f3/LICENSE). The running image contains the same license text. |
| Statistics | `stats-v2.9.2`; image OCI revision `bbf2d71618e39d61edb2ada7ad7ab19cf06ae586` | MIT; OCI label agrees. [Exact revision LICENSE-MIT](https://github.com/blockscout/blockscout-rs/blob/bbf2d71618e39d61edb2ada7ad7ab19cf06ae586/LICENSE-MIT). The copyright holder stated in this file is Blockscout Technologies Ltd., 2025. The filename is `LICENSE-MIT`, not `LICENSE`. |
| Redis | Runtime binary reports `8.10.1` | Choice of RSALv2, SSPLv1, or AGPLv3. [Exact version LICENSE.txt](https://github.com/redis/redis/blob/8.10.1/LICENSE.txt); [official licensing explanation](https://redis.io/legal/licenses/). Redis 8.10.1 must not be described as BSD-only. AGPLv3 provides the OSS option; the other two alternatives are source-available licenses. The presence of a separate Redis container alone does not establish the license of the whole application. |
| PostgreSQL | Both database containers report `17.11 (Debian 17.11-1.pgdg13+2)` | PostgreSQL License. [Exact version COPYRIGHT](https://github.com/postgres/postgres/blob/REL_17_11/COPYRIGHT). |
| NGINX container | Runtime binary reports `1.31.6` | BSD 2-Clause text. [Exact version LICENSE](https://github.com/nginx/nginx/blob/release-1.31.6/LICENSE). This row covers the container proxy; the separate host NGINX installation was not inventoried in this sub-audit. |

The deployed backend version is distinct from the repository's current checkout. A license conclusion about that checkout cannot be substituted for the version-specific evidence above, or vice versa.

## Image and build correspondence

Selected non-secret image metadata was saved locally in `/tmp/colossusx-license-audit/image-evidence.json`; that temporary evidence file is not included in this repository. The following are the observed Docker image IDs, also used by the pinned deployment where applicable:

| Component | Image ID |
| --- | --- |
| Backend | `sha256:7659f168e4e2f6b73dd559ae5278fe96ba67bc2905ea01b57a814c68adf5a9dc` |
| Frontend | `sha256:058315cfa719bd0662551fe2c3e91444266d979cbfd8f8f90435364fdca5071c` |
| Statistics | `sha256:7f9781bb59f51050b22a11161734eac6da86fdffb91409151288fbae1dc2355e` |
| PostgreSQL, both instances | `sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675` |
| Redis | `sha256:bd999b5cfee25fb24b8320a31fddbd69f462df44c8138c66e369582937beebc0` |
| NGINX | `sha256:cb29e33d254e8b72164ad5b8b9014f44e98e6e5f6d51ef02ee859f96708c90fe` |

Deployment references: [compose.yml backend](../compose.yml#L42), [statistics](../compose.yml#L84), [PostgreSQL](../compose.yml#L14), [Redis](../compose.yml#L33), [NGINX](../compose.yml#L126).

The effective frontend is `colossusx-frontend:2.3.0-branding`, selected by [compose.override.yml:11](../compose.override.yml#L11), with `pull_policy: never`. The base compose file also contains an upstream frontend image, but that is not the currently running frontend when the override is loaded.

The local frontend image has no OCI source/license labels. Its provenance is instead supported by [build.sh:8](../frontend/build.sh#L8): the script downloads the `v2.3.0` archive, verifies SHA-256 `d7647463634e2f54ac481f23e0a37d51ef61bb5eddb320b53f10975807948391`, applies the patch at line 22, copies local assets at line 24, and builds the image. Its package.json version is `1.0.0`; that package field is not the upstream release identifier.

## Frontend attribution changes and preserved material

The local patch removes more than product-name text. The original footer includes upstream project information, backend/frontend version links, and a Blockscout Limited copyright notice. The corresponding source can be reviewed in the [exact upstream Footer.tsx](https://github.com/blockscout/frontend/blob/e1111ee2f89af699e53f441340f5149ec153f6f3/ui/snippets/footer/Footer.tsx#L119).

| Evidence | Observed change |
| --- | --- |
| [branding.patch:1210](../frontend/branding.patch#L1210) and [branding.patch:1265](../frontend/branding.patch#L1265) | Removes upstream frontend version/commit URLs and their rendering. |
| [branding.patch:1304](../frontend/branding.patch#L1304) | Removes the original footer project-information section, including upstream branding and version links. |
| [branding.patch:1334](../frontend/branding.patch#L1334) | Deletes the rendered Blockscout Limited copyright statement from the footer. |
| [branding.patch:1456](../frontend/branding.patch#L1456) | The replacement footer links to `https://github.com/CypherTroopers` and a donation address. It does not add a license, legal-notices, warranty, or corresponding-source link. The GitHub link is an organization/profile link, not an identified source release for the deployed build. |
| [branding.patch:171](../frontend/branding.patch#L171), [branding.patch:191](../frontend/branding.patch#L191), and [branding.patch:270](../frontend/branding.patch#L270) | Replaces Blockscout names in metadata and API documentation UI with ColossusX. These wording changes do not grant ownership of the underlying code or change its license. |

The saved public UI verification at `/tmp/colossusx-ui-verification/statistics-after/report.json`, started at `2026-09-20T11:36:08.297Z`, recorded the footer text as `GitHub` and `Donate` in desktop/mobile light/dark profiles. This is supporting historical evidence for the currently observed image ID, not a fresh audit of every public page or menu.

The license file itself was preserved: [Dockerfile:93](../frontend/Dockerfile#L93) copies `/app/LICENSE` into the runtime image. A read from the running frontend produced the same bytes as the exact upstream commit's `LICENSE`: SHA-256 `c53a65c2fd561c87eaabf1072ef5dcab8653042bc15308465f52413585eb6271`. The patch does not modify that file. The copy resides at `/app/LICENSE`, outside `/app/public`; its existence inside a container does not establish an accessible UI notice or fulfillment of source-delivery conditions.

No dedicated `LICENSE`, `NOTICE`, `COPYING`, or `AUTHORS` inventory file was found under `deploy/colossusx` in this scan. The upstream frontend tree has its top-level `LICENSE`; this does not rule out copyright notices in source files or licenses within dependencies. Limited backend/statistics image path checks did not locate a top-level license file, but those checks were not exhaustive and do not establish that the entire images lack notices.

## Publication and interactive-notice questions

GPLv3 distinguishes interaction over a network without transfer of a copy from conveying copies. Publishing covered source or distributing images/bundles requires a separate assessment. Frontend JavaScript is delivered to browsers, so the frontend cannot automatically be treated as only a server process. Modified-source notices and corresponding-source availability require review. GPLv3 section 5(d) addresses interactive legal notices, with an exception for original interfaces that lacked them. The inspected upstream footer proves a copyright display, but does not by itself prove every element of the defined Appropriate Legal Notices. Its removal therefore raises a concrete review question; this audit does not conclude that section 5(d) was necessarily violated. [Official GPLv3, definitions and sections 5–6](https://www.gnu.org/licenses/gpl-3.0.html).

Retaining ColossusX visual branding and retaining upstream legal attribution are compatible technical choices. Restoring a notice does not require representing the fork as an official Blockscout service. Trademark permission and copyright/license obligations should be evaluated separately.

## Remediation options for owner review

These are proposals only; none was applied by this audit.

1. Preserve version-specific upstream license texts and copyright notices, document local modifications and dates, and add a readily accessible legal/about location with upstream attribution, license access, and the required rights/warranty information after the legal review identifies applicable requirements.
2. Identify and provide the corresponding source for the exact deployed frontend, including local modifications and the build material needed for that release. The current upstream download, checksum, patch, and Dockerfiles are useful evidence; this report does not certify that a profile link or an upstream link plus patch alone satisfies every distribution requirement.
3. Maintain a component/license manifest that distinguishes the current repository checkout from the older deployed backend and frontend. Select and document the Redis license basis, and inventory transitive dependencies, bundled operating-system packages, assets, and fonts before claiming a complete audit.
4. Obtain written commercial-license terms from the relevant rights holder before relying on an exception to existing terms. Confirm explicitly which repositories, versions, modifications, branding/attribution requirements, redistribution rights, and third-party components the agreement covers. A commercial agreement for one component should not be assumed to relicense the whole stack.

## Saved evidence and limits

Temporary evidence collected under `/tmp/colossusx-license-audit` includes `image-evidence.json`, the exact backend/frontend/statistics license downloads, the frontend runtime license copy, the upstream footer, the frontend tag response, and version-specific Redis/PostgreSQL/NGINX license files. These temporary evidence files are not part of this repository. The version-specific source links and relevant hashes are recorded above for independent verification. Source downloads use fixed revisions or exact release tags where identified above. The Redis `LICENSE.txt` SHA-256 is `4a0e416b9537688f30dfe69ddaceb2ca64d96b7df02a0a6760d376890ddc4e40`.

This was not a complete transitive dependency or SBOM review, an asset-rights investigation, a source-to-binary reproducibility certification, a review of every interface, or verification of an executed commercial contract. No guarantee of license compliance or third-party permission follows from this report. No secrets or full environment dumps were collected.
