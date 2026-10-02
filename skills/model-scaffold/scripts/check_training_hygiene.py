#!/usr/bin/env python3
"""Training-script reproducibility-hygiene linter for a generated model repo (model-scaffold).

A CONSERVATIVE, AST-based linter (it flags, it does not prove) for the network-free
hygiene properties a medical-imaging training repo must have. It is the training-code
analogue of check_generated_code.py: same posture — parse the source, report missing
patterns, never execute torch. It checks the *presence* of the reproducibility
constructs in code a run can reach: import-time statements plus every function they
reference, transitively (a seed_everything that is defined but never called does not
count; a file whose import-time code calls none of its own functions is entered through
each public top-level function nothing in it references). It deliberately does NOT claim
to prove semantic correctness of the training loop, nor statement order (an inference
call placed before model.eval() in the same function is not detected).

CHECKS (verdicts):
  1. SEED_INCOMPLETE         (Major)  the training script must seed every RNG that
                                      affects a run: random.seed, numpy
                                      (np.random.seed / numpy.random.seed),
                                      torch.manual_seed, torch.cuda.manual_seed_all.
                                      Reports which calls are missing.
  2. MISSING_EVAL_MODE       (Major)  the evaluation/inference script must call
                                      model.eval() AND wrap inference in
                                      torch.no_grad() (or torch.inference_mode());
                                      otherwise dropout/batchnorm stay in train mode
                                      and gradients are tracked.
  3. TRAIN_ON_NONTRAIN_SPLIT (Major)  a training-style DataLoader (shuffle=True) built
                                      from a dataset constructed with split="val" or
                                      split="test" (keyword, or a positional "val"/"test"
                                      literal), directly, through a variable, or inside
                                      a wrapper such as ConcatDataset([...]) / Subset(...)
                                      — training on a non-train split.
  4. CUDNN_NONDETERMINISTIC  (Minor)  torch.backends.cudnn.deterministic is not set
                                      True in the training script.
  5. EVAL_SHUFFLE            (Minor)  an evaluation DataLoader uses shuffle=True
                                      (reorders the test set; harmless for metrics but
                                      a smell, and breaks index-aligned outputs).
  6. PRETRAINED_PROVENANCE_MISSING (Minor)  the training script loads PRETRAINED weights
                                      (a `pretrained=True` kwarg or a `from_pretrained`
                                      call — fine-tuning / transfer learning) but the repo
                                      records no pretrained-weight provenance (no non-empty
                                      PRETRAINED.md and no `pretrained:` block in
                                      config.yaml). A fine-tune whose starting checkpoint is
                                      unrecorded is not reproducible. Fires only in --repo
                                      mode (the provenance record is a repo-level artifact).

INPUTS
  --repo   a scaffolded repo directory; train.py and evaluate.py are auto-found. A
           script that is not found is reported as NOT CHECKED (never as clean).
  --train  explicit path to the training script (overrides --repo discovery).
  --eval   explicit path to the evaluation/inference script.
  (Give --repo, or --train and/or --eval.)

OUTPUT
  A table (stdout) and, with --out, a JSON artifact:
    {train, eval, claims[{verdict, severity, detail, where}], summary}
  SEED_INCOMPLETE / MISSING_EVAL_MODE / TRAIN_ON_NONTRAIN_SPLIT are Major.

Stdlib-only (ast / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error, or (with --strict) a check
group that could not run because --repo has no train.py / evaluate.py.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def _attr_chain(node: ast.AST) -> str:
    """Dotted name for a Name/Attribute chain ('torch.cuda.manual_seed_all')."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _kw(call: ast.Call, name: str):
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


