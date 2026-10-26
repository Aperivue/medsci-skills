#!/usr/bin/env python3
"""Add journal abbreviations (`shortjournal`) to a BibTeX/BibLaTeX .bib from PubMed, then CrossRef.

Why: CSL `container-title form="short"` prints the full journal name unless the
.bib entry carries a `shortjournal` field. Hand-written and AI-written bibs almost never
have it, and a Better BibTeX export has it only when the Zotero item's "Journal Abbr"
field is filled, so NLM-style journals (JKMS, AJR, KJR, JMIR, ...) render the full title
regardless of CSL. This script resolves each entry's PMID (the `pmid` field, else DOI -> PMID)
to the PubMed esummary `source` (the NLM Title Abbreviation) and writes `shortjournal = {...}`.

When PubMed has no record for the DOI, CrossRef's `short-container-title` is used instead and
the entry is reported as `CrossRef`: that value is often an ISO 4 abbreviation with periods
("J. Stat. Softw."), not the NLM form, so check those entries. Never invents an abbreviation:
an entry with no PMID, no DOI or no answer from either source is left unchanged and named.

What it changes and what it does not:
  - adds `shortjournal` right after the entry's `journal`/`journaltitle` field, in the entry's own
    indentation; fills an existing EMPTY `shortjournal = {}` in place;
  - never overwrites a non-empty `shortjournal`, never touches any other field;
  - skips (and names) entries it cannot edit safely: no journal field, a journal given as a
    @string macro or a `#` concatenation, a field it cannot read;
  - stops before writing anything when an entry's braces do not balance, since every entry after
    it would be swallowed unread.
The output is re-parsed before it is written; if any entry, key or field changed other than the
added abbreviations, nothing is written. When pandoc is installed it must also read both the input
and the output: a bib pandoc cannot read is refused before any lookup, and an output it cannot
read is never written.

A bib that Better BibTeX regenerates (`/lit-sync` auto-export) is overwritten on the next
export, so the abbreviations belong in Zotero's "Journal Abbr" field. For such a file this
script refuses to write in place (`--out` equal to `--bib`) and says so when writing elsewhere.

Exit codes:
  0  finished; every entry that could be looked up was (some may have no abbreviation)
  1  output written, but some lookups failed (network or service error): those entries are
     unchanged and named; re-run later
  2  input error (unreadable file, an entry with unbalanced braces, duplicate keys, a bib pandoc
     cannot read), or the output failed its own re-parse; nothing written

Usage:
  python fill_journal_abbrev.py --bib refs.bib --out refs_abbrev.bib
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CROSSREF = "https://api.crossref.org/works/"
UA = {"User-Agent": "medsci-manage-refs/1.1 (https://github.com/Aperivue/medsci-skills)"}

SKIP_TYPES = {"comment", "string", "preamble"}
LIT_SYNC_MARKER = "managed by /lit-sync"


class LookupFailed(RuntimeError):
    """A service could not be asked (network error, HTTP error, unreadable reply).

    Kept apart from "the service has no record": the old lookup returned None for both, so an
    outage read as "PubMed does not know this journal" and the entry silently kept its full title.
    """


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode()


def doi_to_pmid(doi):
    """PMID for a DOI, or None when PubMed has no record. Raises LookupFailed if PubMed was not reached."""
    term = urllib.parse.quote(f'"{doi}"[AID] OR "{doi}"[DOI]')
    try:
        j = json.loads(_get(f"{EUTILS}/esearch.fcgi?db=pubmed&term={term}&retmode=json"))
    except (OSError, ValueError) as exc:  # URLError and HTTPError are OSErrors
        raise LookupFailed(f"PubMed esearch: {exc}") from exc
    res = j.get("esearchresult") if isinstance(j, dict) else None
    # NCBI reports some failures (rate limit, bad query) inside a 200 reply: that is no answer.
    if not isinstance(res, dict) or "error" in j or "ERROR" in res:
        raise LookupFailed(f"PubMed esearch: {str(j)[:200]}")
    ids = res.get("idlist", [])
    return ids[0] if ids else None


def pmids_summary(pmids):
    """{pmid: {'source': NLM abbreviation}} for every PMID. Raises LookupFailed if PubMed was not reached."""
    out, pmids = {}, list(pmids)
    for i in range(0, len(pmids), 150):
        chunk = pmids[i:i + 150]
        try:
            j = json.loads(_get(f"{EUTILS}/esummary.fcgi?db=pubmed&id={','.join(chunk)}&retmode=json"))
        except (OSError, ValueError) as exc:
            raise LookupFailed(f"PubMed esummary: {exc}") from exc
        if not isinstance(j, dict) or "error" in j or not isinstance(j.get("result"), dict):
            raise LookupFailed(f"PubMed esummary: {str(j)[:200]}")
        res = j["result"]
        out.update({p: {"source": (res.get(p) or {}).get("source"), "error": (res.get(p) or {}).get("error")}
                    for p in chunk})
    return out


def crossref_short_title(doi):
    """CrossRef `short-container-title` for a DOI, or None when CrossRef has none. Raises LookupFailed."""
    try:
        j = json.loads(_get(CROSSREF + urllib.parse.quote(doi, safe="/")))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise LookupFailed(f"CrossRef: {exc}") from exc
    except (OSError, ValueError) as exc:
        raise LookupFailed(f"CrossRef: {exc}") from exc
    if not isinstance(j, dict) or j.get("status") != "ok":
        raise LookupFailed(f"CrossRef: {str(j)[:200]}")
    short = j.get("message", {}).get("short-container-title") or []
    return short[0].strip() if short and short[0].strip() else None


# ---- parsing --------------------------------------------------------------------------------
# A small brace-aware parser. The regex parser it replaces needed every entry to end with "\n}"
# and every value to be braced, so a one-line entry was invisible and a quoted `doi = "..."` read as
# no DOI. Its insertion pattern assumed tab indentation: on a two-space bib it matched no journal
# field, appended the new field after a last field that has no comma, and broke the file.

_NAME = re.compile(r"[A-Za-z_][\w\-:.+]*")
_BARE = re.compile(r"[^\s,#}]+")


class Unsupported(ValueError):
    pass


def _skip(text, i, end, extra=""):
    """Index of the next character that is not whitespace, one of `extra`, or a `%` comment.

    Used only where whitespace may stand (between fields, around `=` and `#`): a `%` there runs to
    the end of the line, as pandoc reads it. Inside a value a `%` is text (`url = {.../%7Euser}`).
    """
    while i < end:
        if text[i] in " \t\r\n" or text[i] in extra:
            i += 1
        elif text[i] == "%":
            nl = text.find("\n", i, end)
            i = end if nl == -1 else nl + 1
        else:
            break
    return i


def _match_brace(text, i, entry=False):
    """Index just past the brace that closes the one at text[i] (a backslash escapes one character).

    With entry=True, text[i] opens a whole entry: at its top level, outside a quoted value, a `%`
    starts a comment, so a brace in `% {old note` is not counted.
    """
    depth, j, quoted = 0, i, False
    while j < len(text):
        c = text[j]
        if c == "\\":
            j += 2
            continue
        if entry and depth == 1:
            if c == '"':
                quoted = not quoted
            elif c == "%" and not quoted:
                nl = text.find("\n", j)
                if nl == -1:
                    break
                j = nl + 1
                continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise Unsupported("unbalanced braces")


def _read_value(text, i, end):
    """(value_start, value_end, kind, inner) for the field value at or after text[i]."""
    parts, start = [], None
    while True:
        i = _skip(text, i, end)
        if i >= end:
            raise Unsupported("field without a value")
        start = i if start is None else start
        c = text[i]
        if c == "{":
            j = _match_brace(text, i)
            parts.append(("braced", text[i + 1:j - 1]))
        elif c == '"':
            j, depth = i + 1, 0
            while j < end:
                if text[j] == "\\":
                    j += 2
                    continue
                if text[j] == "{":
                    depth += 1
                elif text[j] == "}":
                    depth -= 1
                elif text[j] == '"' and depth == 0:
                    break
                j += 1
            if j >= end:
                raise Unsupported("unterminated quoted value")
            parts.append(("quoted", text[i + 1:j]))
            j += 1
        else:
            m = _BARE.match(text, i)
            if not m:
                raise Unsupported("unreadable value")
            j = m.end()
            parts.append(("bare", m.group(0)))
        k = _skip(text, j, end)
        if k < end and text[k] == "#":
            i = k + 1
            continue
        if len(parts) == 1:
            return start, j, parts[0][0], parts[0][1]
        return start, j, "concat", None


def parse_bib(text):
    """Entries in file order: dicts with type, key, start, end, fields, unsupported.

    fields maps a lower-cased field name to (name_start, value_start, value_end, kind, inner):
    kind is braced | quoted | bare | concat, inner the text inside the braces or quotes.
    """
    entries, pos = [], 0
    for m in re.finditer(r"@(\w+)\s*\{", text):
        if m.start() < pos:
            continue
        # `% @article{old,` is a comment outside any entry, as pandoc reads it. Only the text after the
        # previous entry counts: a `50\%` inside an entry earlier on the same line is not a comment.
        if "%" in text[max(pos, text.rfind("\n", 0, m.start()) + 1):m.start()]:
            continue
        etype, brace = m.group(1), m.end() - 1
        try:
            end = _match_brace(text, brace, entry=etype.lower() not in SKIP_TYPES)
        except Unsupported:
            # Everything after this point is swallowed by the open entry, so parsing stops here.
            head = re.match(r"\s*([^,\s}]+)", text[brace + 1:])
            entries.append({"type": etype, "key": head.group(1) if head else None, "start": m.start(),
                            "end": len(text), "fields": {}, "unsupported": "unbalanced braces",
                            "line": text.count("\n", 0, m.start()) + 1})
            break
        pos = end
        if etype.lower() in SKIP_TYPES:
            continue
        body_start, body_end = brace + 1, end - 1
        comma = text.find(",", body_start, body_end)
        key = text[body_start:comma if comma != -1 else body_end].strip()
        entry = {"type": etype, "key": key, "start": m.start(), "end": end, "fields": {}, "unsupported": None,
                 "body_start": comma + 1 if comma != -1 else body_end, "body_end": body_end,
                 "line": text.count("\n", 0, m.start()) + 1}
        i = comma + 1 if comma != -1 else body_end
        try:
            while True:
                i = _skip(text, i, body_end, ",")
                if i >= body_end:
                    break
                nm = _NAME.match(text, i)
                if not nm:
                    raise Unsupported("unreadable field name")
                j = _skip(text, nm.end(), body_end)
                if j >= body_end or text[j] != "=":
                    raise Unsupported(f"field {nm.group(0)!r} without '='")
                vstart, vend, kind, inner = _read_value(text, j + 1, body_end)
                entry["fields"].setdefault(nm.group(0).lower(), (nm.start(), vstart, vend, kind, inner))
                k = _skip(text, vend, body_end)
                if k < body_end and text[k] != ",":
                    raise Unsupported(f"no comma after field {nm.group(0)!r}")
                i = vend
        except Unsupported as exc:
            entry["unsupported"] = str(exc)
        entries.append(entry)
    return entries


def _value(entry, name):
    f = entry["fields"].get(name)
    if f and f[3] == "bare" and f[4].isdigit():  # a bare number is a literal; a bare word is a @string macro
        return f[4]
    if not f or f[3] not in ("braced", "quoted"):
        return None
    return f[4].strip()


def parse_entries(bib):
    """Entry texts, in order (the interface callers and tests already use)."""
    return [bib[e["start"]:e["end"]] for e in parse_bib(bib) if e["key"]]


def field(block, name):
    """Value of `name` in one entry's text, or None. The trailing comma is optional in BibTeX."""
    entries = parse_bib(block)
    return _value(entries[0], name.lower()) if entries else None


