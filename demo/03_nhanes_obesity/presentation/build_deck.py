#!/usr/bin/env python3
"""Demo 3 conference talk — 10 minutes. Every number read from analysis/tables/ at build time.

    python3 build_deck.py            # -> demo3_nhanes_obesity.pptx
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
sys.path.insert(0, str(DEMO.parent.parent / "skills" / "present-paper" / "templates"))

from build_pptx_nature_lancet import (          # noqa: E402
    new_presentation, add_title_slide, add_content_slide, add_closing_slide, fix_app_xml,
)

T = DEMO / "analysis" / "tables"
F = DEMO / "analysis" / "figures"
OUT = HERE / "demo3_nhanes_obesity.pptx"

k = {r["metric"]: r["value"] for r in csv.DictReader((T / "key_scalars.csv").open())}
casc = list(csv.DictReader((T / "exclusion_cascade.csv").open()))


def f(key: str, nd: int = 2) -> str:
    return f"{float(k[key]):.{nd}f}"


prs = new_presentation()

add_title_slide(
    prs,
    eyebrow="SURVEY EPIDEMIOLOGY",
    title=f"Obesity carried a {f('aOR_obesity')}-fold adjusted odds of diabetes "
          f"in US adults — with the survey design respected",
    subtitle=f"NHANES 2017–2018, analytic n = {int(float(k['analytic_N'])):,}, "
             f"MEC-weighted with strata and PSUs",
    meta_top="MedSci Skills · Demo 3 · tooling demonstration, not a clinical claim",
    meta_bottom="Presenter · Affiliation",
    notes="10분입니다. 복합표본 설계를 무시하고 그냥 로지스틱을 돌리는 게 이 분야에서 가장 흔한 "
          "실수입니다. 여기서는 가중치·층·PSU를 전부 반영했고, 그래서 구간이 단순 분석보다 넓습니다.")

add_content_slide(
    prs,
    title=f"{int(float(k['analytic_N'])):,} adults remained after a stated exclusion cascade",
    figure_path=F / "strobe_flow.png",
    fig_caption="STROBE participant flow. Every exclusion carries its reason and its count; "
                "the cascade sums to the analytic N.",
    notes="STROBE 흐름도입니다. 제외마다 이유와 숫자가 붙고, 빼기가 정확히 분석 대상 수로 떨어집니다. "
          "이 산술이 안 맞으면 아래 모든 숫자가 의심스러워집니다.")

add_content_slide(
    prs,
    title=f"Weighted prevalence: obesity {f('weighted_obesity_prev_pct', 1)}%, "
          f"diabetes {f('weighted_diabetes_prev_pct', 1)}%",
    bullets=[
        f"Obesity {f('weighted_obesity_prev_pct', 1)}% "
        f"({f('weighted_obesity_ci_lo', 1)}–{f('weighted_obesity_ci_hi', 1)})",
        f"Diabetes {f('weighted_diabetes_prev_pct', 1)}% "
        f"({f('weighted_diabetes_ci_lo', 1)}–{f('weighted_diabetes_ci_hi', 1)})",
        "**Unweighted counts would not estimate the US population at all.**",
    ],
    notes="가중 유병률입니다. NHANES는 특정 집단을 과대표집하므로 가중치 없이 센 비율은 "
          "미국 인구를 추정하지 않습니다. 구간도 설계를 반영해 계산했습니다.")

add_content_slide(
    prs,
    title=f"Adjusted OR {f('aOR_obesity')} ({f('aOR_obesity_ci_lo')}–{f('aOR_obesity_ci_hi')})",
    figure_path=F / "forest_or.png",
    fig_caption=f"Design-based logistic regression; p = {float(k['aOR_obesity_p']):.4f}. "
                f"Covariates listed in Methods.",
    notes="조정 오즈비입니다. 설계 기반 회귀라 표준오차가 단순 무작위표본 가정보다 큽니다. "
          "공변량 목록은 Methods에 있고, 무엇을 왜 넣었는지가 이 표의 신뢰도를 결정합니다.")

add_closing_slide(
    prs,
    title="Cross-sectional, so association — and the wording is enforced",
    bullets=[
        "**Cannot claim:** that obesity caused diabetes — exposure and outcome measured together",
        "**Cannot claim:** a screening or surveillance interval from a single time point",
        "**Enforced:** a scope gate blocks prognostic verbs on a cross-sectional design",
    ],
    contact="demo/03_nhanes_obesity · every number in analysis/tables/key_scalars.csv",
    notes="마무리입니다. 단면연구라 연관성까지만 말할 수 있고, 그건 취향이 아니라 설계의 한계입니다. "
          "이 repo는 단면 설계에 예후 동사가 붙으면 게이트가 막습니다.")

prs.save(OUT)
fix_app_xml(OUT)
print(f"wrote {OUT}")