def _is_true(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


NONTRAIN_SPLITS = ("val", "test")


def _unit_defs(tree: ast.Module):
    """Split a module into the code that runs on import (roots) and the named function units
    (top-level functions and class methods) that run only when something references them."""
    roots, units = [], {}

    def visit(stmts):
        for st in stmts:
            if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                units.setdefault(st.name, []).append(st)
                roots.extend(st.decorator_list)
                roots.extend(st.args.defaults + [d for d in st.args.kw_defaults if d is not None])
            elif isinstance(st, ast.ClassDef):
                roots.extend(st.decorator_list + st.bases + [k.value for k in st.keywords])
                visit(st.body)
            else:
                roots.append(st)

    visit(tree.body)
    return roots, units


def _refs(nodes) -> set:
    out = set()
    for n in nodes:
        for m in ast.walk(n):
            if isinstance(m, ast.Name):
                out.add(m.id)
            elif isinstance(m, ast.Attribute):
                out.add(m.attr)
    return out


def _reachable(tree: ast.Module) -> list:
    """The code a run of this script can execute: import-time statements plus every function unit
    referenced (called, passed, decorated) from reachable code, transitively. A seeding helper that
    is defined but never called therefore does not count as seeding.
    A module whose import-time code references none of its own functions (a library-style file
    whose entry point lives elsewhere) is entered through each public top-level function that
    nothing in the file references. Dunder methods are always entry points (called implicitly)."""
    roots, units = _unit_defs(tree)
    root_refs = _refs(roots)
    entry = {n for n in units if n.startswith("__") and n.endswith("__")}
    if not (root_refs & set(units)):
        everywhere = set()
        for defs in units.values():
            for d in defs:
                everywhere |= _refs(d.body)
        everywhere |= root_refs
        entry |= {n for n in units if not n.startswith("_") and n not in everywhere}
    seen, todo = set(), list(entry | (root_refs & set(units)))
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        for d in units[name]:
            todo.extend((_refs(d.body) & set(units)) - seen)
    nodes = list(roots)
    for name in seen:
        for d in units[name]:
            nodes.extend(d.body)
    return nodes


def _splits_of(expr, dataset_split: dict) -> set:
    """Every split literal a dataset expression is built from: `x` (a variable assigned earlier),
    `DS(..., split="test")`, `DS(..., "test")` (a positional "val"/"test" literal), and wrappers
    such as ConcatDataset([...]) / Subset(ds, idx) whose arguments carry a split."""
    found = set()
    if isinstance(expr, ast.Name):
        found |= dataset_split.get(expr.id, set())
    elif isinstance(expr, ast.Call):
        sp = _kw(expr, "split")
        if isinstance(sp, ast.Constant) and isinstance(sp.value, str):
            found.add(sp.value)
        for a in expr.args:
            if isinstance(a, ast.Constant) and a.value in NONTRAIN_SPLITS:
                found.add(a.value)
            else:
                found |= _splits_of(a, dataset_split)
    elif isinstance(expr, (ast.List, ast.Tuple)):
        for e in expr.elts:
            found |= _splits_of(e, dataset_split)
    elif isinstance(expr, ast.Starred):
        found |= _splits_of(expr.value, dataset_split)
    return found


def _scan(src: str):
    """Extract the hygiene-relevant facts from one script's AST. Seeding, cuDNN determinism,
    eval() and no_grad() count only where a run can reach them (see _reachable)."""
    tree = ast.parse(src)
    facts = {
        "seed_calls": set(),          # normalized RNG seed call chains seen (reachable code)
        "has_eval": False,            # any reachable .eval() call
        "has_no_grad": False,         # torch.no_grad / inference_mode used in reachable code
        "cudnn_determ": False,        # cudnn.deterministic = True (reachable code)
        "dataset_split": {},          # var name -> split literals it was built from
        "loaders": [],                # (dataset label, splits it is built from, shuffle_bool)
        "loads_pretrained": False,    # a pretrained=True kwarg or a from_pretrained call
    }
    # dataset var <- Ctor(..., split="X") / Ctor(..., "X") / ConcatDataset([...]); in source order
    assigns = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)]
    assigns.sort(key=lambda n: (n.lineno, n.col_offset))
    for node in assigns:
        sps = _splits_of(node.value, facts["dataset_split"]) if isinstance(node.value, ast.Call) else set()
        if sps:
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    facts["dataset_split"][tgt.id] = sps   # a later rebinding replaces it

    # whole-file facts (a loader or a pretrained load anywhere is reported)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            tail = _attr_chain(node.func).split(".")[-1]
            if tail == "DataLoader":
                first = node.args[0] if node.args else _kw(node, "dataset")
                label = first.id if isinstance(first, ast.Name) else (
                    ast.unparse(first) if first is not None else None)
                sps = _splits_of(first, facts["dataset_split"]) if first is not None else set()
                sh = _kw(node, "shuffle")
                facts["loaders"].append((label, sps, _is_true(sh)))
            # pretrained-weight load: `...(pretrained=True)` or a `...from_pretrained(...)` call
            if _is_true(_kw(node, "pretrained")) or tail == "from_pretrained":
                facts["loads_pretrained"] = True

    # reachable-only facts
    for root in _reachable(tree):
        for node in ast.walk(root):
            if isinstance(node, ast.Call):
                chain = _attr_chain(node.func)
                tail = chain.split(".")[-1]
                if tail in ("seed", "manual_seed", "manual_seed_all"):
                    # normalize: random.seed / numpy seed / torch(.cuda).manual_seed*
                    if chain.endswith("random.seed") and not chain.startswith(("np", "numpy")):
                        facts["seed_calls"].add("random")
                    elif "random.seed" in chain or chain.endswith("np.random.seed"):
                        facts["seed_calls"].add("numpy")
                    elif chain.endswith("manual_seed_all"):
                        facts["seed_calls"].add("torch.cuda")
                    elif chain.endswith("manual_seed"):
                        facts["seed_calls"].add("torch")
                if tail == "eval" and isinstance(node.func, ast.Attribute):
                    facts["has_eval"] = True
                if chain.endswith(("no_grad", "inference_mode")):
                    facts["has_no_grad"] = True
            # cudnn.deterministic = True (assignment to an Attribute target)
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Attribute) and tgt.attr == "deterministic":
                        if "cudnn" in _attr_chain(tgt) and _is_true(node.value):
                            facts["cudnn_determ"] = True
    return facts


