import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import maintenance.gbrain_cli as gbrain_cli
import maintenance.gbrain_sync as gbrain_sync


def test_gbrain_command_uses_bun_for_bun_shebang(monkeypatch):
    monkeypatch.setattr(gbrain_cli, "gbrain_executable", lambda: "/tmp/gbrain")
    monkeypatch.setattr(gbrain_cli, "_requires_bun", lambda path: True)
    monkeypatch.setattr(gbrain_cli, "bun_executable", lambda: "/tmp/bun")

    cmd = gbrain_cli.gbrain_command(["import", "vault", "--no-embed"])

    assert cmd == ["/tmp/bun", "/tmp/gbrain", "import", "vault", "--no-embed"]



def test_run_gbrain_command_skips_when_bun_missing_for_bun_script(monkeypatch):
    monkeypatch.setattr(gbrain_cli, "gbrain_executable", lambda: "/tmp/gbrain")
    monkeypatch.setattr(gbrain_cli, "_requires_bun", lambda path: True)
    monkeypatch.setattr(gbrain_cli, "bun_executable", lambda: None)

    called = {"value": False}

    def fake_run(*args, **kwargs):
        called["value"] = True
        raise AssertionError("subprocess.run should not be called when bun is missing")

    monkeypatch.setattr(gbrain_cli.subprocess, "run", fake_run)

    result = gbrain_cli.run_gbrain_command(["import", "vault", "--no-embed"])

    assert result["ok"] is False
    assert result["skipped"] is True
    assert "bun not found" in result["reason"]
    assert called["value"] is False



def test_sync_forwards_import_command_and_timeout(monkeypatch, tmp_path):
    captured = {}

    def fake_run_gbrain_command(args, *, command_timeout_seconds=None, lock_timeout_seconds=120):
        captured["args"] = args
        captured["command_timeout_seconds"] = command_timeout_seconds
        captured["lock_timeout_seconds"] = lock_timeout_seconds
        return {"ok": True}

    monkeypatch.setattr(gbrain_sync, "run_gbrain_command", fake_run_gbrain_command)

    vault = tmp_path / "vault"
    result = gbrain_sync.sync(str(vault))

    assert result == {"ok": True}
    assert captured["args"] == ["import", str(vault), "--no-embed"]
    assert captured["command_timeout_seconds"] == 300
    assert captured["lock_timeout_seconds"] == 120



def test_gbrain_env_prefixes_bun_dir_once(monkeypatch):
    monkeypatch.setattr(gbrain_cli, "bun_executable", lambda: "/custom/bin/bun")
    monkeypatch.setattr(gbrain_cli.os, "environ", {"PATH": "/usr/bin:/bin"})

    env = gbrain_cli.gbrain_env()

    assert env["PATH"] == "/custom/bin:/usr/bin:/bin"

    monkeypatch.setattr(gbrain_cli.os, "environ", {"PATH": "/custom/bin:/usr/bin:/bin"})
    env = gbrain_cli.gbrain_env()

    assert env["PATH"] == "/custom/bin:/usr/bin:/bin"


def test_gbrain_executable_prefers_local_bin_before_stale_bun_bin(monkeypatch, tmp_path):
    home = tmp_path / "home"
    local_bin = home / ".local" / "bin"
    bun_bin = home / ".bun" / "bin"
    local_bin.mkdir(parents=True)
    bun_bin.mkdir(parents=True)
    (local_bin / "gbrain").write_text("#!/usr/bin/env bun\n", encoding="utf-8")
    (bun_bin / "gbrain").write_text("#!/usr/bin/env bun\n", encoding="utf-8")

    monkeypatch.setattr(gbrain_cli.shutil, "which", lambda name: None)
    monkeypatch.setattr(gbrain_cli.Path, "home", lambda: home)

    assert gbrain_cli.gbrain_executable() == str(local_bin / "gbrain")


def test_gbrain_executable_skips_stale_bun_bin_without_colocated_bun(monkeypatch, tmp_path):
    home = tmp_path / "home"
    bun_bin = home / ".bun" / "bin"
    bun_bin.mkdir(parents=True)
    (bun_bin / "gbrain").write_text("#!/usr/bin/env bun\n", encoding="utf-8")

    monkeypatch.setattr(gbrain_cli.shutil, "which", lambda name: None)
    monkeypatch.setattr(gbrain_cli.Path, "home", lambda: home)

    assert gbrain_cli.gbrain_executable() is None
