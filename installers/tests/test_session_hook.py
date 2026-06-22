#!/usr/bin/env python3
"""Opt-in SessionStart update-notify hook tests (PR-3, Increment 2).

Covers (offline, network mocked):
  * register/unregister settings.json MERGE — create, idempotent (no duplicate), preserve foreign
    hooks/settings, remove-only-ours (incl. mixed entries), empty-container cleanup, refuse-on-malformed.
  * the hook script itself — cache-first (no network when fresh), network-miss path, silent on
    same-version / unknown-install / MEDSCI_NO_UPDATE_CHECK / network-error; systemMessage format;
    and a subprocess smoke test proving it never reads stdin and emits valid JSON.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

INSTALLERS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(INSTALLERS))
import medsci_txn  # noqa: E402
import update  # noqa: E402

HOOK_SCRIPT = INSTALLERS / "session_update_check.py"

passed = 0
failed = 0


def check(cond: bool, msg: str) -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {msg}")
    else:
        failed += 1
        print(f"  FAIL  {msg}")


def _settings(tmp: Path) -> Path:
    return tmp / ".claude" / "settings.json"


def _read(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _count_ours(p: Path) -> int:
    ss = _read(p).get("hooks", {}).get("SessionStart", [])
    return sum(
        1
        for e in ss
        if isinstance(e, dict)
        for h in (e.get("hooks") or [])
        if isinstance(h, dict) and "session_update_check.py" in (h.get("command") or "")
    )


# ----------------------------------------------------------------- settings merge

def test_settings_merge() -> None:
    print("settings.json register/unregister:")
    with tempfile.TemporaryDirectory(prefix="medsci-hook-") as t:
        tmp = Path(t)
        home = tmp / "state"
        sp = _settings(tmp)

        # S1 create on absent file
        r = update.register_session_hook(home, sp)
        check(r == "enabled", "enable on absent settings.json -> enabled")
        check(sp.is_file(), "settings.json created")
        check(_count_ours(sp) == 1, "exactly one of our hooks present")
        cmd = _read(sp)["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        check("session_update_check.py" in cmd and sys.executable in cmd, "command has interpreter + script path")

        # S2 idempotent
        r = update.register_session_hook(home, sp)
        check(r == "already-enabled" and _count_ours(sp) == 1, "re-enable is idempotent (no duplicate)")

        # S5 disable -> removes, empty cleanup (S7)
        r = update.unregister_session_hook(home, sp)
        check(r == "disabled", "disable -> disabled")
        check("hooks" not in _read(sp), "emptied 'hooks' container removed")
        check(update.unregister_session_hook(home, sp) == "not-enabled", "second disable -> not-enabled")

    with tempfile.TemporaryDirectory(prefix="medsci-hook-") as t:
        tmp = Path(t)
        home = tmp / "state"
        sp = _settings(tmp)
        sp.parent.mkdir(parents=True)
        # S3 preserve foreign settings + foreign hooks
        sp.write_text(json.dumps({
            "model": "some-model",
            "hooks": {
                "PreToolUse": [{"hooks": [{"type": "command", "command": "echo pre"}]}],
                "SessionStart": [{"hooks": [{"type": "command", "command": "echo foreign-start"}]}],
            },
        }), encoding="utf-8")
        update.register_session_hook(home, sp)
        s = _read(sp)
        check(s["model"] == "some-model", "unrelated 'model' setting preserved")
        check(len(s["hooks"]["PreToolUse"]) == 1, "foreign PreToolUse hook preserved")
        cmds = [h["command"] for e in s["hooks"]["SessionStart"] for h in e["hooks"]]
        check("echo foreign-start" in cmds and _count_ours(sp) == 1, "foreign SessionStart hook preserved + ours added")

        # S4 disable preserves foreign
        update.unregister_session_hook(home, sp)
        s = _read(sp)
        check(s["model"] == "some-model" and len(s["hooks"]["PreToolUse"]) == 1, "disable preserves foreign settings/hooks")
        cmds = [h["command"] for e in s["hooks"]["SessionStart"] for h in e["hooks"]]
        check("echo foreign-start" in cmds and _count_ours(sp) == 0, "disable kept foreign SessionStart, removed ours")

    # S6 mixed entry: ours shares an entry with a foreign hook
    with tempfile.TemporaryDirectory(prefix="medsci-hook-") as t:
        tmp = Path(t)
        home = tmp / "state"
        sp = _settings(tmp)
        sp.parent.mkdir(parents=True)
        sp.write_text(json.dumps({"hooks": {"SessionStart": [
            {"hooks": [
                {"type": "command", "command": "echo foreign"},
                {"type": "command", "command": f'"{sys.executable}" "{home / "updater" / "session_update_check.py"}"'},
            ]},
        ]}}), encoding="utf-8")
        r = update.unregister_session_hook(home, sp)
        s = _read(sp)
        remaining = [h["command"] for e in s["hooks"]["SessionStart"] for h in e["hooks"]]
        check(r == "disabled" and remaining == ["echo foreign"], "mixed entry: only ours removed, foreign kept")

    # S8 refuse to clobber malformed settings.json
    with tempfile.TemporaryDirectory(prefix="medsci-hook-") as t:
        tmp = Path(t)
        home = tmp / "state"
        sp = _settings(tmp)
        sp.parent.mkdir(parents=True)
        sp.write_text("[]", encoding="utf-8")  # a JSON array, not an object
        raised = False
        try:
            update.register_session_hook(home, sp)
        except update.UpdateError:
            raised = True
        check(raised and sp.read_text() == "[]", "register refuses + leaves a malformed settings.json untouched")


# ----------------------------------------------------------------- hook script logic

@contextlib.contextmanager
def _state(installed: str | None, cache_tag: str | None):
    """A temp MEDSCI_HOME with an installed version + optional fresh cache; restores env."""
    prev_home = os.environ.get("MEDSCI_HOME")
    prev_no = os.environ.get("MEDSCI_NO_UPDATE_CHECK")
    os.environ.pop("MEDSCI_NO_UPDATE_CHECK", None)
    with tempfile.TemporaryDirectory(prefix="medsci-hookrun-") as t:
        home = Path(t) / "state"
        os.environ["MEDSCI_HOME"] = str(home)
        if installed is not None:
            sd = home / "targets" / "claude"
            sd.mkdir(parents=True)
            (sd / "state.json").write_text(json.dumps({"installed_version": installed}), encoding="utf-8")
        if cache_tag is not None:
            home.mkdir(parents=True, exist_ok=True)
            (home / "update_check.json").write_text(
                json.dumps({"checked_at": time.time(), "latest_tag": cache_tag}), encoding="utf-8")
        try:
            yield home
        finally:
            for k, v in (("MEDSCI_HOME", prev_home), ("MEDSCI_NO_UPDATE_CHECK", prev_no)):
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


def _run_hook_inproc() -> str:
    """Import the hook fresh and run main(), capturing stdout."""
    sys.path.insert(0, str(INSTALLERS))
    import importlib
    mod = importlib.import_module("session_update_check")
    importlib.reload(mod)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.main()
    return buf.getvalue()


def test_hook_logic() -> None:
    print("hook script logic:")
    orig_resolve = update.resolve_latest_tag

    # H1 newer via FRESH CACHE -> message, and NO network (resolve raises if called)
    update.resolve_latest_tag = lambda gj: (_ for _ in ()).throw(AssertionError("network used despite fresh cache"))
    try:
        with _state(installed="1.0.0", cache_tag="v2.0.0"):
            out = _run_hook_inproc()
        ok = '"systemMessage"' in out and "update available" in out and "2.0.0" in out
        check(ok, "fresh cache + newer -> systemMessage, no network")
        check(json.loads(out).get("suppressOutput") is True, "output is a single valid JSON object")
    finally:
        update.resolve_latest_tag = orig_resolve

    # H2 same version -> silent
    with _state(installed="2.0.0", cache_tag="v2.0.0"):
        check(_run_hook_inproc().strip() == "", "same version -> no output")

    # H3 unknown install -> silent
    with _state(installed=None, cache_tag="v2.0.0"):
        check(_run_hook_inproc().strip() == "", "unknown install -> no output")

    # H4 MEDSCI_NO_UPDATE_CHECK -> silent even with newer cache
    with _state(installed="1.0.0", cache_tag="v2.0.0"):
        os.environ["MEDSCI_NO_UPDATE_CHECK"] = "1"
        check(_run_hook_inproc().strip() == "", "MEDSCI_NO_UPDATE_CHECK=1 -> no output")
        os.environ.pop("MEDSCI_NO_UPDATE_CHECK", None)

    # H5 cache miss + network newer -> message + cache stored
    update.resolve_latest_tag = lambda gj: "v3.0.0"
    try:
        with _state(installed="1.0.0", cache_tag=None) as home:
            out = _run_hook_inproc()
            check("3.0.0" in out and "systemMessage" in out, "cache miss + network newer -> message")
            check((home / "update_check.json").is_file(), "network result cached for next time")
    finally:
        update.resolve_latest_tag = orig_resolve

    # H6 cache miss + network error -> silent, no crash
    update.resolve_latest_tag = lambda gj: (_ for _ in ()).throw(update.UpdateError("offline"))
    try:
        with _state(installed="1.0.0", cache_tag=None):
            check(_run_hook_inproc().strip() == "", "cache miss + network error -> silent")
    finally:
        update.resolve_latest_tag = orig_resolve


def test_hook_subprocess_smoke() -> None:
    print("hook script subprocess smoke (no stdin read, valid JSON):")
    with _state(installed="1.0.0", cache_tag="v9.9.9"):
        env = dict(os.environ)
        # stdin is a pipe we never write to: if the hook read stdin it would hang; timeout guards that.
        proc = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            stdin=subprocess.PIPE, capture_output=True, text=True, env=env, timeout=30,
        )
        check(proc.returncode == 0, "exit 0")
        check('"systemMessage"' in proc.stdout and "9.9.9" in proc.stdout, "emits systemMessage for newer version")
        try:
            json.loads(proc.stdout)
            valid = True
        except Exception:
            valid = False
        check(valid, "stdout is a single valid JSON object")


def _all_commands(p: Path) -> list:
    ss = _read(p).get("hooks", {}).get("SessionStart", [])
    return [h.get("command") for e in ss if isinstance(e, dict)
            for h in (e.get("hooks") or []) if isinstance(h, dict)]


def test_matcher_precision() -> None:
    """The matcher must key on the home-anchored script path, not the bare filename, so it never
    touches an unrelated foreign hook nor a hook pointing at a different MEDSCI_HOME."""
    print("matcher precision (no false match on substring / cross-home):")
    with tempfile.TemporaryDirectory(prefix="medsci-hook-") as t:
        tmp = Path(t)
        home = tmp / "state"
        other_home = tmp / "other-state"
        sp = _settings(tmp)
        sp.parent.mkdir(parents=True)
        # Two decoys: (a) a foreign command that merely CONTAINS the bare filename substring;
        # (b) a canonical-format command pointing at a DIFFERENT updater home.
        wrapper = f'"{sys.executable}" "/opt/tools/run_session_update_check.py_wrapper" --foo'
        otherhome = f'"{sys.executable}" "{other_home / "updater" / "session_update_check.py"}"'
        sp.write_text(json.dumps({"hooks": {"SessionStart": [
            {"hooks": [{"type": "command", "command": wrapper}]},
            {"hooks": [{"type": "command", "command": otherhome}]},
        ]}}), encoding="utf-8")

        r = update.register_session_hook(home, sp)
        check(r == "enabled", "enable ADDS ours despite a substring-colliding foreign hook")
        cmds = _all_commands(sp)
        ours = update.session_hook_command(home)
        check(wrapper in cmds and otherhome in cmds and ours in cmds, "both decoys preserved + ours added")

        r = update.unregister_session_hook(home, sp)
        cmds = _all_commands(sp)
        check(r == "disabled", "disable removes ours")
        check(ours not in cmds, "ours removed")
        check(wrapper in cmds and otherhome in cmds, "disable did NOT delete the foreign / other-home hooks")


def test_resolve_latest_tag() -> None:
    print("resolve_latest_tag draft/prerelease guard:")
    check(update.resolve_latest_tag(lambda u: {"tag_name": "v4.7.0", "assets": []}) == "v4.7.0",
          "returns tag with no asset/digest required (works on any OS)")
    for bad, label in (({"tag_name": "v9.9.9", "draft": True}, "draft"),
                       ({"tag_name": "v9.9.9", "prerelease": True}, "prerelease")):
        raised = False
        try:
            update.resolve_latest_tag(lambda u: bad)
        except update.UpdateError:
            raised = True
        check(raised, f"rejects a {label} release")
    raised = False
    try:
        update.resolve_latest_tag(lambda u: {"assets": []})  # no tag_name
    except update.UpdateError:
        raised = True
    check(raised, "rejects a release with no tag_name")

    # The hook must use a short timeout on the (rare) cache-miss network call.
    orig = update._real_get_json
    captured: dict = {}
    update._real_get_json = lambda url, timeout=None: (captured.update(timeout=timeout) or {"tag_name": "v3.0.0"})
    try:
        with _state(installed="1.0.0", cache_tag=None):
            _run_hook_inproc()
        check(captured.get("timeout") == 4, "hook's cache-miss GET uses a 4s timeout")
    finally:
        update._real_get_json = orig


def test_mode_preserved() -> None:
    if os.name == "nt":
        print("settings.json mode preservation: skipped on Windows")
        return
    print("settings.json mode preservation:")
    with tempfile.TemporaryDirectory(prefix="medsci-hook-") as t:
        tmp = Path(t)
        home = tmp / "state"
        sp = _settings(tmp)
        sp.parent.mkdir(parents=True)
        sp.write_text("{}", encoding="utf-8")
        os.chmod(sp, 0o600)
        update.register_session_hook(home, sp)
        check((os.stat(sp).st_mode & 0o777) == 0o600, "0600 preserved across register")
        update.unregister_session_hook(home, sp)
        check((os.stat(sp).st_mode & 0o777) == 0o600, "0600 preserved across unregister")


if __name__ == "__main__":
    test_settings_merge()
    test_matcher_precision()
    test_resolve_latest_tag()
    test_mode_preserved()
    test_hook_logic()
    test_hook_subprocess_smoke()
    print(f"\ntest_session_hook: {passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
