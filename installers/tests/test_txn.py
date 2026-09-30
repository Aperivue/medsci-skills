#!/usr/bin/env python3
"""Crash-recovery + transactional-install tests for installers/medsci_txn.py.

Deterministic, network-free, cross-platform (POSIX + Windows). Drives the installer
against synthetic skill sets in temp dirs with MEDSCI_HOME pointed at a temp root, and
injects crashes at every journal phase to prove recovery converges to a consistent state.
Run: python3 installers/tests/test_txn.py
"""
from __future__ import annotations

import errno
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # installers/
import medsci_txn as T  # noqa: E402

PASS = 0
FAIL = 0


def check(label: str, cond: bool) -> None:
    global PASS, FAIL
    if cond:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}")
        FAIL += 1


def _logger():
    return lambda m: None


def make_source(root: Path, skills: dict[str, dict[str, str]], version: str = "1.0.0") -> Path:
    """root/skills/<name>/SKILL.md(+files); root/metadata/distribution_manifest.json with version."""
    sk = root / "skills"
    for name, files in skills.items():
        d = sk / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(files.get("SKILL.md", f"# {name}\n"), encoding="utf-8")
        for fn, body in files.items():
            if fn != "SKILL.md":
                (d / fn).write_text(body, encoding="utf-8")
    import json as _json
    (root / "metadata").mkdir(parents=True, exist_ok=True)
    (root / "metadata" / "distribution_manifest.json").write_text(
        _json.dumps({"schema_version": 1, "version": version, "owned_skills": sorted(skills)}) + "\n",
        encoding="utf-8")
    return sk


def consistent(dest: Path, owned: list[str]) -> bool:
    if (dest / T.TXN_DIRNAME).exists():
        return False
    return all((dest / n / "SKILL.md").is_file() for n in owned)


def install(src, dest, owned, home, **kw):
    return T.install_target(src, dest, "claude", owned, home, _logger(), **kw)


class _Crash(Exception):
    pass


def _v1_then(base: Path, tag: str):
    """A committed v1 install of a,b plus a v2 source; returns (src_v2, dest, home)."""
    src_v1 = make_source(base / f"{tag}_v1", {"a": {"v": "1"}, "b": {"v": "1"}}, "1.0.0")
    src_v2 = make_source(base / f"{tag}_v2", {"a": {"v": "2"}, "b": {"v": "2"}}, "2.0.0")
    home, dest = base / f"{tag}_home", base / f"{tag}_dest"
    os.environ["MEDSCI_HOME"] = str(home)
    T.install_target(src_v1, dest, "claude", ["a", "b"], home, _logger())
    return src_v2, dest, home


def _fail_after_replace(when):
    """Patch os.replace so the call matching `when(src, dst)` completes and THEN raises: a kill
    between two lines, which crash_hook (run only after journal writes) cannot reach. Returns the
    function that undoes the patch."""
    real = T.os.replace

    def fake(src, dst):
        real(src, dst)
        if when(Path(src), Path(dst)):
            raise _Crash()

    T.os.replace = fake
    return lambda: setattr(T.os, "replace", real)


