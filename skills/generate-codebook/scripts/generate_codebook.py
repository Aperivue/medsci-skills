#!/usr/bin/env python3
"""Generate a citable data dictionary / codebook from a tabular dataset.

Profiles every column of a dataset and emits two artifacts:
  - codebook.json  — machine-readable (consumed by /define-variables and
                      dictionary-first QC)
  - codebook.md    — human-readable table for review/sharing

Hard anti-hallucination rule: the meaning of coded values is NEVER invented. A
categorical/binary column whose levels are bare codes (0/1/2, "Y"/"N", ...) is
flagged `needs_dictionary: true` with a `[NEEDS DICTIONARY]` note, so the
researcher fills the meaning from the authoritative data dictionary rather than
the model guessing. This is the generator side of the dictionary-first rule.

Profiling is deterministic and local — pandas only, no network, no LLM touches
the values. Optional engines (openpyxl/pyarrow/Stata) are used only if present.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas is required (pip install pandas).", file=sys.stderr)
    sys.exit(2)


CATEGORICAL_MAX_LEVELS_DEFAULT = 20
TOP_LEVELS = 15
EXAMPLES = 3


def read_table(path: Path) -> "pd.DataFrame":
    suf = path.suffix.lower()
    if suf in (".csv", ".txt"):
        return pd.read_csv(path)
    if suf in (".tsv",):
        return pd.read_csv(path, sep="\t")
    if suf in (".xlsx", ".xls"):
        return pd.read_excel(path)            # needs openpyxl/xlrd
    if suf in (".parquet", ".pq"):
        return pd.read_parquet(path)          # needs pyarrow/fastparquet
    if suf in (".dta",):
        return pd.read_stata(path)
    if suf in (".sas7bdat",):
        return pd.read_sas(path)
    # default: try CSV
    return pd.read_csv(path)


def _looks_like_date(series: "pd.Series") -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    s = series.dropna().astype(str).head(50)
    if s.empty:
        return False
    parsed = pd.to_datetime(s, errors="coerce", format="mixed") if hasattr(pd, "__version__") else pd.to_datetime(s, errors="coerce")
    return parsed.notna().mean() > 0.8


MIN_ROWS_FOR_UNIQUENESS_ID = 50  # below this, "all-unique" is not a reliable id signal


def _is_integer_valued(series: "pd.Series") -> bool:
    if pd.api.types.is_integer_dtype(series):
        return True
    nn = series.dropna()
    if nn.empty or not pd.api.types.is_numeric_dtype(series):
        return False
    try:
        return bool((nn.astype(float) % 1 == 0).all())
    except Exception:
        return False


def infer_role(series: "pd.Series", n_rows: int, n_unique: int, max_levels: int, name: str) -> str:
    """Dtype- and name-driven role inference.

    Order matters: date and binary are decided before id, and id is conservative
    (a float column or a small dataset's all-unique column is NOT an id — that
    misclassifies continuous measurements as identifiers on small data).
    """
    name_l = name.lower()
    id_name = name_l == "id" or any(
        tok in name_l for tok in ("_id", "id_", "uid", "mrn", "subject", "patient", "record", "accession")
    )

    if _looks_like_date(series):
        return "date"
    if n_unique == 2:
        return "binary"

    if pd.api.types.is_numeric_dtype(series):
        intlike = _is_integer_valued(series)
        # id only for integer-valued, high-cardinality, id-named columns
        if id_name and intlike and n_unique > max_levels:
            return "id"
        if intlike and n_unique <= max_levels:
            return "categorical"
        return "continuous"

    # object / string
    if id_name and n_unique > max_levels:
        return "id"
    if n_unique == n_rows and n_rows >= MIN_ROWS_FOR_UNIQUENESS_ID:
        return "id"
    if n_unique <= max_levels:
        return "categorical"
    return "text"


def _coded_levels(series: "pd.Series") -> bool:
    """True when the categorical/binary levels are bare codes needing a dictionary."""
    vals = series.dropna().unique().tolist()
    if not vals:
        return False
    for v in vals:
        if pd.api.types.is_number(v):
            continue
        s = str(v).strip()
        # short tokens / pure codes look uninterpretable without a dictionary
        if len(s) <= 3 or s.isdigit() or s.upper() in ("Y", "N", "T", "F", "M", "U", "NA"):
            continue
        return False  # at least one human-readable label present
    return True


def profile_column(df: "pd.DataFrame", col: str, n_rows: int, max_levels: int) -> dict:
    s = df[col]
    n_missing = int(s.isna().sum())
    nonnull = s.dropna()
    n_unique = int(nonnull.nunique())
    role = infer_role(s, n_rows, n_unique, max_levels, col)

    rec: dict = {
        "name": col,
        "role": role,
        "dtype": str(s.dtype),
        "n": int(n_rows),
        "n_missing": n_missing,
        "pct_missing": round(100.0 * n_missing / n_rows, 2) if n_rows else 0.0,
        "n_unique": n_unique,
        "label": None,                 # to be filled by researcher from the real dictionary
        "units": None,                 # to be filled by researcher
        "needs_dictionary": False,
        "notes": [],
    }

    if role == "continuous":
        desc = nonnull.astype(float)
        if not desc.empty:
            rec["stats"] = {
                "min": float(desc.min()), "q1": float(desc.quantile(0.25)),
                "median": float(desc.median()), "q3": float(desc.quantile(0.75)),
                "max": float(desc.max()), "mean": round(float(desc.mean()), 4),
                "sd": round(float(desc.std()), 4) if len(desc) > 1 else 0.0,
            }
        rec["notes"].append("[NEEDS DICTIONARY] confirm units and measurement method")
    elif role in ("categorical", "binary"):
        vc = nonnull.value_counts().head(TOP_LEVELS)
        rec["levels"] = [{"value": (int(v) if pd.api.types.is_number(v) and float(v).is_integer() else
                                    (float(v) if pd.api.types.is_number(v) else str(v))),
                          "count": int(c)} for v, c in vc.items()]
        if _coded_levels(nonnull):
            rec["needs_dictionary"] = True
            rec["notes"].append("[NEEDS DICTIONARY] level codes are uninterpretable without the authoritative data dictionary — do not guess meanings")
    elif role == "date":
        try:
            d = pd.to_datetime(nonnull, errors="coerce")
            rec["stats"] = {"min": str(d.min()), "max": str(d.max())}
        except Exception:
            pass
        rec["notes"].append("[NEEDS DICTIONARY] confirm whether this is event / measurement / enrollment date")
    elif role == "id":
        rec["notes"].append("identifier candidate (high/maximal cardinality) — exclude from analysis variables")

    examples = nonnull.head(EXAMPLES).tolist()
    rec["examples"] = [str(x) for x in examples]
    return rec


def build_codebook(df: "pd.DataFrame", source: str, max_levels: int) -> dict:
    n_rows = len(df)
    cols = [profile_column(df, c, n_rows, max_levels) for c in df.columns]
    return {
        "schema_version": 1,
        "source": source,
        "n_rows": n_rows,
        "n_columns": len(df.columns),
        "needs_dictionary_count": sum(1 for c in cols if c["needs_dictionary"]),
        "columns": cols,
    }


def render_md(cb: dict) -> str:
    lines = [
        f"# Codebook — {Path(cb['source']).name}",
        "",
        f"- Rows: {cb['n_rows']}",
        f"- Columns: {cb['n_columns']}",
        f"- Columns needing a data dictionary: **{cb['needs_dictionary_count']}**",
        "",
        "> `[NEEDS DICTIONARY]` rows require the meaning to be filled from the "
        "authoritative data dictionary. Meanings were **not** guessed.",
        "",
        "| Variable | Role | Dtype | Missing % | Unique | Summary | Needs dictionary |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in cb["columns"]:
        if c["role"] == "continuous" and "stats" in c:
            s = c["stats"]
            summ = f"median {s['median']} [{s['q1']}–{s['q3']}], range {s['min']}–{s['max']}"
        elif c["role"] in ("categorical", "binary") and c.get("levels"):
            summ = ", ".join(f"{l['value']}={l['count']}" for l in c["levels"][:6])
            if len(c["levels"]) > 6:
                summ += ", …"
        elif c["role"] == "date" and "stats" in c:
            summ = f"{c['stats'].get('min','?')} → {c['stats'].get('max','?')}"
        else:
            summ = ", ".join(c.get("examples", [])[:3])
        nd = "⚠️ YES" if c["needs_dictionary"] else ""
        summ = summ.replace("|", "\\|")
        lines.append(f"| `{c['name']}` | {c['role']} | {c['dtype']} | {c['pct_missing']} | {c['n_unique']} | {summ} | {nd} |")
    nd_cols = [c["name"] for c in cb["columns"] if c["needs_dictionary"]]
    if nd_cols:
        lines += ["", "## Columns requiring dictionary lookup", ""]
        for name in nd_cols:
            lines.append(f"- `{name}` — fill level meanings + units from the authoritative data dictionary, then cite per the dictionary-first rule before use in /define-variables.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a data dictionary / codebook from a tabular dataset.")
    ap.add_argument("data", help="Path to .csv/.tsv/.xlsx/.parquet/.dta/.sas7bdat")
    ap.add_argument("--out-dir", default=".", help="Output directory (default: cwd)")
    ap.add_argument("--max-levels", type=int, default=CATEGORICAL_MAX_LEVELS_DEFAULT,
                    help=f"Max distinct values to treat a column as categorical (default {CATEGORICAL_MAX_LEVELS_DEFAULT})")
    ap.add_argument("--json-only", action="store_true", help="Write only codebook.json")
    ap.add_argument("--md-only", action="store_true", help="Write only codebook.md")
    args = ap.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"ERROR: data file not found: {data_path}", file=sys.stderr)
        return 2

    try:
        df = read_table(data_path)
    except Exception as e:
        print(f"ERROR: could not read {data_path}: {e}", file=sys.stderr)
        return 2

    cb = build_codebook(df, str(data_path), args.max_levels)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not args.md_only:
        (out / "codebook.json").write_text(json.dumps(cb, indent=2, ensure_ascii=False), encoding="utf-8")
    if not args.json_only:
        (out / "codebook.md").write_text(render_md(cb), encoding="utf-8")

    print(json.dumps({
        "n_rows": cb["n_rows"],
        "n_columns": cb["n_columns"],
        "needs_dictionary_count": cb["needs_dictionary_count"],
        "outputs": [str(out / "codebook.json")] * (not args.md_only) + [str(out / "codebook.md")] * (not args.json_only),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
