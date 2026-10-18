#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Reset this checkout's ColossusX explorer after the chain has been reinitialized.
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "$0")" && pwd -P)
command -v python3 >/dev/null || { echo "Python 3 is required." >&2; exit 1; }
exec python3 - "$script_dir" "$@" <<'PY'
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen

root = Path(sys.argv[1])
parser = argparse.ArgumentParser(
    prog=str(root / "reset-explorer.sh"),
    description="Delete ColossusX explorer databases/cache and restart with the existing images and settings. Run after restarting the chain. No backup is created.",
)
parser.add_argument("--check", action="store_true", help="Validate prerequisites and RPC only; do not stop services, delete data, or change configuration.")
args = parser.parse_args(sys.argv[2:])
deploy = root / "deploy" / "colossusx"
project = "colossusx"
services = {"db", "redis", "backend", "stats-db", "stats", "frontend", "proxy"}
data_mounts = {
    "db": ("db-data", "/var/lib/postgresql/data"),
    "stats-db": ("stats-db-data", "/var/lib/postgresql/data"),
    "redis": ("redis-data", "/data"),
    "backend": ("backend-dets", "/app/dets"),
}
volume_names = {logical: f"{project}_{logical}" for logical, _ in data_mounts.values()}
compose = ["docker", "compose", "--project-directory", str(deploy), "--env-file", str(deploy / ".env"),
           "--project-name", project, "-f", str(deploy / "compose.yml"), "-f", str(deploy / "compose.override.yml")]
backend_file = deploy / "backend.env"
pin_pattern = rb"(?m)^COLOSSUSX_REWARDS_GENESIS_HASH=([^\r\n]*)"
phase = "preflight (existing services/data have not been changed)"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(command, label, timeout=60):
    # Compose configuration includes secrets: keep command output in memory.
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    require(result.returncode == 0, f"{label} failed (exit {result.returncode}).")
    return result.stdout


def docker_json(arguments, label):
    return json.loads(run(["docker", *arguments], label))


def config(*options):
    return json.loads(run([*compose, "config", "--format", "json", *options], "Compose validation"))


def unchanged_configuration():
    require(all(path.read_bytes() == content for path, content in configuration.items()),
            "Deployment configuration changed during reset; inspect it before rerunning.")


def project_objects(kind):
    arguments = ["ps", "-aq"] if kind == "containers" else [kind, "ls", "-q"]
    return run(["docker", *arguments, "--filter", f"label=com.docker.compose.project={project}"], f"List {kind}").split()


def rpc(method, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for attempt in range(3):
        try:
            request = Request(rpc_url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "ColossusX reset"})
            with urlopen(request, timeout=20) as response:
                value = json.load(response)
            require(isinstance(value, dict) and value.get("jsonrpc") == "2.0" and value.get("id") == 1
                    and "error" not in value and value.get("result") is not None, f"Invalid RPC response for {method}.")
            return value["result"]
        except (OSError, ValueError, RuntimeError):
            if attempt == 2:
                raise RuntimeError(f"RPC {method} failed; verify that the initialized network is ready.") from None
            time.sleep(2)


def quantity(value):
    require(isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]+", value), "Invalid RPC quantity.")
    return int(value, 16)