def faults(base: Path) -> None:
    """Fault injection at the points an external review named (transaction safety, #1-#5)."""
    # 9. killed after an old skill was moved aside but before the journal recorded the move. Recovery
    #    must find it in holding and put it back, not delete it along with the holding dir.
    src_v2, dest, home = _v1_then(base, "f9")
    undo = _fail_after_replace(lambda s, d: s == dest / "a" and d.parent.name == "old")
    try:
        install(src_v2, dest, ["a", "b"], home)
    except _Crash:
        pass
    finally:
        undo()
    T.recover_target("claude", home, _logger())
    check("killed between moving an old skill aside and journaling it: recovery restores it",
          consistent(dest, ["a", "b"]) and (dest / "a" / "v").read_text() == "1")

    # 10. a rollback interrupted halfway and then run again must not delete what it already restored.
    src_v2, dest, home = _v1_then(base, "f10")

    def at_first_placement(j):
        if j["phase"] == "new_installed" and len(j["placed_new"]) == 1:
            raise _Crash()

    try:
        install(src_v2, dest, ["a", "b"], home, crash_hook=at_first_placement)
    except _Crash:
        pass
    undo = _fail_after_replace(lambda s, d: d == dest / "a" and s.parent.name == "old")
    try:
        T.recover_target("claude", home, _logger())
    except _Crash:
        pass
    finally:
        undo()
    T.recover_target("claude", home, _logger())
    check("rollback interrupted after restoring one skill, then re-run: both old skills survive",
          consistent(dest, ["a", "b"])
          and [(dest / n / "v").read_text() for n in ("a", "b")] == ["1", "1"])

    # 11. a second install started while the first is mid-transaction must refuse, not "recover"
    #     (roll back) the live transaction underneath it.
    src_v2, dest, home = _v1_then(base, "f11")
    seen: list[str] = []

    def concurrent(j):
        if j["phase"] == "old_moved" and len(j["moved_old"]) == 1 and not seen:
            try:
                install(src_v2, dest, ["a", "b"], home)
                seen.append("ran")
            except T.TxnError:
                seen.append("refused")

    first_ok = True
    try:
        install(src_v2, dest, ["a", "b"], home, crash_hook=concurrent)
    except Exception:  # noqa: BLE001
        first_ok = False
    check("a second install of the same target is refused while the first is running", seen == ["refused"])
    check("...and the first install still completes to v2",
          first_ok and consistent(dest, ["a", "b"]) and (dest / "a" / "v").read_text() == "2")

    # ...but a filesystem that cannot lock at all (ENOLCK) must not stop every install forever.
    real_lock = T._lock_file

    def no_locks(_f, _lock):
        raise OSError(errno.ENOLCK, "No locks available")

    T._lock_file = no_locks
    try:
        install(src_v2, dest, ["a", "b"], home)
        unlockable_ok = consistent(dest, ["a", "b"])
    except Exception:  # noqa: BLE001
        unlockable_ok = False
    finally:
        T._lock_file = real_lock
    check("a filesystem without locking proceeds unlocked, as before", unlockable_ok)

    # 11b. a release that owns no skills (everything installed is pruned), killed right after the
    #      empty manifest is written: recovery must leave dest and manifest agreeing, not restore
    #      the pruned folders beside a manifest that no longer lists them.
    src_v1 = make_source(base / "f11b_v1", {"a": {}, "gone": {}}, "1.0.0")
    home, dest = base / "f11b_home", base / "f11b_dest"
    os.environ["MEDSCI_HOME"] = str(home)
    T.install_target(src_v1, dest, "claude", ["a", "gone"], home, _logger())
    empty = base / "f11b_v2" / "skills"
    undo = _fail_after_replace(lambda s, d: d.name == "installed-manifest.json")
    try:
        T.install_target(empty, dest, "claude", [], home, _logger())
    except _Crash:
        pass
    finally:
        undo()
    T.recover_target("claude", home, _logger())
    listed = sorted(T.read_json_strict(T.target_state_dir("claude", home) / "installed-manifest.json")["skills"])
    on_disk = sorted(p.name for p in dest.iterdir() if p.name != T.TXN_DIRNAME)
    check("empty release killed after its manifest was written: dest and manifest agree after recovery",
          listed == on_disk and not (dest / T.TXN_DIRNAME).exists())

    # 12. a symlink the user added inside an installed skill is a modification: it is backed up, as
    #     a link, before the skill is replaced. A dangling one must not make the backup fail.
    src_v2, dest, home = _v1_then(base, "f12")
    notes = base / "f12_notes.md"
    notes.write_text("my notes", encoding="utf-8")
    linked = False
    if os.name != "posix":
        # Windows symlinks need a privilege, a file/dir flag, and may read back \\?\-prefixed.
        print("  SKIP  symlink cases (POSIX only)")
    else:
        os.symlink(notes, dest / "a" / "notes.md")
        os.symlink(base / "f12_gone", dest / "b" / "dangling")
        linked = True
    if linked:
        try:
            install(src_v2, dest, ["a", "b"], home)
            ok = True
        except Exception:  # noqa: BLE001
            ok = False
        root = home / "backups"
        links = {p.name: os.readlink(p) for p in root.rglob("*") if p.is_symlink()} if root.exists() else {}
        check("a user-added symlink triggers a backup that keeps it as a link",
              ok and links.get("notes.md") == str(notes))
        check("...a dangling one too, without failing the install",
              ok and links.get("dangling") == str(base / "f12_gone") and consistent(dest, ["a", "b"]))

    # 13. atomic_write_bytes: the temp file is created exclusively (a symlink planted at the old
    #     predictable name is not followed) and already has the destination's mode when it replaces it.
    if os.name != "posix":
        print("  SKIP  temp-file mode cases (POSIX modes are not meaningful on this platform)")
        return
    secret = base / "f13_settings.json"
    secret.write_text("{}", encoding="utf-8")
    os.chmod(secret, 0o600)
    victim = base / "f13_victim.txt"
    victim.write_text("VICTIM", encoding="utf-8")
    os.symlink(victim, secret.with_suffix(secret.suffix + f".tmp.{os.getpid()}"))
    modes: list[int] = []
    real = T.os.replace

    def spy(src, dst):
        modes.append(os.stat(src).st_mode & 0o777)
        real(src, dst)

    T.os.replace = spy
    try:
        T.atomic_write_bytes(secret, b'{"token": 1}\n')
    finally:
        T.os.replace = real
    check("the temp file is already 0600, like its destination, before the replace", modes == [0o600])
    check("a symlink planted at a predictable temp name is not followed",
          victim.read_text(encoding="utf-8") == "VICTIM")
    check("destination written, still a regular 0600 file",
          not secret.is_symlink() and secret.read_bytes() == b'{"token": 1}\n'
          and (os.stat(secret).st_mode & 0o777) == 0o600)
    fresh = base / "f13_new.json"
    T.atomic_write_bytes(fresh, b"{}\n")
    mask = os.umask(0)
    os.umask(mask)
    check("a new file gets the ordinary umask mode, not 0600",
          (os.stat(fresh).st_mode & 0o777) == (0o666 & ~mask))


