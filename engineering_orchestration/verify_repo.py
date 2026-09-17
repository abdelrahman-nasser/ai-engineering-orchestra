#!/usr/bin/env python3
"""Compatibility surface for the unified project verifier.

The active implementation and Check declarations live in
``engineering_orchestration.project_verification`` and the active project's
``.ai/project.yaml`` respectively. No fixed verification battery exists here.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

from engineering_orchestration.project import find_project_root
from engineering_orchestration.project_verification import (
    ProjectVerificationResult,
    VerificationPlan,
    format_verification_output,
    verify_project,
)


PreflightResult = ProjectVerificationResult


def find_repo_root(start_path: Path | None = None) -> Path:
    """Compatibility name for caller-CWD active-project discovery."""

    return find_project_root(start_path)


def run_preflight(
    repo_root: Path | None = None,
    *,
    execute_checks: bool = True,
    before_execute: Callable[[VerificationPlan], None] | None = None,
) -> ProjectVerificationResult:
    """Compatibility delegate to the unified project verification path."""

    root = find_project_root() if repo_root is None else Path(repo_root)
    return verify_project(
        root,
        execute_checks=execute_checks,
        before_execute=before_execute,
    )


def format_preflight_output(result: ProjectVerificationResult) -> str:
    """Compatibility delegate to aggregate verification formatting."""

    return format_verification_output(result)


def main(argv: list[str] | None = None) -> int:
    """Route the compatibility script through the public verify command."""

    from engineering_orchestration.cli import main as cli_main

    arguments = sys.argv[1:] if argv is None else argv
    return cli_main(["verify", *arguments])


if __name__ == "__main__":
    raise SystemExit(main())