def pandoc_reads(text):
    """None when pandoc is not installed, else (ok, message) for pandoc reading `text` as BibLaTeX."""
    try:
        p = subprocess.run(["pandoc", "-f", "biblatex", "-t", "csljson"], input=text,
                           capture_output=True, text=True)
    except FileNotFoundError:
        return None
    return p.returncode == 0, " ".join(p.stderr.split())[:300]


def normalize_doi(doi):
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", doi.strip(), flags=re.I)
    return doi or None


def looks_bbt_managed(text):
    """True for a file Better BibTeX regenerates: the /lit-sync marker, or BBT's export shape."""
    if LIT_SYNC_MARKER in text:
        return True
    entries = [e for e in parse_bib(text) if e["key"]]
    if not entries:
        return False
    tabbed = sum(1 for e in entries if re.search(r"\n\t\w", text[e["start"]:e["end"]]))
    bbt_like = sum(1 for e in entries if {"langid", "file", "journaltitle", "urldate"} & set(e["fields"]))
    return tabbed == len(entries) and bbt_like >= len(entries) / 2


# ---- editing --------------------------------------------------------------------------------

def plan_edit(text, entry, abbrev, nl):
    """(position, delete_to, insert) that puts `shortjournal = {abbrev}` into this entry."""
    sj = entry["fields"].get("shortjournal")
    if sj:  # present but empty: fill the value in place
        return (sj[1], sj[2], "{" + abbrev + "}")
    name_start, _vstart, vend, _kind, _inner = entry["fields"].get("journaltitle") or entry["fields"]["journal"]
    line_start = text.rfind("\n", entry["start"], name_start)
    indent = text[line_start + 1:name_start] if line_start != -1 else None
    if indent is not None and indent.strip() == "":
        # Inserted directly after the journal VALUE, before whatever followed it. The new field
        # brings its own leading comma and the original separator (a comma, or nothing before the
        # closing brace) follows unchanged, so this is right whether or not journal was the last field.
        return (vend, vend, "," + nl + indent + "shortjournal = {" + abbrev + "}")
    return (vend, vend, ", shortjournal = {" + abbrev + "}")  # journal shares a line with other text


