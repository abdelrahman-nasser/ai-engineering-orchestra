#!/usr/bin/env python3
"""Compatibility delegate to itru.workflow_catalog."""

import sys
from pathlib import Path

# Only the tool checkout is bootstrapped for direct source-script execution.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from itru import workflow_catalog as _implementation
sys.modules[__name__] = _implementation
