"""Bounded AIO-053 package-surface validation with explicit targets only."""

from __future__ import annotations

import importlib
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
MODULE = ROOT / "engineering_orchestration" / "local_operational_trust.py"
MODULE_NAME = "engineering_orchestration.local_operational_trust"


class LocalOperationalTrustPackagingTests(unittest.TestCase):
    def test_explicit_package_configuration_contains_aio053_module(self) -> None:
        configuration = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        packages = configuration["tool"]["setuptools"]["packages"]

        self.assertIn("engineering_orchestration", packages)
        self.assertTrue(MODULE.is_file())

    def test_exact_aio053_module_imports_from_expected_source(self) -> None:
        module = importlib.import_module(MODULE_NAME)

        self.assertEqual(Path(module.__file__).resolve(), MODULE.resolve())
        self.assertEqual(module.__all__, ("LocalOperationalTrustCoordinator",))


if __name__ == "__main__":
    unittest.main()
