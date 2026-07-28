# Challenge — portal-field markdown residue

## The defect this gate catches

A portal-field text file (`abstract.txt`, `keywords.txt`, …) is cut from the
manuscript markdown so the author can paste it straight into an Editorial Manager /
ScholarOne free-text field. Nothing strips the markdown at that boundary, so a
trailing `---`, a stray `**bold**`, or a `cm^2^` superscript pastes into — and is
published in — the field literally.

Real instance: three portal-field files each ended with a `---` line; the author is
told to paste the file verbatim, so `---` would have printed in the published abstract.

Only `.txt` files are scanned — a `.md` is *meant* to carry markdown, so it is out of
scope. That single scope decision is what keeps the gate precise.

## Fixtures

**Positive** (`fixture/positive/`): two paste-verbatim files carrying, between them,
all six residue kinds — a trailing `---` (hr), `**primary**` (bold), `cm^2^`
(superscript), `[our repository](url)` (link), `# Take-home points` (heading), and
`H~2~O` (subscript). Exit 1.

**Negative** (`fixture/negative/`): clean plain text that deliberately includes the
false-positive traps — significance stars `* p<0.05 and ** p<0.01` (space after the
pair), an approximation tilde `~5%`, a numeric range `1~2 days`, a hyphenated
`risk-factor`, and a bare `https://` URL. None of these is paired markdown, so nothing
fires. Exit 0.

## Verify

`bash verify.sh` — deterministic, network-free. Asserts the positive fixture flags all
six kinds (exit 1) and the negative fixture is clean (exit 0).
