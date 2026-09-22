# Third-party components

This distribution preserves upstream license files, copyright notices, lockfiles, and embedded third-party notices. It is not a relicensing of all included material under a single new license.

| Component | Selected source/version | License record |
| --- | --- | --- |
| Backend | Blockscout v10.2.6, `90f7dd8e9348123b74dfd23f69ab7da76191a820` | GPL version 3; `backend/LICENSE` |
| Modified frontend | Blockscout frontend v2.7.2 | GPL version 3; `frontend/LICENSE` |
| Vendored Ace editor | Ace 1.4.14 | BSD 3-Clause; restored in `backend/apps/block_scout_web/assets/js/lib/ace/LICENSE` from the official v1.4.14 license |
| Stats service | stats/v2.15.0, `3fb0afcbed1f6d4443f06d88e2f0a485adaf7659` | [Upstream MIT license](https://github.com/blockscout/blockscout-rs/blob/3fb0afcbed1f6d4443f06d88e2f0a485adaf7659/LICENSE-MIT) |
| Custom mascot artwork | Supplied mascot images and size/format variants | CC0 1.0; `licenses/CC0-1.0.txt`; no attribution required |
| Container images and package dependencies | Compose digests, Dockerfile base digests, and checked-in lockfiles | Their own component and dependency licenses; not replaced by this release |

Stats and infrastructure container images are referenced rather than redistributed in this source tree. Backend and frontend dependencies are resolved from the included lockfiles rather than vendored as installed packages. Downloading a component from its publisher is distinct from republishing its image or binaries. If redistributing images, packages, or other object code, preserve their notices and provide corresponding source where their licenses require it.

The original backend includes embedded contract examples and third-party source fixtures with individual license declarations. Preserve those declarations. A root GPL license does not erase their separate provenance or conditions. This prepared source removes the Arbitrum precompile preset containing BUSL-1.1 interfaces and the UNLICENSED issue_4758 fixture plus its associated test/bytecode. `backend/LICENSE-PREPARATION.md` documents the exclusions. The selected ColossusX backend image is built from this prepared source, and its source archive hash is recorded in image labels. Separately fetched dependencies still retain their own source and notice obligations.

The backend lockfile contains 188 dependency references. `patches/backend-dependency-review.json` records the selected versions and metadata evidence, including verified archive SHA-256 values for the 63 new or changed Hex packages. The previously reviewed `quantile_estimator` dependency has been removed upstream, and the `prometheus_ex` Git fork is replaced by Hex 5.1.0 with an MIT license file. The new `ex_eth_bls@0.1.0` declares MIT but has no top-level license file in its exact Hex package; its upstream notice provenance and Rust/native dependencies require separate review before binary redistribution. `bcrypt_elixir@3.3.2` retains a historical four-clause BSD notice; the [upstream bcrypt change](https://github.com/pyca/bcrypt/pull/170) links the author's published advertising-clause waiver. Verify its applicability and preserve the relevant notices when bundling. Installed dependencies are not bundled in this source tree. The source release must not be described as an all-dependencies or combined-binary licensing certification.

The SPDX inventory and release-component checks are not a complete legal opinion or an exhaustive audit of every transitive package, artwork item embedded by upstream, or future dependency update. No representation is made that Blockscout has granted a separate commercial agreement. Before distributing a new binary bundle, review the exact artifacts and dependencies it includes; the source publication here does not authorize later restricted-license upstream code.
