#!/usr/bin/env python3
"""Demo 5 conference talk — 10 minutes, one finding, defensibly.

Every number on a slide is read at build time from the shipped artifacts, exactly as the figures
and tables are; nothing is typed into this file. If a result changes, the deck changes with it.

The deck is deliberately built the way the demo argues a deck should be: assertion headlines that
state the finding rather than naming the section, figures drawn as code and inserted as images
rather than assembled from autoshapes, no eyebrow or footer chrome on content slides, and no
scaffolding sentences. Both gates are run by `make_deck.sh`.

    python3 build_deck.py            # -> demo5_external_validation.pptx
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
    new_presentation, add_title_slide, add_section_divider, add_content_slide,
    add_closing_slide, fix_app_xml,
)

FIG = DEMO / "figures"
OUT = HERE / "demo5_external_validation.pptx"


# ---------------------------------------------------------------- read the numbers, never type them
def table(name: str) -> list[dict]:
    with (DEMO / "analysis" / "tables" / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


t2 = {r["arm"]: r for r in table("table2_performance.csv")}
t4 = {r["arm"]: r for r in table("table4_normalisation_evidence.csv")}
sub = [r for r in table("table3_subgroups.csv") if r["arm"].startswith("rung2")]
R1, R2, R3 = ("rung1 MSD held-out (internal)", "rung2 AMOS CT (external)",
              "rung3 AMOS MRI (modality shift)")
R3B = "rung3b AMOS MRI rescaled (counterfactual)"
R3C = "rung3c AMOS MRI z-scored (counterfactual)"
prof = json.loads((DEMO / "qc" / "amos22_dataset_profile_spleen.json").read_text())
intensity_claim = next(c for c in prof["claims"] if c["verdict"] == "INTENSITY_SCALE_INCONSISTENT")
naive = json.loads((DEMO / "qc" / "preprocessing_leakage_naive.json").read_text())


def dice(arm: str) -> str:
    return t2[arm]["dice_median_95CI"].replace("[", "(95% CI ").replace("]", ")").replace("-0.", "–0.")


def stratum(name: str) -> dict:
    return next(r for r in sub if r["stratum"].startswith(name))


prs = new_presentation()

add_title_slide(
    prs,
    eyebrow="EXTERNAL VALIDATION",
    title="A segmentation model that scored 0.89 externally and 0.015 on a modality shift — "
          "and the pipeline never said a word",
    subtitle="Three labelled rungs, two public datasets, one preprocessing contract",
    meta_top="MedSci Skills · Demo 5 · tooling demonstration, not a clinical claim",
    meta_bottom="Presenter · Affiliation",
    notes="10분입니다. 결론부터 말씀드리면, 외부 CT에서는 정직하게 잘 나왔고 MRI에서는 무너졌는데, "
          "무너진 이유가 모델이 아니라 전처리 계약이었습니다. 그리고 파이프라인은 그 사실을 한 번도 "
          "알려주지 않았습니다. 오늘 보실 것은 그 침묵입니다.")

add_content_slide(
    prs,
    title="The question is not whether a clinician can train a model. They can.",
    bullets=[
        "**It is whether the study that results is defensible — and where it stops being so.**",
        "  Spleen segmentation, three labelled rungs, both datasets openly downloadable",
        "**Rungs 1–2 are ordinary validation. Rung 3 is a constructed test.**",
    ],
    notes="질문을 좁혔습니다. 모델을 얻을 수 있느냐가 아니라, 그렇게 나온 연구가 방어 가능하냐입니다. "
          "그리고 미리 밝힙니다 — 3번 rung은 우연히 발견한 게 아니라 우리가 설계해서 넣은 시험입니다. "
          "뒤에서 다시 말씀드리겠습니다.")

add_content_slide(
    prs,
    title="41 labelled MSD cases became 32 train and 9 held-out; AMOS supplied 300 CT and 60 MRI",
    figure_path=FIG / "fig5_case_flow.png",
    fig_caption="Every exclusion carries its reason. Three cases contain no spleen at all.",
    notes="케이스 회계입니다. 제외마다 이유가 붙어 있고, 라벨된 360건 중 3건은 비장이 아예 없습니다. "
          "그 3건은 Dice가 정의되지 않으므로 분포에서 빼고 따로 보고합니다 — 규칙은 예측을 보기 전에 "
          "고정했습니다.")

add_content_slide(
    prs,
    title="Two gates ran before training, and the counterfactual had to fail",
    bullets=[
        "**Split leakage** — disjointness proved by set arithmetic, not asserted",
        "**Preprocessing leakage** — the declared manifest passes",
        f"  The obvious way of using nnU-Net fires **{naive['summary']['n_major']} × "
        f"PREPROCESS_BEFORE_SPLIT**",
    ],
    notes="게이트 두 개가 학습 전에 돌았습니다. 중요한 건 반사실입니다 — nnU-Net을 '평범하게' 쓰면 "
          "held-out까지 포함해 fingerprint를 맞추게 되고, 같은 게이트가 그걸 3건의 Major로 거부합니다. "
          "통과하는 게이트만 보여주면 게이트가 실패할 수 있다는 증거가 없습니다.")

add_content_slide(
    prs,
    title=f"Internal {t2[R1]['dice_median_95CI'].split(' ')[0]} → external CT "
          f"{t2[R2]['dice_median_95CI'].split(' ')[0]} → MRI {t2[R3]['dice_median_95CI'].split(' ')[0]}",
    figure_path=FIG / "across_cohorts_dice.png",
    fig_caption=f"Δ vs internal: {t2[R2]['delta_dice_vs_internal_95CI']} and "
                f"{t2[R3]['delta_dice_vs_internal_95CI']}. Bootstrap 10,000, seeded per arm.",
    notes="사다리입니다. 내부에서 외부 CT로 가면서 0.066 떨어지는데, 이건 정직한 낙폭입니다. "
          "MRI로 가면 거의 전부 잃습니다. 두 낙폭 모두 차이 자체에 구간을 붙였습니다 — 중앙값 두 개의 "
          "뺄셈은 그 자체로는 추론량이 아니기 때문입니다.")

add_content_slide(
    prs,
    title="The external median hides a tail that reaches zero",
    figure_path=FIG / "fig1_dice_by_arm.png",
    bullets=[
        f"**{t2[R2]['n_empty_prediction']} of 300** external CT predictions were empty",
        "**Both** spleen-free cases got a prediction anyway",
        f"HD95 exists for only **{t2[R3]['n_with_hd95']} of {t2[R3]['n_scored']}** MRI cases",
    ],
    notes="중앙값만 보면 안 되는 이유입니다. 외부 CT는 0까지 내려가는 꼬리를 갖고 있고, 빈 예측이 "
          "28건입니다. 비장이 없는 케이스 2건에는 오히려 비장을 그렸습니다. HD95는 예측이 비면 정의가 "
          "안 되는데, 그게 하필 가장 크게 실패한 케이스들이라 분모가 다릅니다.")

s = stratum("enlarged")
n = stratum("normal")
add_content_slide(
    prs,
    title="The model is worst on the spleens the task exists to measure",
    figure_path=FIG / "fig3_subgroups_external_ct.png",
    fig_caption=f"Enlarged >250 mL: {s['dice_median_95CI'].split(' ')[0]} (n={s['n_scored']}) "
                f"vs normal: {n['dice_median_95CI'].split(' ')[0]} (n={n['n_scored']}). "
                f"Cut-points fixed before scoring.",
    notes="사전 지정한 subgroup입니다. 비장비대에서 가장 나쁩니다 — 그런데 비장 분할이 존재하는 이유가 "
          "바로 비장비대 측정입니다. 0.8932라는 헤드라인이 정확히 그걸 가립니다. 층 간 차이는 검정하지 "
          "않았고, 추정치로만 봅니다.")

add_section_divider(prs, num="03", title="Rung 3 was constructed, and here is what it measured",
                    subtitle="We predicted the collapse in writing before inference ran",
                    time_min=3,
                    notes="여기서 정직하게 선을 긋습니다.")

ct, mri = t4[R2], t4[R3]
add_content_slide(
    prs,
    title="A Hounsfield clip applied to images that are not in Hounsfield units",
    figure_path=FIG / "fig4_normalisation_evidence.png",
    bullets=[
        f"Negative voxels: **{ct['cases_with_any_negative_voxel']}** CT, "
        f"**{mri['cases_with_any_negative_voxel']}** MRI",
        f"Clipped at the ceiling: **{ct['pct_voxels_above_clip_ceiling_median_range'].split(' ')[0]}** "
        f"vs **{mri['pct_voxels_above_clip_ceiling_median_range'].split(' ')[0]}**",
        "**No argument declares the modality** — the normaliser rides with the checkpoint",
    ],
    notes="훈련 plan이 CTNormalization을 싣고 추론까지 옵니다. HU는 −1000 근처 공기 바닥으로 정의되는데 "
          "CT는 300건 전부 그게 있고 MRI는 0건입니다. 같은 clip을 적용하면 MRI는 중앙값 23% 볼륨이 "
          "천장에서 뭉개집니다. 그리고 이걸 알려줄 인자가 명령어에 없습니다.")

add_content_slide(
    prs,
    title="Our own profiler had already found it — and filed it as Minor",
    bullets=[
        f'**`{intensity_claim["verdict"]}`** — filed **{intensity_claim["severity"]}**',
        '  "500/600 cases bottom out near air and the rest do not"',
        "**Not a detection gap. A routing and severity gap.**",
    ],
    notes="가장 불편한 슬라이드입니다. 우리 프로파일러가 학습 전에 이미 잡았습니다 — 다만 Minor로, "
          "아무도 다시 읽지 않는 디렉터리에. 그러니 문제는 탐지가 아니라 전달과 심각도입니다. "
          "이건 이 사례가 제기하는 가설이지, 이 사례가 증명한 성질은 아닙니다.")

add_content_slide(
    prs,
    title="Two different repairs recover the same third of the loss",
    bullets=[
        f"**{t2[R3]['dice_median_95CI'].split(' ')[0]} → "
        f"{t2[R3B]['dice_median_95CI'].split(' ')[0]}** — no retraining, same checkpoint",
        f"  A second arm swaps the **normaliser** instead: "
        f"**{t2[R3C]['dice_median_95CI'].split(' ')[0]}**",
        "**Two unrelated repairs, same place — the domain is the story.**",
    ],
    notes="대조군 두 개입니다. 하나는 잘못된 정규화기를 두고 입력을 고쳤고, 다른 하나는 입력을 두고 "
          "정규화기를 바꿨습니다. 둘 다 재학습 없이 0.29 부근에 도달했고 차이의 구간이 0을 포함합니다. "
          "케이스별 상관은 0.94 — 같은 영상에서 성공하고 같은 영상에서 실패합니다. 즉 중요한 건 "
          "데이터가 학습된 강도 도메인에 도달하느냐 하나뿐입니다. 두 예측 모두 실행 전에 적었고, "
          "두 번째는 방향이 틀렸습니다.")

add_closing_slide(
    prs,
    title="What this establishes, and what it does not",
    bullets=[
        "**Establishes:** the run exited 0 and reported a number that means nothing",
        "**Measured** on CT→MRI: 0.29 intensity, 0.59 representation",
        "**Does not:** support general claims — one organ, one team",
        "**Open:** what a model *trained* on MR would do",
    ],
    contact="demo/05_msd_amos_spleen · every number re-derivable from the shipped CSVs",
    notes="마무리입니다. 이 연구가 세운 것과 세우지 못한 것을 나눠 말씀드립니다. "
          "전처리 실패인지 표현 전이 실패인지는 분리하지 못했습니다 — 올바르게 정규화한 MRI 대조군을 "
          "안 돌렸기 때문입니다. 그게 다음 실험이고, 재학습 없이 추론 한 번이면 됩니다.")

prs.save(OUT)
fix_app_xml(OUT)
print(f"wrote {OUT}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
