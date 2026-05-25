"""Regression tests for _apply_profile_override ROK_HOME guard (issue #22502).

When ROK_HOME is set to the rok root (e.g. systemd hardcodes
ROK_HOME=/root/.rok), _apply_profile_override must still read
active_profile and update ROK_HOME to the profile directory.

When ROK_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _run_apply_profile_override(
    tmp_path, monkeypatch, *, rok_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["ROK_HOME"] after the call,
    or None if unset.
    """
    rok_root = tmp_path / ".rok"
    rok_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (rok_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (rok_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if rok_home is not None:
        monkeypatch.setenv("ROK_HOME", rok_home)
    else:
        monkeypatch.delenv("ROK_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["rok", "gateway", "start"])

    from rok_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("ROK_HOME")


class TestApplyProfileOverrideRokHomeGuard:
    """Regression guard for issue #22502.

    Verifies that ROK_HOME pointing to the rok root does NOT suppress
    the active_profile check, while ROK_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_rok_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """ROK_HOME=/root/.rok + active_profile=coder must redirect
        ROK_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets ROK_HOME to the rok root
        and the user switches to a profile via `rok profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        rok_root = tmp_path / ".rok"
        rok_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            rok_home=str(rok_root),
            active_profile="coder",
        )

        assert result is not None, "ROK_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected ROK_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected ROK_HOME to end with 'coder', got: {result!r}"
        )

    def test_rok_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """ROK_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with ROK_HOME already set to a specific profile must stay in that
        profile.
        """
        rok_root = tmp_path / ".rok"
        profile_dir = rok_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (rok_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("ROK_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["rok", "gateway", "start"])

        from rok_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ROK_HOME") == str(profile_dir), (
            "ROK_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_rok_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: ROK_HOME unset + active_profile=coder must set
        ROK_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            rok_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_rok_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect ROK_HOME."""
        rok_root = tmp_path / ".rok"
        rok_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("ROK_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["rok", "gateway", "start"])
        (rok_root / "active_profile").write_text("default")

        from rok_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("ROK_HOME") is None
