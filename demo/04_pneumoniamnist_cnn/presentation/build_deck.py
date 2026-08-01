#!/usr/bin/env python3
"""Demo 4 conference talk — 10 minutes, one finding, defensibly.

Every number on a slide is read at build time from `results/`; nothing is typed into this file.

    python3 build_deck.py            # -> demo4_pneumoniamnist_cnn.pptx
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
sys.path.insert(0, str(DEMO.parent.parent / "skills" / "present-paper" / "templates"))

from build_pptx_nature_lancet import (          # noqa: E402
    new_presentation, add_title_slide, add_content_slide, add_closing_slide, fix_app_xml,
)

FIG = DEMO / "figures"
OUT = HERE / "demo4_pneumoniamnist_cnn.pptx"

res = json.loads((DEMO / "results" / "results.json").read_text())
cal = json.loads((DEMO / "results" / "calibration.json").read_text())
xai = json.loads((DEMO / "results" / "explainability.json").read_text())
leak = json.loads((DEMO / "qc" / "split_leakage.json").read_text())
hyg = json.loads((DEMO / "qc" / "training_hygiene.json").read_text())

ens = res["ensemble"]
auc_lo, auc_hi = ens["auroc_ci95"]
mean_sd = res["over_seeds_mean_sd"]


ece, brier = cal["ece"], cal["brier"]
sd = xai["sanity_detail"]
r_model = sd["mean_pearson_trained_vs_random_model"]
r_label = sd["mean_pearson_trained_vs_permuted_label_model"]
auroc = mean_sd["auroc"]

prs = new_presentation()

add_title_slide(
    prs,
    eyebrow="MODEL ENGINEERING",
    title="A reproducibility-gated CNN pipeline, end to end on a public benchmark",
    subtitle="Gates before training · seeds averaged · calibration and saliency checked",
    meta_top="MedSci Skills · Demo 4 · tooling demo, not a clinical claim",
    meta_bottom="Presenter · Affiliation",
    notes="10분입니다. 이 발표의 주장은 모델 성능이 아닙니다 — PneumoniaMNIST는 쉬운 벤치마크고 "
          "결과는 설계상 평범합니다. 주장은 파이프라인 쪽입니다: 누출 안전성, 시드 평균, 보정, "
          "해석가능성 엄밀성을 사람의 성실함이 아니라 게이트로 강제할 수 있다는 것입니다.")

add_content_slide(
    prs,
    title="The convenience of scaffolding can outrun the rigour",
    bullets=[
        "**Image-level splits · unseeded RNGs · dropout on at inference**",
        "  Uncalibrated probabilities read as trustworthy",
        "  Saliency offered as proof the model is right",
        "**All documented. All silent.**",
    ],
    notes="스캐폴딩이 쉬워질수록 엄밀성이 뒤처지는 게 위험입니다. 여기 나열한 실패들은 전부 문헌에 "
          "기록돼 있고, 공통점은 발생할 때 아무 소리도 안 난다는 겁니다.")

add_content_slide(
    prs,
    title="Two gates ran before a single epoch, and both had to pass",
    bullets=[
        f"**Split leakage** — disjoint by set arithmetic: {leak['summary']['verdict']}",
        f"**Training hygiene** — AST linter over the repo: {hyg['summary']['verdict']}",
        "  Every RNG seeded · cuDNN deterministic · eval() at inference",
        "**Image-level here; patient-level on a patient dataset.**",
    ],
    notes="학습 전에 두 게이트가 돌았습니다. 두 번째는 AST 린터라 코드를 읽습니다 — 시드가 안 걸린 "
          "RNG, 추론 시 eval 모드 누락 같은 걸 잡습니다. 그리고 이 벤치마크는 환자 단위가 없어서 "
          "샘플 단위로만 증명됩니다. 그 한계를 슬라이드에 남겨둡니다.")

add_content_slide(
    prs,
    title=f"Test AUROC {auroc['mean']:.3f} ± {auroc['sd']:.3f} over three seeds",
    figure_path=FIG / "fig2_roc.png",
    fig_caption=f"Ensemble AUROC {ens['auroc']:.3f} (95% CI {auc_lo:.3f}–{auc_hi:.3f}), "
                f"bootstrap 2,000. n = {res['n_test']}, prevalence {res['prevalence']}.",
    notes="세 시드 평균과 앙상블을 함께 보고합니다. MPS 백엔드가 완전 결정론적이 아니라 단일 실행 "
          "숫자는 의미가 약합니다. AUPRC도 같이 봅니다 — 유병률이 0.625라 불균형이 있습니다.")

add_content_slide(
    prs,
    title="The most useful gate output was the one that made the model look worse",
    figure_path=FIG / "fig3_calibration.png",
    bullets=[
        f"**ECE {ece:.3f}** · Brier {brier:.3f}",
        "  A 0.97-AUROC classifier that is over-confident",
        "**Temperature scaling is the remedy — not applied, and said so.**",
    ],
    notes="가장 값어치 있는 출력이 모델을 더 나빠 보이게 만든 것이었습니다. 판별력은 좋은데 확률이 "
          "과신입니다. 의사결정에 쓰려면 보정이 선행돼야 하고, 여기서는 안 했다고 명시했습니다.")

add_content_slide(
    prs,
    title="Grad-CAM passed both Adebayo sanity checks — and is still only attribution",
    figure_path=FIG / "fig4_gradcam.png",
    bullets=[
        f"Model randomisation r **{r_model:+.2f}** · label permutation r **{r_label:+.2f}**",
        "  The maps depend on learned weights, not edges",
        "**No masks, so `localization_metric: none` — attribution, not proof.**",
    ],
    notes="살리언시가 학습된 가중치에 실제로 의존하는지 두 가지 무작위화 검사로 확인했습니다. "
          "그런데 통과했다고 '모델이 옳다'는 증거가 되지는 않습니다. 이 벤치마크에는 병변 마스크가 "
          "없어서 정량적 국소화 지표 자체를 계산할 수 없습니다. 게이트가 그 표현을 강제했습니다.")

add_closing_slide(
    prs,
    title="What the gates bought, and what they did not",
    bullets=[
        "**Bought:** leakage-safety, seed-averaging, calibration, XAI rigour",
        "**Did not:** external validation — one 28×28 benchmark",
        "**Did not:** any clinical claim",
        "**Next:** Demo 5 is the external counterpart",
    ],
    contact="demo/04_pneumoniamnist_cnn · every number in results/results.json",
    notes="마무리입니다. 게이트가 사준 것과 사주지 못한 것을 나눕니다. 외부 검증이 없다는 게 가장 큰 "
          "빈칸이고, 그건 Demo 5가 답합니다.")

prs.save(OUT)
fix_app_xml(OUT)
print(f"wrote {OUT}")
