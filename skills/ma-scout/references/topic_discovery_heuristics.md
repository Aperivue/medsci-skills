# Topic Discovery Heuristics (Mode B)

Load this reference when `/ma-scout` T-Phase 0 starts from a user who asks for topic suggestions
without a specific idea.

1. **Trend scan** — Search recent high-IF radiology journals for "gap in the literature" + "meta-analysis needed":
   ```bash
   bash ${CLAUDE_SKILL_DIR}/../search-lit/references/pubmed_eutils.sh search \
     '"no meta-analysis" AND "radiology"[Journal] AND 2024:2026[dp]' 30
   ```

2. **Guideline update gaps** — New guidelines (ACR, ESR, RSNA) often cite lack of MA evidence:
   - Consensus search: `"practice guideline" AND "insufficient evidence" AND [radiology subspecialty]`

3. **AI + classical imaging** — Overlay AI/DL/radiomics on well-studied classical topics:
   - Many classical DTA topics have 10+ MAs, but AI angle has 0-1

4. **Korean/Asian population** — Population-specific MA for diseases with geographic variation:
   - TB, NTM, parasitic diseases, gastric cancer, liver fluke, HBV-related HCC

5. **Technology adoption** — New modalities with growing evidence but no synthesis:
   - Photon-counting CT, abbreviated MRI, contrast-enhanced mammography, AI CAD

6. **Cross-subspecialty** — Topics spanning two subspecialties often fall through MA cracks:
   - Cardiac + thoracic (coronary CT + lung screening), neuro + MSK (spine imaging)
