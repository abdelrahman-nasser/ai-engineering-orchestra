#!/usr/bin/env python3
"""Compatibility delegate to engineering_orchestration.verify_repo."""

import sys
from pathlib import Path

# Only the tool checkout is bootstrapped for direct source-script execution.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engineering_orchestration import verify_repo as _implementation
if __name__ == "__main__":
    raise SystemExit(_implementation.main())
else:
    # Preserve legacy imports and patch targets without copying implementations.
    sys.modules[__name__] = _implementation