def run():
    with tempfile.TemporaryDirectory(prefix="medsci-txn-") as tmp:
        base = Path(tmp)
        os.environ["MEDSCI_HOME"] = str(base / "state")

        # 1. fresh install
        s1 = make_source(base / "r1", {"a": {"x.txt": "1"}, "b": {}, "c": {}}, "1.0.0")
        d1 = base / "dest1"
        install(s1, d1, ["a", "b", "c"], base / "state")
        man = T.read_json_strict(T.target_state_dir("claude", base / "state") / "installed-manifest.json")
        check("fresh install: dest discoverable", consistent(d1, ["a", "b", "c"]))
        check("fresh install: manifest has inventory", "x.txt" in man["skills"]["a"]["inventory"])
        st = T.read_json_strict(T.target_state_dir("claude", base / "state") / "state.json")
        check("state.json records version", st["installed_version"] == "1.0.0")

        # 2. idempotent re-install (no backup, still consistent)
        install(s1, d1, ["a", "b", "c"], base / "state")
        check("re-install idempotent", consistent(d1, ["a", "b", "c"]))
        check("re-install made no backup", not (base / "state" / "backups").exists())

        # 3. user-edit detection -> permanent backup before update
        (d1 / "a" / "x.txt").write_text("EDITED", encoding="utf-8")
        s1b = make_source(base / "r1b", {"a": {"x.txt": "1"}, "b": {}, "c": {}}, "1.1.0")
        install(s1b, d1, ["a", "b", "c"], base / "state")
        backups = list((base / "state" / "backups").rglob("a/x.txt")) if (base / "state" / "backups").exists() else []
        check("user-edit -> permanent backup made", any(p.read_text() == "EDITED" for p in backups))
        check("user-edit -> dest restored to source", (d1 / "a" / "x.txt").read_text() == "1")

        # 4. prune a removed owned skill
        s2 = make_source(base / "r2", {"a": {}, "b": {}}, "2.0.0")
        install(s2, d1, ["a", "b"], base / "state")
        check("prune: removed skill gone from dest", not (d1 / "c").exists())
        check("prune: kept skills present", consistent(d1, ["a", "b"]))

        # 5. legacy collision (dest skill with no prior manifest)
        d3 = base / "dest3"
        (d3 / "a").mkdir(parents=True)
        (d3 / "a" / "SKILL.md").write_text("HANDMADE", encoding="utf-8")
        # use a different target so prior manifest is empty for it
        T.install_target(s1, d3, "codex", ["a", "b"], base / "state", _logger())
        legacy = list((base / "state" / "backups").rglob("a/SKILL.md"))
        check("legacy collision -> backup of handmade skill", any(p.read_text() == "HANDMADE" for p in legacy))

        # 6. crash at each journal phase -> recovery converges
        # v1 install has both a,b present, so during the v2 update moved_old reaches 2.
        crash_points = [
            ("prepared", 0, 0), ("old_moved", 0, 0), ("old_moved", 1, 0), ("old_moved", 2, 0),
            ("new_installed", 2, 0), ("new_installed", 2, 1), ("committed", 2, 2),
        ]
        for phase, nmoved, nplaced in crash_points:
            src_v1 = make_source(base / f"cv1_{phase}_{nmoved}_{nplaced}", {"a": {"v": "1"}, "b": {}}, "1.0.0")
            src_v2 = make_source(base / f"cv2_{phase}_{nmoved}_{nplaced}", {"a": {"v": "2"}, "b": {}}, "2.0.0")
            home = base / f"home_{phase}_{nmoved}_{nplaced}"
            dest = base / f"cdest_{phase}_{nmoved}_{nplaced}"
            os.environ["MEDSCI_HOME"] = str(home)
            T.install_target(src_v1, dest, "claude", ["a", "b"], home, _logger())  # commit v1

            class _Crash(Exception):
                pass

            def hook(j, _p=phase, _m=nmoved, _n=nplaced):
                if j["phase"] == _p and len(j["moved_old"]) == _m and len(j["placed_new"]) == _n:
                    raise _Crash()

            crashed = False
            try:
                T.install_target(src_v2, dest, "claude", ["a", "b"], home, _logger(), crash_hook=hook)
            except _Crash:
                crashed = True
            # recovery alone -> consistent (either v1 rolled back or v2 rolled forward)
            T.recover_target("claude", home, _logger())
            ok_after_recover = consistent(dest, ["a", "b"])
            v = (dest / "a" / "v").read_text()
            # a clean re-install completes to v2
            T.install_target(src_v2, dest, "claude", ["a", "b"], home, _logger())
            ok_final = consistent(dest, ["a", "b"]) and (dest / "a" / "v").read_text() == "2"
            check(f"crash@{phase}(m{nmoved},n{nplaced}): crashed={crashed} recover-consistent({v}) + completes",
                  crashed and ok_after_recover and v in ("1", "2") and ok_final)
        os.environ["MEDSCI_HOME"] = str(base / "state")

        # 7. corrupt journal -> fail closed
        home_c = base / "home_corrupt"
        dest_c = base / "dest_corrupt"
        src_c = make_source(base / "rc", {"a": {}}, "1.0.0")
        T.install_target(src_c, dest_c, "claude", ["a"], home_c, _logger())
        (T.target_state_dir("claude", home_c) / "journal.json").write_text("{ not json", encoding="utf-8")
        failed_closed = False
        try:
            T.recover_target("claude", home_c, _logger())
        except T.TxnError:
            failed_closed = True
        check("corrupt journal -> fail closed (TxnError)", failed_closed)

        # 8. containment: escaping path -> TxnError
        esc = False
        try:
            T.assert_contained(base / "outside" / "x", base / "inside")
        except T.TxnError:
            esc = True
        check("assert_contained rejects escape", esc)

        faults(base)

    os.environ.pop("MEDSCI_HOME", None)
    print("----")
    print(f"test_txn: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(run())