def fill(text):
    """(new_text, results), results = [(key, status, detail, source)].

    status: added | filled_empty | kept | no_journal | journal_not_editable | no_id |
            not_found | lookup_failed | unsupported
    """
    nl = "\r\n" if "\r\n" in text else "\n"
    results, todo = [], []
    for e in parse_bib(text):
        key = e["key"] or "(unreadable entry)"
        if e["unsupported"]:
            results.append((key, "unsupported", e["unsupported"], None))
            continue
        if _value(e, "shortjournal"):
            results.append((key, "kept", _value(e, "shortjournal"), None))
            continue
        jf = e["fields"].get("journaltitle") or e["fields"].get("journal")
        if not jf:
            results.append((key, "no_journal", None, None))
            continue
        sj = e["fields"].get("shortjournal")
        if jf[3] not in ("braced", "quoted") or (sj and sj[3] not in ("braced", "quoted")):
            results.append((key, "journal_not_editable", None, None))
            continue
        pm = re.search(r"\d+", _value(e, "pmid") or "")
        doi = normalize_doi(_value(e, "doi") or "")
        if not pm and not doi:
            results.append((key, "no_id", None, None))
            continue
        todo.append((e, pm.group(0) if pm else None, doi))

    # PubMed first: DOI -> PMID where the entry has no PMID, then one esummary for all of them.
    pmid_of, failed = {}, {}
    for e, pmid, doi in todo:
        if pmid:
            pmid_of[e["key"]] = pmid
            continue
        try:
            pmid_of[e["key"]] = doi_to_pmid(doi)
        except LookupFailed as exc:
            failed[e["key"]] = str(exc)
        time.sleep(0.4)  # NCBI allows 3 requests per second without an API key
    pmids = sorted({p for p in pmid_of.values() if p})
    summary = {}
    if pmids:
        try:
            summary = pmids_summary(pmids)
        except LookupFailed as exc:
            for k, p in pmid_of.items():
                if p:
                    failed.setdefault(k, str(exc))

    edits = []
    for e, bib_pmid, doi in todo:
        key = e["key"]
        if key in failed:
            results.append((key, "lookup_failed", failed[key], None))
            continue
        p = pmid_of.get(key)
        record_error = (summary.get(p) or {}).get("error") if p else None
        note = None
        if record_error and not bib_pmid:
            # PubMed returned this PMID for the DOI a moment ago, so an error now is the service's.
            results.append((key, "lookup_failed", f"PubMed esummary for PMID {p}: {record_error}", None))
            continue
        if record_error:  # retrying will not help: the pmid field names no PubMed record
            note = f"PubMed has no record for pmid {p} ({record_error}); check the pmid field"
        abbrev = ((summary.get(p) or {}).get("source") or "").strip() if p else ""
        source = "PubMed" if abbrev else None
        if not abbrev and doi:
            try:
                abbrev = (crossref_short_title(doi) or "").strip()
            except LookupFailed as exc:
                results.append((key, "lookup_failed", str(exc), None))
                continue
            source = "CrossRef" if abbrev else None
        abbrev = abbrev.replace("{", "").replace("}", "")  # a brace would end the field early
        if not abbrev:
            results.append((key, "not_found", note, None))
            continue
        edits.append(plan_edit(text, e, abbrev, nl))
        results.append((key, "filled_empty" if e["fields"].get("shortjournal") else "added", abbrev, source))

    out = text
    for pos, delete_to, insert in sorted(edits, key=lambda t: t[0], reverse=True):
        out = out[:pos] + insert + out[delete_to:]
    return out, results


