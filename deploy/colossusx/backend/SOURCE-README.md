# ColossusX backend source

This tree is based on Blockscout v10.2.6, commit
`90f7dd8e9348123b74dfd23f69ab7da76191a820`, under GPLv3. The existing GPL text
and third-party notices are retained. See `LICENSE-PREPARATION.md` for the source
exclusions and English edits. The ColossusX Dockerfile is derived from the exact
upstream `docker/Dockerfile`; it bounds BEAM/compiler concurrency, pins the build
base, and records version, revision and source archive hash in the resulting image.

After extracting the published source archive, build with:

```bash
COLOSSUSX_SOURCE_SHA256=THE_DOWNLOADED_ARCHIVE_SHA256 \
COLOSSUSX_SOURCE_URL=https://YOUR_DOMAIN/source/THE_DOWNLOADED_ARCHIVE_FILENAME \
  ./build-colossusx.sh
```

Use the SHA-256 checksum file provided alongside the archive. The script defaults
to `local-rebuild` when no archive digest is provided and must not be described as
the published artifact in that case. The image tag is `colossusx-backend:10.2.6`.
The Elixir requirement is 1.19.4 with Erlang/OTP 27.3.4.6. The Docker build retrieves
the locked Elixir dependencies and operating-system packages; network access is
needed. Development/test dependencies are outside the production build. Initial
compilation is memory intensive; build with a memory limit and sufficient swap or
use a separate build host before restarting production services.

The source release does not include dependencies, native libraries, databases,
private environment files, or a container image. Corresponding-source and notice
obligations for separately fetched dependencies still need to be met if a binary
image is redistributed. A working build does not certify the licenses of all native
or operating-system packages.

The opt-in FHS-D reward adapter and its API/UI contract are documented in
`COLOSSUSX_REWARDS.md`. It indexes block-production, Common miner and Common RPC
payouts without Ethereum fee additions. Its parser, RPC, persistence, API and
schema tests are included in the source tree. The audited patch and per-file
baseline/result hashes are retained under `colossusx/patches/`.
