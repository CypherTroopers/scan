#!/usr/bin/env python3
"""Create download links only for existing, checksum-verified source artifacts.

Created for ColossusX on 2026-09-21. SPDX-License-Identifier: GPL-3.0-only
"""

import hashlib
from html import escape
from pathlib import Path


def main():
    distribution = Path(__file__).resolve().parent.parent / "source-dist"
    digest, name = (distribution / "frontend.sha256").read_text().split()
    if Path(name).name != name or not name.endswith(".tar.gz"):
        raise ValueError("Unexpected source archive name")
    with (distribution / name).open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual != digest:
        raise ValueError("Frontend source checksum mismatch")
    backend_name = (distribution / "backend-current.txt").read_text().strip()
    if Path(backend_name).name != backend_name or not backend_name.endswith(".tar.gz"):
        raise ValueError("Unexpected backend source archive name")
    backend_digest, recorded_name = (distribution / f"{backend_name}.sha256").read_text().split()
    with (distribution / backend_name).open("rb") as handle:
        if recorded_name != backend_name or hashlib.file_digest(handle, "sha256").hexdigest() != backend_digest:
            raise ValueError("Backend source checksum mismatch")
    page = f'''<!doctype html>
<!-- ColossusX source distribution. Created 2026-09-21; GPL-3.0-only. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Source Code | ColossusX</title><link rel="stylesheet" href="/legal/style.css"></head>
<body><nav aria-label="Navigation"><a href="/">Explorer</a><a href="/legal/">Licenses &amp; Notices</a></nav>
<main><h1>ColossusX Source Code</h1>
<p>This page provides the modified source for the backend and frontend served by this explorer.
Downloads are free and do not require an account.</p>
<h2>Frontend v2.7.2 with ColossusX changes</h2>
<p><a href="{escape(name)}" download>Download the complete modified frontend source (.tar.gz)</a></p>
<p>SHA-256: <code>{digest}</code> (<a href="frontend.sha256">checksum file</a>)</p>
<p>The archive contains source files, dependency lockfiles, vendor source and notices,
artwork license, dated changes, and the Dockerfiles and script used to build the application.
Read <code>COLOSSUSX_BUILD.md</code>, then run <code>./build-colossusx.sh</code> with Docker and Buildx installed.</p>
<p>Upstream: <a href="https://github.com/blockscout/frontend/tree/446c409eeb54274aab90ff371a705f9699cd84ef">Blockscout frontend v2.7.2</a>.
The frontend and ColossusX code modifications are licensed under <a href="/legal/GPL-3.0.txt">GPLv3</a>.
Other bundled material retains its own license and copyright notices.</p>
<h2>Backend v10.2.6 with ColossusX changes</h2>
<p><a href="{escape(backend_name)}" download>Download the complete modified backend source (.tar.gz)</a></p>
<p>SHA-256: <code>{backend_digest}</code> (<a href="{escape(backend_name)}.sha256">checksum file</a>)</p>
<p>This backend was built from the supplied modified GPLv3 source, based on
<a href="https://github.com/blockscout/blockscout/tree/90f7dd8e9348123b74dfd23f69ab7da76191a820">upstream v10.2.6</a>.
The archive includes its Dockerfile, dependency lockfile, dated modifications and build instructions.
Read <code>COLOSSUSX_BUILD.md</code> and run <code>./build-colossusx.sh</code>.</p>
<h2>Statistics v2.15.0</h2>
<p><a href="https://github.com/blockscout/blockscout-rs/tree/3fb0afcbed1f6d4443f06d88e2f0a485adaf7659">Exact upstream source</a>,
licensed under <a href="/legal/STATS-MIT.txt">MIT</a>.</p>
<h2>Redis v8.10.1</h2>
<p>This deployment selects the AGPLv3 licensing option for unmodified Redis.
<a href="https://github.com/redis/redis/tree/8.10.1">Upstream source and build instructions</a> and
<a href="/legal/REDIS.txt">license terms</a>.</p>
<p>Source availability is tied to the deployed build. Previous archives are retained when the frontend is rebuilt.</p>
</main><footer><a href="https://blockscout.com">Made with Blockscout</a><a href="/legal/">Licenses &amp; Notices</a></footer></body></html>
'''
    staged = distribution / "index.html.tmp"
    staged.write_text(page, encoding="utf-8")
    staged.replace(distribution / "index.html")


if __name__ == "__main__":
    main()