def _has_pretrained_provenance(repo: Path) -> bool:
    """True if the repo records pretrained-weight provenance: a non-empty PRETRAINED.md, or
    a `pretrained:` block in config.yaml."""
    pm = repo / "PRETRAINED.md"
    if pm.is_file() and pm.read_text(encoding="utf-8").strip():
        return True
    cfg = repo / "config.yaml"
    if cfg.is_file():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("pretrained:"):
                return True
    return False


def analyze(train: str | None, eval_: str | None, repo: str | None = None,
            unchecked: list | None = None) -> dict:
    claims = []
    unchecked = list(unchecked or [])
    tfacts = _scan(Path(train).read_text(encoding="utf-8")) if train else None
    efacts = _scan(Path(eval_).read_text(encoding="utf-8")) if eval_ else None

    if tfacts is not None:
        need = {"random", "numpy", "torch", "torch.cuda"}
        missing = sorted(need - tfacts["seed_calls"])
        if missing:
            claims.append({
                "verdict": "SEED_INCOMPLETE", "severity": "Major",
                "detail": f"training script does not seed: {', '.join(missing)} "
                          f"(found: {', '.join(sorted(tfacts['seed_calls'])) or 'none'})",
                "where": Path(train).name,
            })
        if not tfacts["cudnn_determ"]:
            claims.append({
                "verdict": "CUDNN_NONDETERMINISTIC", "severity": "Minor",
                "detail": "torch.backends.cudnn.deterministic is not set True in the training script",
                "where": Path(train).name,
            })
        # training on a non-train split (shuffle=True loader from a val/test dataset)
        for name, sps, shuffle in tfacts["loaders"]:
            bad = sorted(set(sps) & set(NONTRAIN_SPLITS))
            if shuffle and bad:
                sp = "/".join(bad)
                claims.append({
                    "verdict": "TRAIN_ON_NONTRAIN_SPLIT", "severity": "Major",
                    "detail": f"a shuffled (training-style) DataLoader is built from dataset "
                              f"'{name}' constructed with split=\"{sp}\" — training on the {sp} split",
                    "where": Path(train).name,
                })
        # fine-tuning: pretrained weights loaded but no provenance recorded (repo mode only)
        if tfacts["loads_pretrained"] and repo and not _has_pretrained_provenance(Path(repo)):
            claims.append({
                "verdict": "PRETRAINED_PROVENANCE_MISSING", "severity": "Minor",
                "detail": "the training script loads pretrained weights (fine-tuning) but the "
                          "repo records no pretrained-weight provenance (a non-empty PRETRAINED.md "
                          "or a 'pretrained:' block in config.yaml). Record the exact "
                          "source / checkpoint / license / hash so the fine-tune is reproducible.",
                "where": Path(train).name,
            })

    if efacts is not None:
        if not (efacts["has_eval"] and efacts["has_no_grad"]):
            miss = []
            if not efacts["has_eval"]:
                miss.append("model.eval()")
            if not efacts["has_no_grad"]:
                miss.append("torch.no_grad()/inference_mode()")
            claims.append({
                "verdict": "MISSING_EVAL_MODE", "severity": "Major",
                "detail": f"evaluation script is missing {', '.join(miss)} before inference "
                          f"(dropout/batchnorm stay in train mode and gradients are tracked)",
                "where": Path(eval_).name,
            })
        for name, _sps, shuffle in efacts["loaders"]:
            if shuffle:
                claims.append({
                    "verdict": "EVAL_SHUFFLE", "severity": "Minor",
                    "detail": "an evaluation DataLoader uses shuffle=True (reorders the test set)",
                    "where": Path(eval_).name,
                })

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "train": train, "eval": eval_, "claims": claims, "unchecked": unchecked,
        "summary": {"n_claims": len(claims), "n_major": n_major,
                    "n_minor": len(claims) - n_major,
                    "verdict": ("MAJOR_CANDIDATE" if n_major
                                else "INCOMPLETE" if unchecked else "OK")},
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        ran = []
        if result.get("train"):
            ran.append("training script seeds all RNGs and sets cuDNN deterministic "
                       "(in code a run reaches), no shuffled loader on a val/test split")
        if result.get("eval"):
            ran.append("evaluation script calls eval() and no_grad() in code a run reaches")
        lines.append(f"| (none) | — | {'; '.join(ran)} |")
    for u in result.get("unchecked", []):
        lines.append(f"| NOT CHECKED | — | {u} |")
    return "\n".join(lines)