def verify(before, after, results):
    """Problems with `after`; empty when every entry and field survived and each addition reads back."""
    problems = []
    b = [e for e in parse_bib(before) if e["key"]]
    a = [e for e in parse_bib(after) if e["key"]]
    if [e["key"] for e in b] != [e["key"] for e in a]:
        return ["entry keys or their order changed"]
    for eb, ea in zip(b, a):
        if ea["unsupported"] and not eb["unsupported"]:
            problems.append(f"{eb['key']}: no longer parses ({ea['unsupported']})")
        for name in set(eb["fields"]) | set(ea["fields"]):
            if name != "shortjournal" and _value(ea, name) != _value(eb, name):
                problems.append(f"{eb['key']}: field {name} changed")
    a_by_key = {e["key"]: e for e in a}
    for key, status, abbrev, _src in results:
        if status in ("added", "filled_empty") and _value(a_by_key[key], "shortjournal") != abbrev:
            problems.append(f"{key}: shortjournal does not read back as {abbrev!r}")
    return problems


LABELS = {
    "added": "added", "filled_empty": "filled (was empty)",
    "no_journal": "skipped: no journal/journaltitle field",
    "journal_not_editable": "skipped: journal or shortjournal is a macro or concatenation",
    "no_id": "skipped: no PMID or DOI", "not_found": "no abbreviation found (PubMed, CrossRef)",
    "lookup_failed": "LOOKUP FAILED, unchanged", "unsupported": "skipped: entry not parsed",
}


