#!/usr/bin/env python3
"""Assemble a separate, pinned GPL source distribution without host secrets.

Modified for ColossusX on 2026-09-21. SPDX-License-Identifier: GPL-3.0-only
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile


BACKEND_VERSION = "10.2.6"
BACKEND_COMMIT = "90f7dd8e9348123b74dfd23f69ab7da76191a820"
FRONTEND_VERSION = "2.7.2"
FRONTEND_ARCHIVE_SHA256 = "34f4758f639f029bfe91d47584e3dcdbd5033d72a6b32d0c93904a5e347f081f"
FRONTEND_LICENSE_SHA256 = "c53a65c2fd561c87eaabf1072ef5dcab8653042bc15308465f52413585eb6271"
RELEASE_DIR = Path(__file__).resolve().parent
DATE = "2026-09-21"
BACKEND_ENGLISH_PATCH_SHA256 = "5ad9ca4532d0d7f3c212bb771f94f5fab4709c204c0866c052d042af84a947ac"
BACKEND_ENGLISH_FILES = {
    "apps/block_scout_web/lib/block_scout_web/graphql/schema/scalars.ex": "75c71073765439aca2a2513ac42147283df1214819e81801b5d2ab0f732af36f",
    "apps/explorer/lib/explorer/chain/wei.ex": "360adb90ce72f82060ca43cd78747b27b8652ac2301f84267b2602a3099304ef",
    "apps/explorer/test/explorer/token/metadata_retriever_test.exs": "33b9724c1281c6308843319b3900c45c09354cdc3e3a8eda6f6c5c9d452578a2",
}

# Each path is deliberately reviewed. Do not replace this with a directory copy.
OPS_FILES = (
    "LICENSE", "compose.yml", "compose.override.yml", "backend.env", "frontend.env", "nginx.conf",
    "frontend/Dockerfile", "frontend/Dockerfile.deps", "frontend/build.sh", "frontend/branding.patch",
    "frontend/build-from-source.sh", "frontend/SOURCE-README.md", "frontend/update-source-index.py",
    "backend/Dockerfile", "backend/build.sh", "backend/build-from-source.sh", "backend/SOURCE-README.md", "backend/REWARDS.md",
    "host-nginx/bootstrap.conf", "host-nginx/colossusx.conf", "host-nginx/renew-nginx.sh",
    "network-info/admission.js", "network-info/app.js", "network-info/index.html", "network-info/style.css",
    "network-info/maintenance.html",
    "network-info/logo.png", "network-info/favicon.ico", "network-info/apple-touch-icon.png",
    "network-info/ARTWORK-LICENSE.txt",
    "tests/admission.test.mjs", "tests/upgrade-ui.mjs", "tests/transaction-fees-ui.mjs", "tests/rewards-ui.mjs",
)
EXCLUDED_DIRS = {".git", ".next", "node_modules", "coverage", "playwright-report", "test-results", "__pycache__"}
ARTWORK_EXTENSIONS = {".png", ".svg", ".ico", ".jpg", ".jpeg", ".webp"}
SECRET_PATTERN = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----|\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}")
SPDX_PATTERN = re.compile(r"SPDX-License-Identifier:[ \t]*([^\r\n\\\"']+)")
REVIEWED_SPDX = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "CC0-1.0", "CC-BY-4.0",
    "GPL-2.0-or-later", "GPL-3.0", "GPL-3.0-only", "GPL-3.0-or-later",
}


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def files(root):
    return sorted(path for path in root.rglob("*") if path.is_file())


def safe_extract(archive, target):
    with tarfile.open(archive) as handle:
        for member in handle.getmembers():
            if member.issym() or member.islnk():
                raise ValueError(f"Unexpected archive link: {member.name}")
        handle.extractall(target, filter="data")


def checked_copy(source, target):
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"Expected an ordinary file: {source.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_frontend(source, target, baseline):
    for directory, subdirs, filenames in os.walk(source, followlinks=False):
        parent = Path(directory)
        subdirs[:] = sorted(name for name in subdirs if name not in EXCLUDED_DIRS)
        for name in subdirs:
            if (parent / name).is_symlink():
                raise ValueError(f"Unexpected frontend directory link: {name}")
        for name in sorted(filenames):
            path = parent / name
            relative = path.relative_to(source)
            # Include upstream environment examples/fixtures only when unchanged.
            if name.startswith(".env"):
                original = baseline / relative
                if not original.is_file() or sha256(path) != sha256(original):
                    raise ValueError(f"Non-upstream environment file in frontend: {relative}")
            if name == ".env" or name.endswith((".pem", ".key", ".p12", ".pfx", ".dump", ".log")):
                raise ValueError(f"Unexpected private or generated file in frontend: {relative}")
            checked_copy(path, target / relative)


def copy_ops(source, target):
    for relative in OPS_FILES:
        checked_copy(source / relative, target / relative)
    for directory in ("frontend/assets", "public-legal"):
        root = source / directory
        if not root.is_dir():
            raise ValueError(f"Required reviewed deployment directory missing: {directory}")
        for path in files(root):
            relative = path.relative_to(root)
            if any(part.startswith(".") or part == "backups" for part in relative.parts):
                raise ValueError(f"Unexpected hidden/private deployment file: {directory}/{relative}")
            checked_copy(path, target / directory / relative)
    shutil.copytree(RELEASE_DIR, target / "release", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(RELEASE_DIR / "templates/env.example", target / ".env.example")
    shutil.copy2(RELEASE_DIR / "templates/DEPLOYMENT.md", target / "README.md")
    (target / ".gitignore").write_text(".env\nbackups/\nsource-dist/\n.build/\nnetwork-info/maintenance.flag\n__pycache__/\n*.pyc\n*.dump\n", encoding="utf-8")


def prepare_backend(backend):
    """Remove identified third-party material without republishing it in a diff."""
    preparation = json.loads((RELEASE_DIR / "patches/backend-license-preparation.json").read_text())
    if preparation["upstream_commit"] != BACKEND_COMMIT:
        raise ValueError("Backend exclusions target a different upstream commit")
    operations = preparation["operations"]
    changes = []
    for operation in operations:
        relative = operation["path"]
        path = backend / relative
        if sha256(path) != operation["upstream_sha256"]:
            raise ValueError(f"Backend exclusion baseline changed: {relative}")
        action = operation["action"]
        if action == "replace_with_empty_json_array":
            path.write_text("[]\n", encoding="utf-8")
        elif action == "delete_file":
            path.unlink()
        elif action == "remove_test_block":
            text = path.read_text(encoding="utf-8")
            start = text.index(operation["start_marker"])
            stop = text.index(operation["next_test_marker"], start)
            if hashlib.sha256(text[start:stop].encode()).hexdigest() != operation["removed_block_sha256"]:
                raise ValueError("Restricted-fixture test block changed")
            replacement = (
                "      # ColossusX modification, 2026-09-21: omitted the restricted issue 4758 fixture test\n"
                "      # and its embedded bytecode. See LICENSE-PREPARATION.md at the backend root.\n\n"
            )
            path.write_text(
                "# Modified for ColossusX on 2026-09-21: restricted third-party fixture test excluded.\n"
                + text[:start] + replacement + text[stop:], encoding="utf-8"
            )
        else:
            raise ValueError(f"Unknown source exclusion action: {action}")
        changes.append({"path": relative, "upstream_sha256": operation["upstream_sha256"], "modified_sha256": sha256(path) if path.exists() else None, "modification_date": DATE, "reason": operation["reason"]})
    changes.extend(apply_backend_english(backend))
    changes.extend(apply_backend_rewards(backend))
    shutil.copy2(RELEASE_DIR / "templates/LICENSE-PREPARATION.md", backend / "LICENSE-PREPARATION.md")
    ace_notice = backend / "apps/block_scout_web/assets/js/lib/ace/LICENSE"
    shutil.copy2(RELEASE_DIR / "templates/ACE-BSD3-LICENSE.txt", ace_notice)
    changes.append({"path": ace_notice.relative_to(backend).as_posix(), "upstream_sha256": None, "modified_sha256": sha256(ace_notice), "modification_date": DATE, "reason": "Restore BSD 3-Clause notice from the exact upstream Ace v1.4.14 release for vendored minified files."})
    for source_name, target_name in (
        ("Dockerfile", "Dockerfile.colossusx"),
        ("build-from-source.sh", "build-colossusx.sh"),
        ("SOURCE-README.md", "COLOSSUSX_BUILD.md"),
        ("REWARDS.md", "COLOSSUSX_REWARDS.md"),
    ):
        target = backend / target_name
        checked_copy(RELEASE_DIR.parent / "backend" / source_name, target)
        changes.append({"path": target_name, "upstream_sha256": None, "modified_sha256": sha256(target), "modification_date": DATE, "reason": "Add reproducible ColossusX backend build instructions, bounded compiler concurrency and image source provenance."})
    (backend / "build-colossusx.sh").chmod(0o755)
    shutil.copytree(RELEASE_DIR / "patches", backend / "colossusx/patches")
    (backend / "COLOSSUSX-SOURCE-PROVENANCE.json").write_text(
        json.dumps({"prepared_on": DATE, "upstream_version": BACKEND_VERSION, "upstream_commit": BACKEND_COMMIT, "license": "GPL-3.0-only", "changes": changes}, indent=2) + "\n",
        encoding="utf-8",
    )
    return changes


def apply_backend_english(backend):
    patch = RELEASE_DIR / "patches/backend-english.patch"
    if sha256(patch) != BACKEND_ENGLISH_PATCH_SHA256:
        raise ValueError("The reviewed backend English patch has changed")
    for relative, expected_hash in BACKEND_ENGLISH_FILES.items():
        if sha256(backend / relative) != expected_hash:
            raise ValueError(f"Backend English-edit baseline changed: {relative}")
    subprocess.run(
        ["patch", "--batch", "--forward", "--fuzz=0", "--strip=1", "--directory", str(backend), "--input", str(patch)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    changes = []
    for relative, original_hash in BACKEND_ENGLISH_FILES.items():
        path = backend / relative
        reason = (
            "Replace the Japanese Unicode fixture with English text plus an emoji, preserving the UTF-8 byte-length case."
            if relative.endswith("_test.exs") else "Use the English Wei Dai link label in documentation."
        )
        path.write_text(f"# Modified for ColossusX on {DATE}: {reason}\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
        changes.append({"path": relative, "upstream_sha256": original_hash, "modified_sha256": sha256(path), "modification_date": DATE, "reason": reason})
    return changes



def apply_backend_rewards(backend):
    metadata = json.loads((RELEASE_DIR / "patches/backend-colossusx-rewards.json").read_text())
    patch = RELEASE_DIR / "patches/backend-colossusx-rewards.patch"
    if metadata["upstream_commit"] != BACKEND_COMMIT or sha256(patch) != metadata["patch_sha256"]:
        raise ValueError("The reviewed ColossusX reward patch has changed")
    for change in metadata["changes"]:
        path = backend / change["path"]
        actual = sha256(path) if path.exists() else None
        if actual != change["upstream_sha256"]:
            raise ValueError(f"Reward patch baseline changed: {change['path']}")
    subprocess.run(
        ["patch", "--batch", "--forward", "--fuzz=0", "--strip=1", "--directory", str(backend), "--input", str(patch)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    for change in metadata["changes"]:
        if sha256(backend / change["path"]) != change["modified_sha256"]:
            raise ValueError(f"Reward patch result differs: {change['path']}")
    return metadata["changes"]


def json_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from json_strings(item)


def check_source_licenses(path, relative):
    text = path.read_text(encoding="utf-8", errors="replace")
    texts = [text]
    if path.suffix == ".json":
        try:
            # Decode embedded contract sources rather than just looking at a
            # JSON file's own header. This catches escaped SPDX declarations.
            texts.extend(json_strings(json.loads(text)))
        except json.JSONDecodeError:
            pass
    for source in texts:
        for match in SPDX_PATTERN.finditer(source):
            expression = match.group(1).strip().rstrip(" */")
            identifiers = set(re.findall(r"[A-Za-z0-9][A-Za-z0-9.+-]*", expression)) - {"AND", "OR", "WITH"}
            unreviewed = identifiers - REVIEWED_SPDX
            if unreviewed:
                raise ValueError(f"Restricted or unreviewed SPDX declaration in {relative}: {', '.join(sorted(unreviewed))}")


def scan_local_material(root):
    for path in files(root):
        relative = path.relative_to(root)
        if path.name in {".env", "maintenance.flag"} or ".git" in relative.parts or "backups" in relative.parts:
            raise ValueError(f"Private/generated path in release: {relative}")
        if SECRET_PATTERN.search(path.read_bytes()):
            raise ValueError(f"Credential-like material found in: {relative}")
        check_source_licenses(path, relative)
        if path.name in {"backend.env", "frontend.env"}:
            for line in path.read_text(encoding="utf-8").splitlines():
                key, separator, value = line.partition("=")
                if separator and re.search(r"(?:PASSWORD|SECRET|SECRET_KEY_BASE|PRIVATE_KEY|API_KEY|ACCESS_TOKEN|AUTH_TOKEN)$", key.strip()):
                    if value.strip().strip("\"'") not in {"", "false", "null"}:
                        raise ValueError(f"Nonempty credential setting in: {relative} ({key.strip()})")
                if separator and re.search(r"://[^/\s:@]+:[^/\s@]+@", value):
                    raise ValueError(f"Credential-bearing URL in: {relative} ({key.strip()})")


def validate_artwork(root):
    """Keep the chosen CC0 terms and verify source/deployment artwork agree."""
    source = root / "frontend/public/static/colossusx"
    deployed = root / "deployment/frontend/assets"
    if "SPDX-License-Identifier: CC0-1.0" not in (source / "LICENSE").read_text():
        raise ValueError("The custom artwork CC0 license is missing")
    if (source / "LICENSE").read_bytes() != (deployed / "LICENSE").read_bytes():
        raise ValueError("Source and deployment artwork licenses differ")
    for path in files(deployed):
        if path.suffix.lower() in ARTWORK_EXTENSIONS:
            counterpart = source / path.relative_to(deployed)
            if not counterpart.is_file() or sha256(path) != sha256(counterpart):
                raise ValueError(f"Source/deployment artwork mismatch: {path.name}")
    image_hashes = {sha256(path) for path in files(source) if path.suffix.lower() in ARTWORK_EXTENSIONS}
    for name in ("logo.png", "favicon.ico", "apple-touch-icon.png"):
        if sha256(root / "deployment/network-info" / name) not in image_hashes:
            raise ValueError(f"Network-info artwork differs from the source assets: {name}")
    cc0 = root / "deployment/public-legal/CC0-1.0.txt"
    if "CC0 1.0 Universal" not in cc0.read_text():
        raise ValueError("The full CC0 text is missing")
    checked_copy(cc0, root / "licenses/CC0-1.0.txt")


def frontend_changes(frontend, baseline):
    result = []
    paths = {path.relative_to(frontend) for path in files(frontend)} | {path.relative_to(baseline) for path in files(baseline)}
    for relative in sorted(paths):
        current, original = frontend / relative, baseline / relative
        current_hash = sha256(current) if current.is_file() else None
        original_hash = sha256(original) if original.is_file() else None
        if current_hash != original_hash:
            result.append({"path": relative.as_posix(), "upstream_sha256": original_hash, "modified_sha256": current_hash, "modification_date": DATE})
    return result


def assemble(args):
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Output already exists; choose a new directory (nothing is overwritten)")
    for input_dir in (args.frontend_source, args.deployment_source):
        if output.is_relative_to(input_dir.resolve()):
            raise ValueError("Output must not be inside a copied source directory")
    if sha256(args.frontend_archive) != FRONTEND_ARCHIVE_SHA256:
        raise ValueError(f"The frontend upstream archive does not match pinned v{FRONTEND_VERSION}")
    if sha256(args.frontend_source / "LICENSE") != FRONTEND_LICENSE_SHA256:
        raise ValueError("The frontend GPL license was changed or removed")
    # Upstream package.json versions do not reliably identify release tags;
    # the archive checksum identifies this pinned release.
    for required in ("package.json", "yarn.lock", "next.config.js", "deploy/scripts/entrypoint.sh"):
        if not (args.frontend_source / required).is_file():
            raise ValueError(f"Incomplete frontend source: missing {required}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".colossusx-release-", dir=output.parent))
    try:
        with tempfile.TemporaryDirectory(prefix="colossusx-upstream-") as work_name:
            work = Path(work_name)
            backend_archive = work / "backend.tar"
            with backend_archive.open("wb") as handle:
                subprocess.run(["git", "-C", str(args.backend_repository), "archive", "--format=tar", BACKEND_COMMIT], stdout=handle, check=True)
            safe_extract(backend_archive, stage / "backend")
            backend_license = stage / "backend/LICENSE"
            if "GNU GENERAL PUBLIC LICENSE" not in backend_license.read_text() or "Version 3" not in backend_license.read_text():
                raise ValueError("Pinned backend does not contain the expected GPLv3 license")
            backend_changes = prepare_backend(stage / "backend")
            safe_extract(args.frontend_archive, work / "frontend-baseline")
            baseline = work / f"frontend-baseline/frontend-{FRONTEND_VERSION}"
            copy_frontend(args.frontend_source, stage / "frontend", baseline)
            copy_ops(args.deployment_source, stage / "deployment")
            validate_artwork(stage)
            (stage / "licenses").mkdir(exist_ok=True)
            for name in ("README.md", "NOTICE.md", "MODIFICATIONS.md", "THIRD_PARTY.md", ".gitignore"):
                shutil.copy2(RELEASE_DIR / "templates" / name, stage / name)
            shutil.copy2(backend_license, stage / "LICENSE")
            shutil.copy2(backend_license, stage / "licenses/GPL-3.0.txt")
            shutil.copytree(RELEASE_DIR / "patches", stage / "patches")
            backend_runtime_note = (
                "The selected backend build uses this prepared source, including its recorded exclusions and English edits. "
                "Image provenance and separately fetched dependency sources/notices must accompany binary redistribution."
                if args.backend_runtime_source == "prepared" else
                "The selected backend image uses the unmodified upstream source. This prepared source excludes third-party "
                "fixtures and Arbitrum metadata and is not byte-for-byte corresponding source for that image."
            )
            provenance = {
                "prepared_on": DATE,
                "publication_status": "prepared-source",
                "backend": {"version": BACKEND_VERSION, "repository": "https://github.com/blockscout/blockscout", "commit": BACKEND_COMMIT, "license": "GPL-3.0-only", "changes_applied": True, "changes": backend_changes, "runtime_source": args.backend_runtime_source, "runtime_note": backend_runtime_note},
                "frontend": {"version": FRONTEND_VERSION, "repository": "https://github.com/blockscout/frontend", "upstream_archive_sha256": FRONTEND_ARCHIVE_SHA256, "license": "GPL-3.0-only", "changes": frontend_changes(stage / "frontend", baseline)},
                "not_included": ["Backend 11.3.1 working tree or Git history", "Production .env", "Database volumes and backups", "Private keys and certificates", "node_modules and build outputs", "Container images", "Private commercial-license inquiry"],
            }
            (stage / "SOURCE-PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        scan_local_material(stage)
        hashes = [f"{sha256(path)}  {path.relative_to(stage).as_posix()}" for path in files(stage)]
        (stage / "SHA256SUMS").write_text("\n".join(hashes) + "\n", encoding="utf-8")
        stage.rename(output)
    except BaseException:
        shutil.rmtree(stage)
        raise
    print(f"Prepared independent source tree: {output}")
    print("No production service, source checkout, Git history, or remote repository was changed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend-source", type=Path, required=True, help=f"Clean full modified frontend v{FRONTEND_VERSION} source")
    parser.add_argument("--frontend-archive", type=Path, required=True, help=f"Original SHA-256 pinned frontend v{FRONTEND_VERSION} .tar.gz")
    parser.add_argument("--backend-repository", type=Path, default=RELEASE_DIR.parents[2])
    parser.add_argument("--backend-runtime-source", choices=("upstream", "prepared"), default="upstream", help="Whether the selected backend image was built from upstream or this prepared source")
    parser.add_argument("--deployment-source", type=Path, default=RELEASE_DIR.parent)
    parser.add_argument("--output", type=Path, default=RELEASE_DIR.parents[2] / "public-release/colossusx")
    args = parser.parse_args()
    try:
        assemble(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Assembly stopped: {error}\n")


if __name__ == "__main__":
    main()
