# ColossusX Frontend Source

This is the full modified source used to build the ColossusX frontend, based on
Blockscout frontend v2.7.2, upstream commit
`446c409eeb54274aab90ff371a705f9699cd84ef`.

The upstream GPLv3 license is retained in `LICENSE`. ColossusX modifications are
also under GPLv3; see `COLOSSUSX_CHANGES.md` and the dated source notices. Bundled
libraries, fonts, artwork, and vendor code retain their respective notices and
licenses. The version-specific source archive and its SHA-256 are available
through the explorer's `/source/` page.

## Build

Install Docker with Buildx, then run from this extracted source directory:

```sh
./build-colossusx.sh
```

This builds `colossusx-frontend:2.7.2-branding`. The build uses the checked-in
`yarn.lock`, vendored wallet hooks, and pinned Node base image. It requires network
access to the package registries and image registry. Operating-system package
repositories are not snapshot-pinned, so identical image bytes are not promised.

The backend and statistics services are separate components. Runtime configuration
is documented in `docs/ENVS.md` and the ColossusX deployment directory. Do not add
production passwords or a private `.env` file to the source archive.

This ColossusX build disables wallet connection and advertising integrations.
Restricted or unlicensed optional SDKs are removed from its dependency graph.
The read-only explorer, contract reads, statistics, and transaction lookup remain
available. Re-enabling removed integrations requires new code and a review of
their licenses.