def main():
    ap = argparse.ArgumentParser(description="Add journal abbreviations (shortjournal) from PubMed, then CrossRef.")
    ap.add_argument("--bib", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        with open(a.bib, encoding="utf-8") as fh:
            bib = fh.read()
    except OSError as exc:
        print(f"ERROR: cannot read {a.bib}: {exc}", file=sys.stderr)
        sys.exit(2)

    broken = [e for e in parse_bib(bib) if e["unsupported"] == "unbalanced braces"]
    if broken:
        e = broken[0]
        print(f"ERROR: {a.bib} line {e['line']}: entry {e['key'] or '(no key)'} has unbalanced braces, so "
              "nothing after it can be read. Fix the bib first; nothing written.", file=sys.stderr)
        sys.exit(2)

    seen, dups = set(), []
    for e in parse_bib(bib):
        if e["key"] in seen and e["key"] not in dups:
            dups.append(e["key"])
        seen.add(e["key"])
    if dups:
        print(f"ERROR: duplicate entry keys in {a.bib}: {', '.join(dups)}. Each key must be unique "
              "(which entry a citation means is ambiguous); nothing written.", file=sys.stderr)
        sys.exit(2)

    read = pandoc_reads(bib)
    if read is not None and not read[0]:
        print(f"ERROR: pandoc cannot read {a.bib} ({read[1]}). Fix the bib first; nothing written.",
              file=sys.stderr)
        sys.exit(2)

    bbt = looks_bbt_managed(bib)
    if bbt and os.path.realpath(a.out) == os.path.realpath(a.bib):
        print(f"ERROR: {a.bib} looks regenerated by Better BibTeX; the next export would erase the "
              "abbreviations. Fill Zotero's 'Journal Abbr' field instead, or write to a separate --out.",
              file=sys.stderr)
        sys.exit(2)

    out, results = fill(bib)
    problems = verify(bib, out, results)
    read = pandoc_reads(out) if out != bib else None
    if read is not None and not read[0]:
        problems.append(f"pandoc cannot read the edited bib ({read[1]})")
    if problems:
        print("ERROR: the edited bib failed its own re-parse; nothing written:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        sys.exit(2)
    with open(a.out, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)

    for key, status, detail, source in results:
        if status in ("added", "filled_empty"):
            note = " (CrossRef: may not be the NLM form, check it)" if source == "CrossRef" else f" ({source})"
            print(f"  {key}: {LABELS[status]} {{{detail}}}{note}")
        elif status != "kept":
            print(f"  {key}: {LABELS[status]}" + (f" ({detail})" if detail else ""))

    def count(*statuses):
        return sum(1 for r in results if r[1] in statuses)

    def by_source(s):
        return sum(1 for r in results if r[1] in ("added", "filled_empty") and r[3] == s)

    print(f"shortjournal added: {count('added', 'filled_empty')} (PubMed {by_source('PubMed')}, "
          f"CrossRef {by_source('CrossRef')}); kept: {count('kept')}; no abbreviation found: "
          f"{count('not_found')}; lookup failed: {count('lookup_failed')}; skipped: "
          f"{count('no_journal', 'journal_not_editable', 'no_id', 'unsupported')}")
    print(f"written: {a.out}")
    if bbt:
        print("NOTE: this bib looks regenerated by Better BibTeX. Render from the --out file, or put the "
              "abbreviations in Zotero's 'Journal Abbr' field so the next export keeps them.", file=sys.stderr)
    caps = [e["key"] for e in parse_bib(bib)
            if e["key"] and re.search(r"\{?[A-Z]{3,}\}?,\s*\{?[A-Z]{3,}", _value(e, "author") or "")]
    if caps:
        print("WARN: ALL-CAPS author fields (fix case manually or re-pull):", caps)
    if count("lookup_failed"):
        print("Some lookups failed; those entries are unchanged. Re-run later.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
