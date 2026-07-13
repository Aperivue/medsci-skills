#!/usr/bin/env python3
"""Training-script reproducibility-hygiene linter for a generated model repo (model-scaffold).

A CONSERVATIVE, AST-based linter (it flags, it does not prove) for the network-free
hygiene properties a medical-imaging training repo must have. It is the training-code
analogue of check_generated_code.py: same posture — parse the source, report missing
patterns, never execute torch. It checks the *presence* of the reproducibility
constructs, which is reliably decidable from the AST; it deliberately does NOT claim
to prove semantic correctness of the training loop.

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
                                      split="test" — training on a non-train split.
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
  --repo   a scaffolded repo directory; train.py and evaluate.py are auto-found.
  --train  explicit path to the training script (overrides --repo discovery).
  --eval   explicit path to the evaluation/inference script.
  (Give --repo, or --train and/or --eval.)

OUTPUT
  A table (stdout) and, with --out, a JSON artifact:
    {train, eval, claims[{verdict, severity, detail, where}], summary}
  SEED_INCOMPLETE / MISSING_EVAL_MODE / TRAIN_ON_NONTRAIN_SPLIT are Major.

Stdlib-only (ast / json / argparse / pathlib). Exit codes: 0 clean (or report-only),
1 Major claim(s) found (with --strict), 2 input/usage error.
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


def _scan(src: str):
    """Extract the hygiene-relevant facts from one script's AST."""
    tree = ast.parse(src)
    facts = {
        "seed_calls": set(),          # normalized RNG seed call chains seen
        "has_eval": False,            # any .eval() call
        "has_no_grad": False,         # torch.no_grad / inference_mode used
        "cudnn_determ": False,        # cudnn.deterministic = True
        "dataset_split": {},          # var name -> split literal it was built with
        "loaders": [],                # (first_arg_name, shuffle_bool)
        "loads_pretrained": False,    # a pretrained=True kwarg or a from_pretrained call
    }
    # dataset var <- Ctor(..., split="X")
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            sp = _kw(node.value, "split")
            if isinstance(sp, ast.Constant) and isinstance(sp.value, str):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        facts["dataset_split"][tgt.id] = sp.value
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute):
            # torch.backends.cudnn.deterministic = True
            pass

    for node in ast.walk(tree):
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
            if tail == "DataLoader":
                first = node.args[0] if node.args else None
                name = first.id if isinstance(first, ast.Name) else None
                sh = _kw(node, "shuffle")
                facts["loaders"].append((name, _is_true(sh)))
            # pretrained-weight load: `...(pretrained=True)` or a `...from_pretrained(...)` call
            if _is_true(_kw(node, "pretrained")) or tail == "from_pretrained":
                facts["loads_pretrained"] = True
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


def analyze(train: str | None, eval_: str | None, repo: str | None = None) -> dict:
    claims = []
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
        for name, shuffle in tfacts["loaders"]:
            sp = tfacts["dataset_split"].get(name)
            if shuffle and sp in ("val", "test"):
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
        for name, shuffle in efacts["loaders"]:
            if shuffle:
                claims.append({
                    "verdict": "EVAL_SHUFFLE", "severity": "Minor",
                    "detail": "an evaluation DataLoader uses shuffle=True (reorders the test set)",
                    "where": Path(eval_).name,
                })

    n_major = sum(1 for c in claims if c["severity"] == "Major")
    return {
        "train": train, "eval": eval_, "claims": claims,
        "summary": {"n_claims": len(claims), "n_major": n_major,
                    "n_minor": len(claims) - n_major,
                    "verdict": "MAJOR_CANDIDATE" if n_major else "OK"},
    }


def render(result: dict) -> str:
    lines = ["| Check | Severity | Detail |", "|---|---|---|"]
    for c in result["claims"]:
        lines.append(f"| {c['verdict']} | {c['severity']} | {c['detail']} |")
    if len(lines) == 2:
        lines.append("| (none) | — | seeds all RNGs, cuDNN deterministic, eval() + no_grad() inference |")
    return "\n".join(lines)


def _resolve(repo: str | None, train: str | None, eval_: str | None):
    if repo:
        r = Path(repo)
        if not r.is_dir():
            sys.stderr.write(f"ERROR: --repo not a directory: {repo}\n")
            sys.exit(2)
        train = train or (str(r / "train.py") if (r / "train.py").is_file() else None)
        eval_ = eval_ or (str(r / "evaluate.py") if (r / "evaluate.py").is_file() else None)
    for label, p in (("--train", train), ("--eval", eval_)):
        if p and not Path(p).is_file():
            sys.stderr.write(f"ERROR: {label} not found: {p}\n")
            sys.exit(2)
    if not train and not eval_:
        sys.stderr.write("ERROR: nothing to check; pass --repo or --train/--eval\n")
        sys.exit(2)
    return train, eval_


def main() -> int:
    ap = argparse.ArgumentParser(description="Training-script reproducibility-hygiene linter (model-scaffold).")
    ap.add_argument("--repo", help="scaffolded repo directory (auto-finds train.py / evaluate.py)")
    ap.add_argument("--train", help="explicit training script path")
    ap.add_argument("--eval", dest="eval_", help="explicit evaluation/inference script path")
    ap.add_argument("--out", help="write JSON artifact to this path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any Major claim exists")
    ap.add_argument("--quiet", action="store_true", help="suppress stdout table")
    args = ap.parse_args()

    train, eval_ = _resolve(args.repo, args.train, args.eval_)
    result = analyze(train, eval_, repo=args.repo)

    if not args.quiet:
        print("=" * 41)
        print(" Training Hygiene (model-scaffold)")
        print("=" * 41)
        print(render(result))
        print()
        s = result["summary"]
        print(f"MAJOR candidate: {s['n_major']} hygiene issue(s)." if s["n_major"]
              else "OK: training/evaluation reproducibility hygiene present.")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"detector": "check_training_hygiene", **result}, indent=2), encoding="utf-8")
        if not args.quiet:
            print(f"\nwrote {args.out}")

    return 1 if (args.strict and result["summary"]["n_major"]) else 0


if __name__ == "__main__":
    sys.exit(main())