def network_identity():
    require(quantity(rpc("eth_chainId", [])) == expected_chain_id, "RPC chain ID does not match the configured ColossusX chain ID.")
    genesis = rpc("eth_getBlockByNumber", ["0x0", False])
    require(isinstance(genesis, dict) and quantity(genesis.get("number")) == 0, "Invalid genesis block.")
    value = genesis.get("hash")
    require(isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", value), "Invalid genesis hash.")
    header = rpc("eth_getHeaderByHash", [value])
    require(isinstance(header, dict) and str(header.get("hash", "")).lower() == value.lower()
            and quantity(header.get("number")) == 0, "The genesis header does not match the block.")
    return value.lower(), quantity(rpc("eth_blockNumber", []))


def update_genesis(value):
    require(backend_file.read_bytes() == original_backend, "backend.env changed during reset; inspect it before rerunning.")
    updated = re.sub(pin_pattern, b"COLOSSUSX_REWARDS_GENESIS_HASH=" + value.encode(), original_backend)
    if updated == original_backend:
        return
    metadata = backend_file.stat()
    fd, name = tempfile.mkstemp(prefix=".backend.env.reset-", dir=deploy)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
            os.fchmod(handle.fileno(), stat.S_IMODE(metadata.st_mode))
            if os.geteuid() == 0:
                os.fchown(handle.fileno(), metadata.st_uid, metadata.st_gid)
        os.replace(name, backend_file)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def wait_for_api():
    deadline = time.monotonic() + 600
    next_notice = 0
    while time.monotonic() < deadline:
        try:
            with urlopen("http://127.0.0.1:18080/api/v2/main-page/indexing-status", timeout=5) as response:
                status = json.load(response)
            require(isinstance(status, dict) and isinstance(status.get("finished_indexing"), bool), "Indexing status is not ready.")
            with urlopen("http://127.0.0.1:18080/", timeout=5) as response:
                require(response.status == 200, "Frontend is not ready.")
            with urlopen("http://127.0.0.1:18080/api/v2/main-page/blocks", timeout=5) as response:
                blocks = json.load(response)
            require(isinstance(blocks, list) and blocks and isinstance(blocks[0], dict), "Waiting for the first indexed block.")
            block = blocks[0]
            block_hash, block_height = block.get("hash"), block.get("height")
            require(isinstance(block_hash, str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", block_hash), "Waiting for a valid indexed block hash.")
            require(type(block_height) is int and block_height >= 0, "Waiting for a valid indexed block height.")
            canonical = rpc("eth_getBlockByNumber", [hex(block_height), False])
            require(isinstance(canonical, dict) and str(canonical.get("hash", "")).lower() == block_hash.lower(), "Indexed block does not match the RPC.")
            containers = project_objects("containers")
            inspected = docker_json(["inspect", *containers], "Check service state") if containers else []
            running = {c["Config"]["Labels"].get("com.docker.compose.service") for c in inspected
                       if c["State"]["Status"] == "running" and not c["State"]["OOMKilled"]
                       and c["State"].get("Health", {}).get("Status", "healthy") == "healthy"}
            if running == services:
                return status
        except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired):
            pass
        if time.monotonic() >= next_notice:
            print("Waiting for database migrations and the explorer API...", flush=True)
            next_notice = time.monotonic() + 30
        time.sleep(5)
    raise RuntimeError("Startup timed out after 10 minutes. Services were left running; check their logs before retrying. Rerunning this script deletes their data again.")


try:
    require(shutil.which("docker") is not None, "Docker is required.")
    input_names = (".env", "backend.env", "frontend.env", "compose.yml", "compose.override.yml")
    for name in input_names:
        require((deploy / name).is_file(), f"Missing deployment file: {name}.")
    require(not backend_file.is_symlink(), "backend.env must be a regular file, not a symlink.")
    state_dir = root / ".colossusx-build"
    state_dir.mkdir(exist_ok=True)
    lock = open(state_dir / "reset-explorer.lock", "a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError("Another explorer reset/check is already running.") from None

    configuration = {deploy / name: (deploy / name).read_bytes() for name in input_names}
    print("Checking ColossusX deployment and RPC before any data deletion...", flush=True)
    run(["docker", "info", "--format", "{{.ServerVersion}}"], "Docker access (use sudo if required)")
    current = config()
    require(current.get("name") == project and set(current["services"]) == services, "Unexpected Compose project or services; refusing to reset.")
    require(set(current.get("volumes", {})) == set(volume_names), "Unexpected data volumes; refusing to reset.")
    for logical, name in volume_names.items():
        definition = current["volumes"][logical]
        require(definition.get("name") == name and not definition.get("external") and not definition.get("driver_opts")
                and definition.get("driver", "local") == "local", f"Unexpected volume definition: {logical}.")
    for service, definition in current["services"].items():
        mounts = [(v.get("source"), v.get("target")) for v in definition.get("volumes", []) if v["type"] == "volume"]
        require(mounts == ([data_mounts[service]] if service in data_mounts else []), f"Unexpected persistent mount for {service}.")
    # Both flags are needed to keep env_file values unexpanded on Compose 2.40.
    raw = config("--no-env-resolution", "--no-interpolate")
    raw_backend = raw["services"]["backend"]
    explicit_env = raw_backend.get("environment", {})
    explicit_names = set(explicit_env) if isinstance(explicit_env, dict) else {entry.split("=", 1)[0] for entry in explicit_env}
    require("COLOSSUSX_REWARDS_GENESIS_HASH" not in explicit_names and not any("$" in name for name in explicit_names),
            "The genesis pin must come from backend.env, not a Compose environment override.")
    require([entry["path"] if isinstance(entry, dict) else entry for entry in raw_backend.get("env_file", [])] == [str(backend_file)],
            "Expected backend.env as the backend's only service environment file.")
    backend_env = current["services"]["backend"]["environment"]
    expected_chain_id = int(backend_env["CHAIN_ID"])
    require(expected_chain_id == 10101919, "This script targets ColossusX chain ID 10101919.")
    require(backend_env.get("FETCH_REWARDS_WAY") == "colossusx" and backend_env.get("INDEXER_DISABLE_BLOCK_REWARD_FETCHER") == "false", "The native ColossusX reward fetcher must be enabled.")
    require(backend_env.get("APPLICATION_MODE", "all") == "all" and backend_env.get("DISABLE_INDEXER", "false") == "false", "Combined API/indexer mode must be enabled.")
    rpc_url = backend_env["ETHEREUM_JSONRPC_HTTP_URL"]
    require(rpc_url.startswith(("https://", "http://")), "Expected an HTTP(S) RPC URL.")
    original_backend = backend_file.read_bytes()
    require(len(re.findall(pin_pattern, original_backend)) == 1, "Expected exactly one genesis pin in backend.env.")
    images = sorted({service["image"] for service in current["services"].values()})
    run(["docker", "image", "inspect", "--format", "{{.Id}}", *images], "Check existing images (build or pull missing images first)")
    existing = project_objects("containers")
    if existing:
        for container in docker_json(["inspect", *existing], "Check project ownership"):
            require(container["Config"]["Labels"].get("com.docker.compose.project.working_dir") == str(deploy), "The colossusx project belongs to another deployment directory.")
            require(container["Config"]["Labels"].get("com.docker.compose.service") in services, "Unexpected existing project service; refusing to remove it.")
    names = run(["docker", "volume", "ls", "--format", "{{.Name}}"], "List volumes").split()
    for logical, name in volume_names.items():
        if name in names:
            labels = docker_json(["volume", "inspect", name], "Check volume ownership")[0].get("Labels") or {}
            require(labels.get("com.docker.compose.project") == project and labels.get("com.docker.compose.volume") == logical, f"Volume ownership mismatch: {name}.")
    owned = run(["docker", "volume", "ls", "--filter", f"label=com.docker.compose.project={project}", "--format", "{{.Name}}"], "Check project volumes").split()
    require(set(owned) <= set(volume_names.values()), "Unexpected extra project volume; refusing to reset.")
    genesis, height = network_identity()
    unchanged_configuration()
    print(f"RPC verified: chain ID {expected_chain_id}, head #{height}, genesis {genesis}", flush=True)
    if backend_env.get("COLOSSUSX_REWARDS_GENESIS_HASH", "").lower() != genesis:
        print("Reset will refresh the genesis pin; chain ID and other settings are retained.", flush=True)
    if args.check:
        print("Check passed. No services, data, or configuration were changed.")
        sys.exit(0)

    unchanged_configuration()
    phase = "stopping services and deleting explorer data"
    print("Stopping ColossusX and deleting its block DB, stats DB, Redis cache, and backend DETS data...", flush=True)
    run([*compose, "down", "--volumes", "--remove-orphans", "--timeout", "300"], "Stop and delete explorer data", timeout=900)
    require(not project_objects("containers"), "Some explorer containers remain; refusing to start.")
    remaining = run(["docker", "volume", "ls", "--format", "{{.Name}}"], "Verify data deletion").split()
    require(not set(remaining).intersection(volume_names.values()), "Some data volumes remain; refusing to start.")
    phase = "data deleted; preparing the new network"
    require(network_identity()[0] == genesis, "Genesis changed during reset. Explorer remains stopped; wait for a stable network and rerun.")
    unchanged_configuration()
    update_genesis(genesis)
    configuration[backend_file] = backend_file.read_bytes()
    require(config()["services"]["backend"]["environment"]["COLOSSUSX_REWARDS_GENESIS_HASH"].lower() == genesis, "Updated genesis pin was not applied.")
    unchanged_configuration()
    phase = "starting the explorer"
    print("Starting existing images with empty data volumes...", flush=True)
    run([*compose, "up", "-d", "--no-build", "--pull", "never"], "Start explorer", timeout=600)
    wait_for_api()
    require(network_identity()[0] == genesis, "RPC genesis changed during startup; do not treat this reset as complete.")
    print("Explorer restarted and a canonical block was verified. Fresh synchronization continues automatically in the background.")
    print("Open: https://colossusx.make-cph-great-again.community")
    print("Status: curl -fsS http://127.0.0.1:18080/api/v2/main-page/indexing-status")
except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as error:
    # Avoid printing RPC URLs, expanded Compose configuration, or credentials.
    message = str(error) if isinstance(error, RuntimeError) else f"{type(error).__name__}; check deployment prerequisites."
    print(f"Reset failed during {phase}: {message}", file=sys.stderr)
    print(f"Inspect services with: cd {deploy} && docker compose -p colossusx ps", file=sys.stderr)
    sys.exit(1)
except KeyboardInterrupt:
    print(f"Reset interrupted during {phase}. Inspect services before rerunning; a new run deletes explorer data again.", file=sys.stderr)
    sys.exit(130)
PY
