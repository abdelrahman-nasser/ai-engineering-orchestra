#!/usr/bin/env python3
"""ITRU source CLI entry point.

All command routing and domain logic lives in itru/cli.py,
which is intentionally brand-neutral.
"""

from itru.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
