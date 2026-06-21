#!/usr/bin/env python3
"""Crash-recovery + transactional-install tests for installers/medsci_txn.py.

Deterministic, network-free, cross-platform (POSIX + Windows). Drives the installer
against synthetic skill sets in temp dirs with MEDSCI_HOME pointed at a temp root, and
injects crashes at every journal phase to prove recovery converges to a consistent state.
Run: python3 installers/tests/test_txn.py
"""
from __future__ import annotations

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

    os.environ.pop("MEDSCI_HOME", None)
    print("----")
    print(f"test_txn: {PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(run())
