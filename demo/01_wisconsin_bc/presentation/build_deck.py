#!/usr/bin/env python3
"""Demo 1 conference talk — 10 minutes. Every number read from analysis/tables/ at build time.

    python3 build_deck.py            # -> demo1_wisconsin_bc.pptx
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
sys.path.insert(0, str(DEMO.parent.parent / "skills" / "present-paper" / "templates"))

from build_pptx_nature_lancet import (          # noqa: E402
    new_presentation, add_title_slide, add_content_slide, add_closing_slide, fix_app_xml,
)

T = DEMO / "analysis" / "tables"
OUT = HERE / "demo1_wisconsin_bc.pptx"

acc = {r["Model"]: r for r in csv.DictReader((T / "diagnostic_accuracy.csv").open())}
lr = acc["Logistic Regression"]
stard = json.loads((DEMO / "qc" / "_stard_assessment.json").read_text()) \
    if (DEMO / "qc" / "_stard_assessment.json").exists() else {}
n_test = int(lr["TP"]) + int(lr["FP"]) + int(lr["FN"]) + int(lr["TN"])

prs = new_presentation()

add_title_slide(
    prs,
    eyebrow="DIAGNOSTIC ACCURACY",
    title=f"Three classifiers on fine-needle aspirate morphometry, "
          f"reported to STARD with DeLong intervals",
    subtitle=f"n = {n_test} held-out samples · histopathology as the reference standard",
    meta_top="MedSci Skills · Demo 1 · tooling demonstration, not a clinical claim",
    meta_bottom="Presenter · Affiliation",
    notes="10분입니다. 진단정확도 연구의 전형적 형태를 끝까지 돌린 예시입니다. "
          "데이터셋이 쉬워서 숫자 자체는 자랑거리가 아니고, 보실 것은 보고 방식입니다 — "
          "참조표준 정의, 흐름도, 구간, 그리고 체크리스트까지.")

add_content_slide(
    prs,
    title="The reference standard is histopathology, and the analysis unit is one aspirate",
    figure_path=DEMO / "figures" / "stard_flow.png",
    fig_caption=f"STARD 2015 participant flow. Stratified 70/30 split, seed 42; "
                f"{n_test} held-out ({int(lr['TP'])+int(lr['FN'])} malignant).",
    notes="STARD 흐름도입니다. 층화 분할에 시드가 기록돼 있고, 각 칸의 숫자는 표에서 그대로 나옵니다. "
          "분석 단위는 흡인검체 한 건이고 환자 중복은 없습니다.")

add_content_slide(
    prs,
    title=f"Logistic regression reached AUC {lr['AUC']} (95% CI {lr['AUC_lo']}–{lr['AUC_hi']})",
    figure_path=DEMO / "analysis" / "figures" / "roc_curve.png",
    fig_caption="Three models, DeLong 95% CIs. The benchmark is easy; the point is the reporting.",
    notes="세 모델 모두 AUC가 0.99대입니다. 이 데이터셋에서는 정상이고, 그래서 이 발표의 주장은 "
          "성능이 아닙니다. 구간은 DeLong으로 계산했고 표에서 읽습니다.")

add_content_slide(
    prs,
    title=f"At threshold 0.5, sensitivity {lr['Thr0.5_Sens']} and specificity {lr['Thr0.5_Spec']}",
    figure_path=DEMO / "analysis" / "figures" / "confusion_matrices.png",
    bullets=[
        f"**{lr['FN']} false negatives** of {int(lr['TP'])+int(lr['FN'])} malignant",
        f"Youden threshold {lr['Youden_thr']} would give "
        f"sens {lr['Youden_Sens']} / spec {lr['Youden_Spec']}",
    ],
    notes="임계값 0.5에서의 혼동행렬입니다. 위음성이 몇 건인지 세는 게 AUC보다 임상적으로 직접적입니다. "
          "Youden 임계값도 같이 보고하는데, 임계값 선택은 사후에 하면 낙관 편향이 생깁니다.")

add_closing_slide(
    prs,
    title="What the pipeline produced, and what it cannot claim",
    bullets=[
        "**Produced:** manuscript, STARD flow, DeLong CIs, checklist, self-review — no hand-typed numbers",
        "**Cannot claim:** clinical utility — a curated 1990s morphometry benchmark",
        "**Cannot claim:** generalisation — no external cohort",
    ],
    contact="demo/01_wisconsin_bc · every number in analysis/tables/",
    notes="파이프라인이 만든 것과 주장할 수 없는 것을 나눕니다. 외부 코호트가 없고 벤치마크가 "
          "정제된 것이라 임상 유용성은 주장하지 않습니다.")

prs.save(OUT)
fix_app_xml(OUT)
print(f"wrote {OUT}")
