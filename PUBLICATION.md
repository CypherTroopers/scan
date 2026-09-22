# ColossusX Public Source Preparation

Do not publish this entire working checkout as the ColossusX GPL release.
It contains Blockscout backend 11.3.1 under the separate Blockscout Software
Licence. Its license has not been replaced and no commercial agreement has
been obtained.

The independent GPL release is assembled using
[`deploy/colossusx/release/`](deploy/colossusx/release/README.md). Its selected
baseline is backend v10.2.6 and frontend v2.7.2, with ColossusX modifications,
documented source exclusions, and retained third-party notices. Stats v2.15.0
is selected under MIT for this backend schema. The upgrade's independent output
is `public-release/colossusx-10.2.6/`, excluded from this checkout's Git index.
Only that prepared output should become the new public repository. Do not copy
this checkout's Git history, production `.env`, or backups into it.

The custom mascot artwork is released under CC0-1.0, without a credit
requirement. This does not change the licenses or attribution requirements of
Blockscout, fonts, or other third-party components.

Read the [current release status](deploy/colossusx/legal/RELEASE-STATUS.md)
and the generated source notices before publication. The frontend source
and backend source archives must match the source hashes recorded in their
respective deployed images. The upgraded backend is built from the prepared
v10.2.6 source, including its documented exclusions and English edits. The earlier
`public-release/colossusx/` tree is the historical v9.0.2/frontend v2.3.0 release;
it must not be confused with the upgraded output.

No GitHub publication or commercial agreement is part of the assembly step.
Preparing this source does not establish all rights to subsequently bundle and
redistribute dependency binaries. Upgrade image builds, independent assembly,
database reset/resynchronization, and public acceptance checks are recorded
separately in the current release status; earlier verification results do not
establish that the new versions have passed those checks.
