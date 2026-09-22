# ColossusX Explorer

ColossusX is a customized deployment of Blockscout. This independent source distribution uses the GPLv3 backend at **v10.2.6**, commit `90f7dd8e9348123b74dfd23f69ab7da76191a820`, and the modified GPLv3 frontend at **v2.7.2**. It does not include the later backend 11.3.1 checkout or its Git history.

Commercial use and redistribution are permitted by the applicable open-source licenses, subject to their conditions. This release does not represent a separately negotiated Blockscout commercial agreement, transfer ownership of upstream code, or grant trademark rights. Preserve the copyright notices, license texts, modification notices, and source access when distributing it. See [NOTICE.md](NOTICE.md), [THIRD_PARTY.md](THIRD_PARTY.md), and [LICENSE](LICENSE).

## Source layout

| Directory | Contents |
| --- | --- |
| `backend/` | Full modified GPL backend v10.2.6 source, reviewed exclusions, notices and image build scripts |
| `frontend/` | Complete modified frontend v2.7.2, including its lockfiles and build scripts |
| `deployment/` | Reviewed ColossusX deployment files, public notices, and nonsecret configuration |
| `patches/` | Applied backend English text/test fixture patch and hash-checked license-preparation instructions |
| `licenses/` | Release license texts, including CC0 for the custom mascot artwork |

`SOURCE-PROVENANCE.json` records the selected upstream sources, backend exclusions, and every frontend file that differs from the verified upstream archive. [backend/LICENSE-PREPARATION.md](backend/LICENSE-PREPARATION.md) explains the excluded Arbitrum metadata and contract fixture/test. `MODIFICATIONS.md` describes the changes. `SHA256SUMS` records the assembled files before any local changes. Verify them with `sha256sum --check SHA256SUMS` from this directory.

## Build and run

See [deployment/README.md](deployment/README.md) for the Docker workflow, secret generation, source packaging, and configuration. Both backend and frontend are built from this release's modified source. Their individual build entry points are:

```sh
./backend/build-colossusx.sh
./frontend/build-colossusx.sh
```

The custom Dockerfiles and scripts are part of the distributed source. Follow the deployment guide to archive clean sources and pass their SHA-256 values to the build scripts before serving them publicly. Docker downloads pinned base images and dependencies during the build; an internet connection is required. Dependency downloads follow the checked-in lockfiles. No private signing key, production secret, or commercial service account is required by this release's core explorer workflow.

For backend source builds, follow [backend/COLOSSUSX_BUILD.md](backend/COLOSSUSX_BUILD.md) and the backend's pinned toolchain: Elixir `1.19.4-otp-27`, Erlang `27.3.4.6`, and Node.js `20.17.0`. The selected backend image is built from this prepared source, including its documented exclusions and English edits. Its source-archive hash is recorded in the image labels. The full backend development and test environment has separate requirements listed in its upstream documentation. Stats is pinned to MIT-licensed v2.15.0 for this backend schema.

## Source availability and updates

The deployed legal page should link to accessible archives of the exact modified backend and frontend sources, including their build materials. An upstream-only link or a GitHub account home page does not replace the modified source. Keep the source link available and update the matching archive whenever either deployed application changes. When redistributing binaries or images, review their own corresponding-source and third-party notice requirements too.

Updates must be reviewed by exact source version and license. Do not replace this GPL source baseline with later backend files or release tags without checking the licenses of that new material. This baseline was selected to match the deployed backend and known source grant, not as a claim that it contains all later security fixes.

The release does not vendor container images or installed package dependencies. Their licenses remain separate; see the inventory and limits in [THIRD_PARTY.md](THIRD_PARTY.md). The custom mascot images and their size/format variants use CC0 1.0 with no attribution requirement; see `licenses/CC0-1.0.txt`. Third-party artwork and trademarks retain their own terms.
