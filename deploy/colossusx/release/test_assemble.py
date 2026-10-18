"""Regression checks for publishing deployment templates without local secrets."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("assemble", Path(__file__).with_name("assemble.py"))
assemble = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(assemble)


class DeploymentEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, relative, content=""):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_copy_ops_publishes_templates_and_ignores_local_runtime_files(self):
        source = self.root / "source"
        target = self.root / "output"
        for relative in assemble.OPS_FILES:
            self.write(Path("source") / relative)
        for relative in ("frontend/assets/LICENSE", "public-legal/NOTICE.md"):
            self.write(Path("source") / relative)
        for name in (".env", "backend.env", "frontend.env"):
            self.write(Path("source") / name, "LOCAL_ONLY=must-not-be-published\n")
        for name in ("backend.example.env", "frontend.example.env"):
            self.write(Path("source") / name, "PUBLIC_SETTING=true\nAPI_KEY=\n")
        self.write("release/templates/env.example", "DB_PASSWORD=\nSECRET_KEY_BASE=\n")
        self.write("release/templates/DEPLOYMENT.md", "Initialize local environment files.\n")

        with patch.object(assemble, "RELEASE_DIR", self.root / "release"):
            assemble.copy_ops(source, target)

        assemble.scan_local_material(target)
        for name in (".env", "backend.env", "frontend.env"):
            self.assertFalse((target / name).exists())
        for name in ("backend.example.env", "frontend.example.env"):
            self.assertEqual((target / name).read_bytes(), (source / name).read_bytes())
        self.assertTrue((target / ".env.example").is_file())
        self.assertFalse(any(b"must-not-be-published" in path.read_bytes() for path in assemble.files(target)))

        subprocess.run(["git", "init", "--quiet", str(target)], check=True)
        paths = (".env", ".env.production", "backend.env", "frontend.env", ".env.example",
                 "backend.example.env", "frontend.example.env")
        result = subprocess.run(
            ["git", "-C", str(target), "check-ignore", "--no-index", *paths],
            check=True, capture_output=True, text=True,
        )
        self.assertEqual(set(result.stdout.splitlines()), set(paths[:4]))

    def test_scanner_rejects_runtime_files_even_without_secrets(self):
        for name in (".env", "backend.env", "frontend.env"):
            with self.subTest(name=name):
                path = self.write(name, "PUBLIC_SETTING=true\n")
                with self.assertRaisesRegex(ValueError, "Private/generated path"):
                    assemble.scan_local_material(self.root)
                path.unlink()

    def test_scanner_rejects_credentials_in_each_deployment_template(self):
        for name in ("backend.example.env", "frontend.example.env", ".env.example", "release/templates/env.example",
                     "deployment/backend.example.env", "deployment/frontend.example.env", "deployment/.env.example",
                     "deployment/release/templates/env.example"):
            for setting in ("DB_PASSWORD=synthetic-test-value\n", "SECRET_KEY_BASE=synthetic-test-value\n",
                            "API_KEY=synthetic-test-value\n", "RPC_URL=https://user:synthetic-test-value@example.test\n"):
                with self.subTest(name=name, key=setting.partition("=")[0]):
                    path = self.write(name, setting)
                    with self.assertRaises(ValueError) as error:
                        assemble.scan_local_material(self.root)
                    self.assertNotIn("synthetic-test-value", str(error.exception))
                    path.unlink()

    def test_scanner_accepts_empty_credentials_and_public_settings(self):
        self.write("backend.example.env", "DB_PASSWORD=\nSECRET_KEY_BASE=''\nAPI_KEY=\"\"\nRPC_URL=https://example.test\n")
        assemble.scan_local_material(self.root)


if __name__ == "__main__":
    unittest.main()
