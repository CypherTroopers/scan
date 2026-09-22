# Independent GPL source assembly

This tool creates a new source tree based on the exact GPL backend v10.2.6 Git object, with the documented third-party exclusions and a clean modified frontend v2.7.2. The deployment selects MIT-licensed stats v2.15.0 for the backend 10.2 schema. It never copies the current backend 11.3.1 working tree or its Git history. It refuses to replace an existing output directory and does not build, deploy, commit, or push anything.

Python 3.12 or newer, Git, and GNU patch are required. The original frontend tar archive is verified against SHA-256 `34f4758f639f029bfe91d47584e3dcdbd5033d72a6b32d0c93904a5e347f081f`. The modified frontend must retain its exact GPL license, full source, lockfiles, and ColossusX build scripts. The pinned archive, rather than the package's `version` field, identifies the selected upstream release.

```sh
python3 deploy/colossusx/release/assemble.py \
  --frontend-source /path/to/clean-modified-frontend \
  --frontend-archive /path/to/frontend-v2.7.2.tar.gz \
  --backend-runtime-source prepared \
  --output /root/blockscout/public-release/colossusx-10.2.6
```

The default backend repository is this working repository, but only `git archive 90f7dd8e9348123b74dfd23f69ab7da76191a820` is used. A clone containing that commit can be supplied with `--backend-repository`. `--deployment-source` can select a reviewed operations directory with the same allowlisted paths. The explicit output path separates the upgrade from the historical `public-release/colossusx` release. The `prepared` runtime-source option records that the backend image is built from the prepared source; it does not itself run or verify that build.

Deployment files are individually allowlisted in the script. Production `.env`, backups, database dumps, source archive output, private audit reports, commercial-license inquiries, certificate/private-key files, node_modules, build outputs, and Git metadata are excluded. The reviewed backend dependency report is included with the release patches. The public maintenance page and upgrade browser checks are included, while `network-info/maintenance.flag` is excluded and rejected by the final scanner. The source archive must not be recursively copied into itself. The ordinary `backend.env` and `frontend.env` files are public settings; nonempty credential-like variables in them cause assembly to fail. The scanner provides targeted checks, not a guarantee that arbitrary source cannot contain a secret.

The backend is archived from the exact GPL baseline, then prepared using `patches/backend-license-preparation.json`: omit the restricted Arbitrum metadata, an UNLICENSED contract fixture, and the one test containing that fixture's compiled bytecode. The rest of the test module is preserved. The manifest stores hashes and transformation instructions, without reproducing the excluded source in a deletion diff. `patches/backend-english.patch` is applied to the known GPL baseline after verifying the patch and original-file hashes. The three modified files receive dated notices. Only the reviewed documentation and Unicode fixture edits are ported; no complete files from backend 11.3.1 are copied. An adjacent BSD notice is added for the already-vendored Ace 1.4.14 files.

The prepared backend includes its custom Dockerfile, source build script, pinned Elixir 1.19.4/Erlang 27.3.4.6 base, dependency report and modification provenance. `../backend/build.sh --prepare-only` reconstructs the same backend source and creates a deterministic archive; the full independent release builds from `backend/build-colossusx.sh`. Image labels record the matching source archive SHA-256. The modified frontend is likewise packaged before its build. Recheck both published archive hashes against the selected image labels after deployment. Dependency implementations and base-image/native components remain a separate binary redistribution review scope.

## Custom artwork

The custom mascot images and their size/format variants use CC0 1.0, without an attribution requirement. The source includes a short asset license and the full CC0 text. No personal copyright statement or permission record is distributed. Blockscout names, logos, and other third-party material retain their own terms.

The assembler verifies the artwork license and checks that frontend and deployment image copies agree. These checks identify the materials covered by this release; new third-party artwork needs its own applicable terms.

After assembly, verify `sha256sum --check SHA256SUMS` inside the release tree and review `SOURCE-PROVENANCE.json`, public notices, source URLs, and the actual file inventory. This tool does not decide the legal status of third-party source, waive license obligations, or negotiate a commercial agreement.
