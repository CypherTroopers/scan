#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Exercise reset safety without invoking Docker or making network requests.

Run from the repository root with:
    python3 -m unittest discover -s deploy/colossusx/tests -p 'test_reset_explorer.py' -v
"""

import contextlib
import fcntl
import io
import json
from pathlib import Path
import stat
import tempfile
import types
import unittest
from unittest.mock import patch


REPOSITORY = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY / "reset-explorer.sh"
PROGRAM = compile(
    SCRIPT.read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0],
    str(SCRIPT),
    "exec",
)
OLD_GENESIS = "0x" + "1" * 64
NEW_GENESIS = "0x" + "2" * 64
ROTATED_GENESIS = "0x" + "3" * 64
BLOCK_HASH = "0x" + "4" * 64
SERVICES = ("db", "redis", "backend", "stats-db", "stats", "frontend", "proxy")
MOUNTS = {
    "db": ("db-data", "/var/lib/postgresql/data"),
    "stats-db": ("stats-db-data", "/var/lib/postgresql/data"),
    "redis": ("redis-data", "/data"),
    "backend": ("backend-dets", "/app/dets"),
}
VOLUMES = ["colossusx_" + name for name, _ in MOUNTS.values()]
SECRET = "fixture-secret-never-log"


class JsonResponse(io.BytesIO):
    status = 200

    def __init__(self, value):
        super().__init__(json.dumps(value).encode())


class FakeDeployment:
    """An in-memory Docker daemon and RPC, backed by disposable config files."""

    def __init__(self, root):
        self.root = root
        self.deploy = root / "deploy" / "colossusx"
        self.deploy.mkdir(parents=True)
        self.backend = self.deploy / "backend.env"
        self.backend.write_bytes(
            ("# Preserve comments and CRLF bytes.\r\n"
             "CHAIN_ID=10101919\r\n"
             "ETHEREUM_JSONRPC_HTTP_URL=https://rpc.example.invalid\r\n"
             "FETCH_REWARDS_WAY=colossusx\r\n"
             "INDEXER_DISABLE_BLOCK_REWARD_FETCHER=false\r\n"
             f"COLOSSUSX_REWARDS_GENESIS_HASH={OLD_GENESIS}\r\n"
             "UNCHANGED_SETTING=keep-this-value\r\n").encode()
        )
        self.backend.chmod(0o640)
        for name in (".env", "frontend.env", "compose.yml", "compose.override.yml"):
            (self.deploy / name).write_text(f"# Untouched fixture: {name}\nSECRET={SECRET}\n")
        self.original_files = {p.name: p.read_bytes() for p in self.deploy.iterdir()}
        self.commands = []
        self.events = []
        self.containers = list(SERVICES)
        self.volumes = list(VOLUMES)
        self.clock = 0.0
        self.down_called = False
        self.up_called = False
        self.rpc_unavailable = False
        self.chain_id = 10101919
        self.missing_image = False
        self.extra_config_volume = False
        self.foreign_directory = False
        self.wrong_volume_owner = False
        self.fail_down = False
        self.retain_volume = False
        self.fail_up = False
        self.rotate_after_down = False
        self.race_before_down = False
        self.race_after_down = False
        self.pin_override = False
        self.raw_environment_list = False
        self.extra_env_file = False
        self.indexer_disabled = False
        self.mutated = False
        self.status_responses = []
        self.block_responses = []
        self.api_attempts = 0

    def configuration(self, raw=False):
        env = dict(line.split("=", 1) for line in self.backend.read_text().splitlines()
                   if "=" in line and not line.startswith("#"))
        if self.indexer_disabled:
            env["DISABLE_INDEXER"] = "true"
        service_config = {name: {"image": f"fixture-{name}:1"} for name in SERVICES}
        for name, (source, target) in MOUNTS.items():
            service_config[name]["volumes"] = [{"type": "volume", "source": source, "target": target}]
        service_config["backend"]["environment"] = (
            {"COLOSSUSX_REWARDS_GENESIS_HASH": OLD_GENESIS} if self.pin_override else {}
        ) if raw else env
        if raw:
            service_config["backend"]["env_file"] = [{"path": str(self.backend), "required": True}]
            if self.extra_env_file:
                service_config["backend"]["env_file"].append({"path": str(self.deploy / "unexpected.env"), "required": True})
            if self.raw_environment_list:
                service_config["backend"]["environment"] = [
                    f"{key}={value}" for key, value in service_config["backend"]["environment"].items()
                ]
        volumes = {logical: {"name": "colossusx_" + logical} for logical, _ in MOUNTS.values()}
        if self.extra_config_volume:
            volumes["unrelated"] = {"name": "unrelated"}
        return {"name": "colossusx", "services": service_config, "volumes": volumes}

    def container(self, name):
        return {
            "Config": {"Labels": {
                "com.docker.compose.project": "colossusx",
                "com.docker.compose.project.working_dir": "/foreign/deployment" if self.foreign_directory else str(self.deploy),
                "com.docker.compose.service": name,
            }},
            "State": {"Status": "running", "OOMKilled": False, "Health": {"Status": "healthy"}},
        }

    def run(self, command, **kwargs):
        command = list(command)
        self.commands.append(command)
        self.assert_safe_command(command)
        output = ""
        code = 0
        if command[1] == "compose":
            if "config" in command:
                if "--no-env-resolution" in command and "--no-interpolate" not in command:
                    raise AssertionError("Raw Compose inspection requires both environment flags on Compose 2.40")
                output = json.dumps(self.configuration(raw="--no-env-resolution" in command))
            elif "down" in command:
                self.events.append("down")
                self.down_called = True
                if self.fail_down:
                    code = 1
                    output = SECRET
                else:
                    self.containers = []
                    self.volumes = self.volumes[:1] if self.retain_volume else []
            elif "up" in command:
                self.events.append("up")
                self.up_called = True
                if self.fail_up:
                    code = 1
                else:
                    self.containers = list(SERVICES)
                    self.volumes = list(VOLUMES)
            else:
                raise AssertionError(f"Unexpected Compose command: {command}")
        elif command[1] == "info":
            output = "29.1.3"
        elif command[1:3] == ["image", "inspect"]:
            code = int(self.missing_image)
            output = SECRET if self.missing_image else "sha256:fixture"
        elif command[1] == "ps":
            output = "\n".join(self.containers)
        elif command[1] == "inspect":
            output = json.dumps([self.container(name) for name in command[2:]])
        elif command[1:3] == ["volume", "ls"]:
            if self.down_called and not self.up_called:
                self.events.append("verify_deleted_volumes")
            output = "\n".join(self.volumes)
        elif command[1:3] == ["volume", "inspect"]:
            logical = command[3].removeprefix("colossusx_")
            output = json.dumps([{"Labels": {
                "com.docker.compose.project": "other-project" if self.wrong_volume_owner else "colossusx",
                "com.docker.compose.volume": logical,
            }}])
        else:
            raise AssertionError(f"Unexpected Docker command: {command}")
        return types.SimpleNamespace(returncode=code, stdout=output, stderr=SECRET if code else "")

    def assert_safe_command(self, command):
        if command[0] != "docker":
            raise AssertionError("The script attempted a non-Docker subprocess.")
        if command[1] == "compose":
            for flag, expected in (("--project-name", "colossusx"),
                                   ("--project-directory", str(self.deploy)),
                                   ("--env-file", str(self.deploy / ".env"))):
                if command[command.index(flag) + 1] != expected:
                    raise AssertionError(f"Unexpected {flag} scope")
            files = [command[i + 1] for i, item in enumerate(command) if item == "-f"]
            if files != [str(self.deploy / "compose.yml"), str(self.deploy / "compose.override.yml")]:
                raise AssertionError("Unexpected Compose files")

    def urlopen(self, request, **kwargs):
        if isinstance(request, str):
            if request == "http://127.0.0.1:18080/api/v2/main-page/indexing-status":
                self.api_attempts += 1
                value = self.status_responses.pop(0) if self.status_responses else {"finished_indexing": True}
                return JsonResponse(value)
            if request == "http://127.0.0.1:18080/api/v2/main-page/blocks":
                value = self.block_responses.pop(0) if self.block_responses else [{"height": 1, "hash": BLOCK_HASH}]
                return JsonResponse(value)
            if request == "http://127.0.0.1:18080/":
                return JsonResponse("frontend")
            raise AssertionError(f"Unexpected API request: {request}")
        if request.full_url != "https://rpc.example.invalid":
            raise AssertionError("Unexpected RPC URL")
        if self.rpc_unavailable:
            raise OSError(SECRET)
        payload = json.loads(request.data)
        method, params = payload["method"], payload["params"]
        if not self.mutated and ((self.race_before_down and not self.down_called)
                                or (self.race_after_down and self.down_called)):
            with (self.deploy / "compose.override.yml").open("a") as handle:
                handle.write("# Concurrent operator change\n")
            self.mutated = True
        genesis = ROTATED_GENESIS if self.rotate_after_down and self.down_called else NEW_GENESIS
        if method == "eth_chainId":
            value = hex(self.chain_id)
        elif method == "eth_blockNumber":
            value = "0x1"
        elif method == "eth_getBlockByNumber":
            number = int(params[0], 16)
            value = {"number": hex(number), "hash": genesis if number == 0 else BLOCK_HASH}
        elif method == "eth_getHeaderByHash":
            value = {"number": "0x0", "hash": genesis}
        else:
            raise AssertionError(f"Unexpected RPC method: {method}")
        return JsonResponse({"jsonrpc": "2.0", "id": payload["id"], "result": value})

    def sleep(self, seconds):
        # Failures still hit the script's deadline without waiting in real time.
        self.clock += max(seconds, 60)


class ResetExplorerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="colossusx-reset-test-")
        self.addCleanup(temporary.cleanup)
        self.fake = FakeDeployment(Path(temporary.name))

    def execute(self, *arguments):
        namespace = {"__name__": "__main__"}
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch("sys.argv", ["-", str(self.fake.root), *arguments]))
            stack.enter_context(patch("shutil.which", return_value="/fake/docker"))
            stack.enter_context(patch("subprocess.run", side_effect=self.fake.run))
            stack.enter_context(patch("urllib.request.urlopen", side_effect=self.fake.urlopen))
            stack.enter_context(patch("time.sleep", side_effect=self.fake.sleep))
            stack.enter_context(patch("time.monotonic", side_effect=lambda: self.fake.clock))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            code = 0
            try:
                exec(PROGRAM, namespace)
            except SystemExit as error:
                code = error.code
            finally:
                if "lock" in namespace:
                    namespace["lock"].close()
        output = stdout.getvalue() + stderr.getvalue()
        self.assertNotIn(SECRET, output)
        return code, output

    def assert_preflight_rejected(self):
        code, output = self.execute()
        self.assertEqual(code, 1, output)
        self.assertFalse(self.fake.down_called)
        self.assertFalse(self.fake.up_called)
        self.assertEqual(self.fake.backend.read_bytes(), self.fake.original_files["backend.env"])
        return output

    def test_check_is_non_destructive_even_when_genesis_changed(self):
        code, output = self.execute("--check")
        self.assertEqual(code, 0, output)
        self.assertFalse(self.fake.down_called)
        self.assertFalse(self.fake.up_called)
        self.assertEqual(self.fake.volumes, VOLUMES)
        for name, content in self.fake.original_files.items():
            self.assertEqual((self.fake.deploy / name).read_bytes(), content)

    def test_reset_preserves_other_settings_and_file_metadata(self):
        before = self.fake.backend.stat()
        code, output = self.execute()
        self.assertEqual(code, 0, output)
        self.assertLess(self.fake.events.index("down"), self.fake.events.index("verify_deleted_volumes"))
        self.assertLess(self.fake.events.index("verify_deleted_volumes"), self.fake.events.index("up"))
        expected = self.fake.original_files["backend.env"].replace(OLD_GENESIS.encode(), NEW_GENESIS.encode())
        self.assertEqual(self.fake.backend.read_bytes(), expected)
        for name, content in self.fake.original_files.items():
            if name != "backend.env":
                self.assertEqual((self.fake.deploy / name).read_bytes(), content)
        after = self.fake.backend.stat()
        self.assertEqual(stat.S_IMODE(after.st_mode), stat.S_IMODE(before.st_mode))
        self.assertEqual((after.st_uid, after.st_gid), (before.st_uid, before.st_gid))
        self.assertEqual(list(self.fake.deploy.glob(".backend.env.reset-*")), [])
        down = next(c for c in self.fake.commands if "down" in c)
        up = next(c for c in self.fake.commands if "up" in c)
        self.assertIn("--volumes", down)
        self.assertIn("--no-build", up)
        self.assertEqual(up[up.index("--pull") + 1], "never")
        self.assertNotIn("Synchronization is complete", output)

    def test_repeated_reset_with_unchanged_genesis_succeeds(self):
        code, output = self.execute()
        self.assertEqual(code, 0, output)
        after_first_reset = self.fake.backend.read_bytes()
        code, output = self.execute()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.fake.backend.read_bytes(), after_first_reset)
        self.assertEqual(self.fake.events.count("down"), 2)
        self.assertEqual(self.fake.events.count("up"), 2)

    def test_wrong_chain_id_preserves_existing_data(self):
        self.fake.chain_id = 1
        self.assertIn("chain ID", self.assert_preflight_rejected())

    def test_unavailable_rpc_preserves_existing_data_and_hides_secrets(self):
        self.fake.rpc_unavailable = True
        self.assertIn("RPC", self.assert_preflight_rejected())

    def test_missing_image_preserves_existing_data(self):
        self.fake.missing_image = True
        self.assertIn("images", self.assert_preflight_rejected())

    def test_unexpected_config_volume_rejected(self):
        self.fake.extra_config_volume = True
        self.assertIn("Unexpected data volumes", self.assert_preflight_rejected())

    def test_extra_existing_project_volume_rejected(self):
        self.fake.volumes.append("colossusx_unrelated")
        self.assertIn("extra project volume", self.assert_preflight_rejected())

    def test_foreign_project_directory_rejected(self):
        self.fake.foreign_directory = True
        self.assertIn("another deployment directory", self.assert_preflight_rejected())

    def test_unknown_existing_service_rejected(self):
        self.fake.containers.append("unrelated")
        self.assertIn("Unexpected existing project service", self.assert_preflight_rejected())

    def test_wrong_volume_owner_rejected(self):
        self.fake.wrong_volume_owner = True
        self.assertIn("Volume ownership mismatch", self.assert_preflight_rejected())

    def test_genesis_override_rejected(self):
        self.fake.pin_override = True
        self.assertIn("Compose environment override", self.assert_preflight_rejected())

    def test_genesis_override_in_environment_list_rejected(self):
        self.fake.pin_override = True
        self.fake.raw_environment_list = True
        self.assertIn("Compose environment override", self.assert_preflight_rejected())

    def test_additional_backend_env_file_rejected(self):
        self.fake.extra_env_file = True
        self.assertIn("only service environment file", self.assert_preflight_rejected())

    def test_disabled_indexer_rejected(self):
        self.fake.indexer_disabled = True
        self.assertIn("Combined API/indexer", self.assert_preflight_rejected())

    def test_down_failure_blocks_start_and_pin_update(self):
        self.fake.fail_down = True
        code, output = self.execute()
        self.assertEqual(code, 1, output)
        self.assertTrue(self.fake.down_called)
        self.assertFalse(self.fake.up_called)
        self.assertEqual(self.fake.backend.read_bytes(), self.fake.original_files["backend.env"])

    def test_retained_volume_blocks_start(self):
        self.fake.retain_volume = True
        code, output = self.execute()
        self.assertEqual(code, 1, output)
        self.assertTrue(self.fake.down_called)
        self.assertFalse(self.fake.up_called)
        self.assertIn("Some data volumes remain", output)

    def test_genesis_rotation_after_deletion_blocks_start(self):
        self.fake.rotate_after_down = True
        code, output = self.execute()
        self.assertEqual(code, 1, output)
        self.assertTrue(self.fake.down_called)
        self.assertFalse(self.fake.up_called)
        self.assertEqual(self.fake.backend.read_bytes(), self.fake.original_files["backend.env"])
        self.assertIn("Genesis changed during reset", output)

    def test_config_race_before_deletion_is_rejected(self):
        self.fake.race_before_down = True
        self.assertIn("configuration changed", self.assert_preflight_rejected())

    def test_config_race_after_deletion_blocks_start(self):
        self.fake.race_after_down = True
        code, output = self.execute()
        self.assertEqual(code, 1, output)
        self.assertTrue(self.fake.down_called)
        self.assertFalse(self.fake.up_called)
        self.assertIn("configuration changed", output)

    def test_concurrent_lock_blocks_all_docker_calls(self):
        directory = self.fake.root / ".colossusx-build"
        directory.mkdir()
        with (directory / "reset-explorer.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertIn("already running", self.assert_preflight_rejected())
        self.assertEqual(self.fake.commands, [])

    def test_start_failure_returns_nonzero(self):
        self.fake.fail_up = True
        code, output = self.execute()
        self.assertEqual(code, 1, output)
        self.assertTrue(self.fake.down_called)
        self.assertTrue(self.fake.up_called)
        self.assertNotIn("Explorer restarted", output)

    def test_empty_or_invalid_api_waits_for_canonical_block(self):
        self.fake.status_responses = [[], None, {}, {"finished_indexing": "true"}]
        self.fake.block_responses = [[], None, [{}], [{"height": 1, "hash": ROTATED_GENESIS}]]
        code, output = self.execute()
        self.assertEqual(code, 0, output)
        self.assertGreaterEqual(self.fake.api_attempts, 9)
        self.assertIn("Waiting for database migrations", output)

    def test_empty_database_does_not_count_as_ready(self):
        self.fake.block_responses = [[] for _ in range(20)]
        code, output = self.execute()
        self.assertEqual(code, 1, output)
        self.assertIn("Startup timed out", output)
        self.assertNotIn("Explorer restarted", output)

    def test_invalid_block_height_is_retried(self):
        self.fake.block_responses = [[{"height": None, "hash": BLOCK_HASH}]]
        code, output = self.execute()
        self.assertEqual(code, 0, output)
        self.assertGreaterEqual(self.fake.api_attempts, 2)

    def test_missing_or_invalid_block_hash_is_retried(self):
        self.fake.block_responses = [
            [{"height": 1}],
            [{"height": 1, "hash": None}],
            [{"height": 1, "hash": "0x123"}],
            [{"height": True, "hash": BLOCK_HASH}],
        ]
        code, output = self.execute()
        self.assertEqual(code, 0, output)
        self.assertGreaterEqual(self.fake.api_attempts, 5)


if __name__ == "__main__":
    unittest.main()