def _resolve(repo: str | None, train: str | None, eval_: str | None):
    unchecked = []
    if repo:
        r = Path(repo)
        if not r.is_dir():
            sys.stderr.write(f"ERROR: --repo not a directory: {repo}\n")
            sys.exit(2)
        train = train or (str(r / "train.py") if (r / "train.py").is_file() else None)
        eval_ = eval_ or (str(r / "evaluate.py") if (r / "evaluate.py").is_file() else None)
        if not train:
            unchecked.append("training-script checks (seeding, cuDNN, train split): no train.py "
                             "in --repo; pass --train")
        if not eval_:
            unchecked.append("evaluation-script checks (eval(), no_grad()): no evaluate.py in "
                             "--repo; pass --eval")
    for label, p in (("--train", train), ("--eval", eval_)):
        if p and not Path(p).is_file():
            sys.stderr.write(f"ERROR: {label} not found: {p}\n")
            sys.exit(2)
    if not train and not eval_:
        sys.stderr.write("ERROR: nothing to check; pass --repo or --train/--eval\n")
        sys.exit(2)
    return train, eval_, unchecked


def main() -> int:
    ap = argparse.ArgumentParser(description="Training-script reproducibility-hygiene linter (model-scaffold).")
    ap.add_argument("--repo", help="scaffolded repo directory (auto-finds train.py / evaluate.py)")
    ap.add_argument("--train", help="explicit training script path")
    ap.add_argument("--eval", dest="eval_", help="explicit evaluation/inference script path")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    train, eval_, unchecked = _resolve(args.repo, args.train, args.eval_)
    result = analyze(train, eval_, repo=args.repo, unchecked=unchecked)

    if not args.quiet:
        print("=" * 41)
        print(" Training Hygiene (model-scaffold)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        if s["n_major"]:
            print(f"MAJOR candidate: {s['n_major']} hygiene issue(s).")
        elif result["unchecked"]:
            print(f"INCOMPLETE: {len(result['unchecked'])} check group(s) could not run "
                  "(see NOT CHECKED); not a clearance.")
        else:
            print("OK: training/evaluation reproducibility hygiene present.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_training_hygiene", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    if args.strict and result["summary"]["n_major"]:
        return 1
    if args.strict and result["unchecked"]:
        return 2   # a check that could not run is not a pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
