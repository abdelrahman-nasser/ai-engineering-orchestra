#!/usr/bin/env python3
"""Temporary branded CLI entry point.

This is the current command alias for the repository CLI.
The product name 'aio' is a working project codename and may change.

All command routing and domain logic lives in scripts/cli.py,
which is intentionally brand-neutral.
"""

from scripts.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
