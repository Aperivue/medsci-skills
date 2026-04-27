#!/usr/bin/env bash
# Fetch official reporting guideline flow diagram / figure templates from
# the canonical statement sites (PRISMA, CONSORT, STARD, SPIRIT).
#
# Idempotent: skips downloads when target already exists with non-zero size.
# Network failures are non-fatal; the script reports per-target status at the end.
#
# Usage:
#   bash scripts/fetch_official_templates.sh                  # fetch all
#   bash scripts/fetch_official_templates.sh prisma2020       # one target
#   FORCE=1 bash scripts/fetch_official_templates.sh          # re-download
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_ROOT="${SKILL_DIR}/templates/official"
mkdir -p "${DEST_ROOT}"

UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Claude-Code-medsci-skills/1.0'

# target_id|filename|url
# URLs verified 2026-04-27. PRISMA 2020 from prismastatement.org/s/.
# CONSORT/SPIRIT migrated to consort-spirit.org (formerly consort-statement.org +
# spirit-statement.org). STARD provides PDF only — checklist .docx fetched as
# the closest official Word artifact; flow diagram remains PDF.
TARGETS=(
  # PRISMA 2020 — both new-SR and updated-SR, both v1 (databases/registers only)
  # and v2 (incl. other sources). Official .docx, CC-BY 4.0.
  "prisma2020|PRISMA_2020_flow_new_SR_v1.docx|https://prismastatement.org/s/PRISMA_2020_flow_diagram_new_SRs_v1-lml8.docx"
  "prisma2020|PRISMA_2020_flow_new_SR_v2.docx|https://prismastatement.org/s/PRISMA_2020_flow_diagram_new_SRs_v2-t3jp.docx"
  "prisma2020|PRISMA_2020_flow_updated_SR_v1.docx|https://prismastatement.org/s/PRISMA_2020_flow_diagram_updated_SRs_v1-f8ly.docx"
  "prisma2020|PRISMA_2020_flow_updated_SR_v2.docx|https://prismastatement.org/s/PRISMA_2020_flow_diagram_updated_SRs_v2-dbrh.docx"

  # CONSORT 2025 (supersedes 2010) — main flow diagram + editable checklist
  "consort2010|CONSORT_2025_flow_diagram.docx|https://www.consort-spirit.org/_files/ugd/b5740e_019fabb52c9a4894abb681afcbff41f8.docx?dn=CONSORT_2025_flow_diagram.docx"
  "consort2010|CONSORT_2025_editable_checklist.docx|https://www.consort-spirit.org/_files/ugd/b628c8_6fa59b2c6db04efb9a9d0bc967a9fcf7.docx?dn=CONSORT%20%202025%20editable%20checklist.docx"

  # STARD 2015 — flow diagram is published as PDF only (no official Word source).
  # Ship the checklist .docx + the flow PDF as the canonical bundle.
  "stard2015|STARD_2015_flow_diagram.pdf|https://www.equator-network.org/wp-content/uploads/2015/03/STARD-2015-flow-diagram.pdf"
  "stard2015|STARD_2015_checklist.docx|https://www.equator-network.org/wp-content/uploads/2015/10/STARD-2015-Checklist.docx"

  # SPIRIT 2025 (supersedes 2013) — participant timeline + editable checklist
  "spirit2013|SPIRIT_2025_participant_timeline.docx|https://www.consort-spirit.org/_files/ugd/b5740e_5fad4e7a16bf44f6a2a0a809ad2a2e9d.docx?dn=SPIRIT%202025%20participant%20timeline.docx"
  "spirit2013|SPIRIT_2025_editable_checklist.docx|https://www.consort-spirit.org/_files/ugd/b5740e_667c45b02102408ab983c9704525597b.docx?dn=SPIRIT%202025%20editable%20checklist.docx"
)

WANT="${1:-all}"
FORCE="${FORCE:-0}"

declare -a ok_list fail_list skip_list

for entry in "${TARGETS[@]}"; do
  IFS='|' read -r tid fname url <<<"${entry}"
  if [[ "${WANT}" != "all" && "${WANT}" != "${tid}" ]]; then
    continue
  fi
  out="${DEST_ROOT}/${tid}/${fname}"
  if [[ "${FORCE}" != "1" && -s "${out}" ]]; then
    skip_list+=("${tid}/${fname}")
    continue
  fi
  echo "→ ${tid}/${fname}"
  if curl -fsSL --retry 2 --max-time 30 -A "${UA}" -o "${out}.tmp" "${url}"; then
    if [[ -s "${out}.tmp" ]]; then
      mv "${out}.tmp" "${out}"
      ok_list+=("${tid}/${fname}")
    else
      rm -f "${out}.tmp"
      fail_list+=("${tid}/${fname} (empty)")
    fi
  else
    rm -f "${out}.tmp"
    fail_list+=("${tid}/${fname} (HTTP)")
  fi
done

echo
echo "── fetch summary ─────────────────────────────"
printf 'OK   : %s\n' "${ok_list[@]:-(none)}"
printf 'SKIP : %s\n' "${skip_list[@]:-(none)}"
printf 'FAIL : %s\n' "${fail_list[@]:-(none)}"

if [[ ${#fail_list[@]} -gt 0 ]]; then
  echo
  echo "Some downloads failed. Statement sites occasionally rotate URLs;"
  echo "verify at: https://www.equator-network.org/reporting-guidelines/"
  exit 2
fi
