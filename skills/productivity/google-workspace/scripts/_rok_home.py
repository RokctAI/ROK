"""Resolve ROK_HOME for standalone skill scripts.

Skill scripts may run outside the Rok process (e.g. system Python,
nix env, CI) where ``rok_constants`` is not importable.  This module
provides the same ``get_rok_home()`` and ``display_rok_home()``
contracts as ``rok_constants`` without requiring it on ``sys.path``.

When ``rok_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``rok_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``ROK_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from rok_constants import display_rok_home as display_rok_home
    from rok_constants import get_rok_home as get_rok_home
except (ModuleNotFoundError, ImportError):

    def get_rok_home() -> Path:
        """Return the Rok home directory (default: ~/.rok).

        Mirrors ``rok_constants.get_rok_home()``."""
        val = os.environ.get("ROK_HOME", "").strip()
        return Path(val) if val else Path.home() / ".rok"

    def display_rok_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``rok_constants.display_rok_home()``."""
        home = get_rok_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
