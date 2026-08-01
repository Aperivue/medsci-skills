#!/usr/bin/env python3
"""Demo 2 conference talk — 10 minutes. Every number read from analysis/tables/ at build time.

    python3 build_deck.py            # -> demo2_bcg_meta_analysis.pptx
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

F = DEMO / "analysis" / "figures"
OUT = HERE / "demo2_bcg_meta_analysis.pptx"

m = {r["metric"]: r["value"] for r in csv.DictReader((DEMO / "analysis" / "tables" / "meta_results.csv").open())}


def f(key: str, nd: int = 3) -> str:
    return f"{float(m[key]):.{nd}f}"


prs = new_presentation()

add_title_slide(
    prs,
    eyebrow="META-ANALYSIS",
    title=f"BCG vaccination halved tuberculosis risk across {m['k_trials']} trials — "
          f"and the heterogeneity is the finding",
    subtitle=f"Random-effects RR {f('pooled_RR')} "
             f"({f('pooled_RR_lci')}–{f('pooled_RR_uci')}), I² {f('I2_percent', 1)}%",
    meta_top="MedSci Skills · Demo 2 · tooling demonstration, not a clinical claim",
    meta_bottom="Presenter · Affiliation",
    notes="10분입니다. 고전적인 BCG 데이터셋입니다. 통합 추정치는 위험을 절반으로 낮추지만, "
          "이 발표에서 정말 볼 것은 이질성입니다 — I²가 92%면 하나의 요약치를 그대로 읽는 게 "
          "정직하지 않습니다.")

add_content_slide(
    prs,
    title=f"Pooled RR {f('pooled_RR')} ({f('pooled_RR_lci')}–{f('pooled_RR_uci')})",
    figure_path=F / "forest.png",
    fig_caption=f"{m['k_trials']} trials, {int(float(m['total_participants'])):,} participants. "
                f"Random effects (REML), τ² {f('tau2')}.",
    notes="숲그림입니다. 시험별 추정치가 한쪽에 몰려 있지 않고 넓게 퍼져 있습니다. "
          "통합값 하나만 인용하면 그 퍼짐이 사라집니다.")

add_content_slide(
    prs,
    title=f"I² is {f('I2_percent', 1)}%, so the prediction interval is the honest summary",
    bullets=[
        f"**Prediction interval {f('pred_interval_lb')}–{f('pred_interval_ub')}** — it crosses 1",
        f"  Q = {f('Q', 1)} on {m['Q_df']} df · τ² = {f('tau2')}",
        "**A new trial could plausibly show no benefit.**",
    ],
    notes="핵심 슬라이드입니다. 신뢰구간은 평균 효과의 정밀도지만, 예측구간은 새 시험이 어디에 "
          "떨어질지를 말합니다. 그리고 그 구간은 1을 넘어갑니다. 통합 RR만 보고하면 이 사실이 "
          "보이지 않습니다.")

add_content_slide(
    prs,
    title="Small-study effects: Egger and rank tests both non-significant",
    figure_path=F / "funnel.png",
    bullets=[
        f"Egger z = {f('egger_z')}, p = {f('egger_p')}",
        f"Rank correlation τ = {f('ranktest_tau')}, p = {f('ranktest_p')}",
        f"**k = {m['k_trials']}: underpowered — absence of evidence, not evidence of absence.**",
    ],
    notes="깔때기 그림과 두 검정 모두 유의하지 않습니다. 다만 k가 13이면 이 검정들은 검정력이 "
          "낮습니다. '출판편향 없음'이 아니라 '이 표본으로는 판단 못 함'이 정확한 서술입니다.")

add_closing_slide(
    prs,
    title="What a pooled estimate hides, and what the pipeline enforced",
    bullets=[
        "**Hides:** a prediction interval crossing 1 despite a halved pooled risk",
        "**Enforced:** PRISMA flow, prediction interval, bias tests, leave-one-out",
        "**Not done:** per-study risk-of-bias and GRADE — out of scope, disclosed",
    ],
    contact="demo/02_metafor_bcg · every number in analysis/tables/meta_results.csv",
    notes="마무리입니다. 통합 추정치가 가리는 것과 파이프라인이 강제한 것을 나눕니다. "
          "연구별 비뚤림 평가와 GRADE는 범위 밖이고, 그 사실을 숨기지 않고 적었습니다.")

prs.save(OUT)
fix_app_xml(OUT)
print(f"wrote {OUT}")
