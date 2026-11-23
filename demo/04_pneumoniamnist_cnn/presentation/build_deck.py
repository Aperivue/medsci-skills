#!/usr/bin/env python3
"""Demo 4 conference talk, 10 minutes, on the medsci slide template.

    python3 build_deck.py                 # -> demo4_pneumoniamnist_cnn.pptx (pine palette, plain, white layouts)
    python3 build_deck.py --band OUT      # the same slides with the section band, written to OUT

Every number on a slide is read from results/ and qc/ at build time; none is typed in.
Slide text is English; speaker notes are Korean prose.

Emphasis, one meaning for the whole deck:  [[words]]   = the point of the slide (what to read);
                                           [[2|words]] = what it is set against.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

HERE = Path(__file__).resolve().parent
DEMO = HERE.parent
TEMPLATE = DEMO.parent.parent / "skills" / "present-paper" / "templates" / "slide_template"
sys.path.insert(0, str(TEMPLATE))

import build_slide_template as t      # noqa: E402
import new_deck as nd                 # noqa: E402

FIG = DEMO / "figures"
PALETTE = "pine"

res = json.loads((DEMO / "results" / "results.json").read_text())
cal = json.loads((DEMO / "results" / "calibration.json").read_text())
xai = json.loads((DEMO / "results" / "explainability.json").read_text())
leak = json.loads((DEMO / "qc" / "split_leakage.json").read_text())
hyg = json.loads((DEMO / "qc" / "training_hygiene.json").read_text())

assert leak["summary"]["verdict"] == "OK" and hyg["summary"]["verdict"] == "OK", "the gate slide says both passed"
assert xai["sanity_detail"]["passes"], "the Grad-CAM slide says both sanity checks passed"
assert xai["localization_metric"] == "none", "the limitation slide says there is no localisation metric"

ens = res["ensemble"]
auc_lo, auc_hi = ens["auroc_ci95"]
auroc = res["over_seeds_mean_sd"]["auroc"]
seeds = res["per_seed"]
n_test, prevalence = res["n_test"], res["prevalence"]
parts = leak["partitions"]
ece, brier = cal["ece"], cal["brier"]
sd = xai["sanity_detail"]
n_seeds = len(seeds)
WORDS = {2: "two", 3: "three", 4: "four", 5: "five"}


def f3(value):
    """Three decimals, as the manuscript prints them."""
    return f"{float(value):.3f}"


def r2(value):
    """Two decimals with a true minus sign, as the manuscript prints the correlations."""
    return f"{float(value):.2f}".replace("-", "−")


lo_auc, hi_auc = min(s["auroc"] for s in seeds), max(s["auroc"] for s in seeds)
lo_acc, hi_acc = min(s["accuracy"] for s in seeds), max(s["accuracy"] for s in seeds)
CREDIT = "PneumoniaMNIST images, MedMNIST v2, CC BY 4.0 (Yang et al. 2023)"

GATE_W = [3.0, 6.4, 2.83]                 # inches; the middle column carries the sentence
SEED_W = [3.0, 3.0, 3.0, 3.23]


# (layout, section name, {placeholder idx: text}, options)
SLIDES = [
    ("Cover", None,
     {0: "A reproducibility-gated CNN pipeline, end to end on a public benchmark",
      1: "Presenter", 14: "Department\nInstitution, City, Country",
      13: "MedSci Skills · Demo 4 · tooling demonstration"},
     dict(notes="10분입니다. 이 발표의 주장은 모델 성능이 아닙니다. PneumoniaMNIST는 쉬운 벤치마크이고 결과는 설계상 "
                "평범합니다. 주장은 파이프라인 쪽입니다. 누출 안전성, 시드 평균, 보정, 해석가능성 엄밀성을 사람의 "
                "성실함이 아니라 게이트로 강제할 수 있다는 것입니다.")),
    ("Disclosure", None, {0: "Disclosures", 1: "None", 13: "None"},
     dict(notes="이해관계와 연구비는 없습니다.")),
    ("Result · Table", "Gates",
     {0: "Two gates passed before any model was trained",
      13: "PneumoniaMNIST has no patient grouping, so the split is [[image-level]].",
      14: f"{parts['train']:,} train, {parts['val']} validation and {parts['test']} test images. qc/split_leakage.json, qc/training_hygiene.json"},
     dict(table=[["Gate", "What it checks", "Result"],
                 ["Split leakage", "Train, validation and test sets share no sample", "Passed"],
                 ["Training hygiene", "Seeded RNGs; eval() at inference", "Passed"]],
          widths=GATE_W,
          notes="학습 전에 두 게이트가 돌았습니다. 첫째는 분할 누출 검사로, 집합 연산으로 학습·검증·시험 표본이 겹치지 "
                "않음을 증명합니다. 둘째는 코드를 읽는 린터로, 시드가 안 걸린 난수 생성이나 추론 시 eval 모드 누락을 "
                "잡습니다. 둘 다 통과했습니다. 다만 이 벤치마크는 환자 단위 묶음이 없어서 표본 단위로만 증명됩니다. "
                "그 한계를 슬라이드에 남겨 둡니다.")),
    ("Result · Figure", "Results",
     {0: f"Test AUROC was {auroc['mean']:.3f} ± {auroc['sd']:.3f} over {WORDS.get(n_seeds, n_seeds)} seeds",
      14: f"Ensemble AUROC {f3(ens['auroc'])} (95% CI {f3(auc_lo)} to {f3(auc_hi)}), bootstrap {ens['bootstrap_n']:,}. "
          f"n = {n_test}, prevalence {f3(prevalence)}."},
     dict(picture=FIG / "fig2_roc.png", align="ctr",
          notes="세 시드 평균과 앙상블을 함께 보고합니다. MPS 백엔드가 완전한 결정론이 아니어서 단일 실행 숫자는 의미가 "
                "약합니다. 그림은 앙상블의 ROC 곡선이고, 구간은 시험 세트를 부트스트랩으로 다시 뽑아 얻었습니다. "
                "유병률이 0.625라 불균형이 있어서 AUPRC도 함께 봅니다.")),
    ("Result · Table", "Results",
     {0: "AUROC held across seeds; accuracy at 0.5 did not",
      13: f"AUROC spans [[{f3(lo_auc)} to {f3(hi_auc)}]]; accuracy spans [[2|{f3(lo_acc)} to {f3(hi_acc)}]].",
      14: f"Held-out test set, n = {n_test}. Accuracy at threshold 0.5. results/results.json"},
     dict(table=[["Seed", "AUROC", "AUPRC", "Accuracy"]]
          + [[str(s["seed"]), f3(s["auroc"]), f3(s["auprc"]), f3(s["accuracy"])] for s in seeds],
          widths=SEED_W,
          notes="시드별 결과입니다. 판별력인 AUROC는 세 시드에서 거의 같습니다. 반면 임계값 0.5의 정확도는 시드마다 "
                "꽤 달라서, 임계값에 의존하는 숫자는 한 번의 실행으로 믿기 어렵습니다. 그래서 평균과 표준편차를 "
                "함께 보고합니다.")),
    ("Result · Figure", "Results",
     {0: "High AUROC, yet the probabilities were over-confident",
      14: f"Expected calibration error {f3(ece)}, Brier {f3(brier)}. Temperature scaling was not applied."},
     dict(picture=FIG / "fig3_calibration.png", align="ctr",
          notes="가장 값어치 있는 출력이 모델을 더 나빠 보이게 만든 것이었습니다. 판별력은 좋은데 확률이 과신입니다. "
                "그림에서 곡선이 대각선 아래에 있습니다. 의사결정에 쓰려면 보정이 먼저 필요하고, 여기서는 하지 않았다고 "
                "분명히 밝힙니다.")),
    ("Result · Figure", "Results",
     {0: f"Grad-CAM passed both sanity checks (r = {r2(sd['mean_pearson_trained_vs_random_model'])}, "
         f"{r2(sd['mean_pearson_trained_vs_permuted_label_model'])})",
      14: f"{CREDIT}."},
     dict(picture=FIG / "fig4_gradcam.png", align="ctr",
          notes="살리언시가 학습된 가중치와 라벨에 실제로 의존하는지 두 가지 무작위화 검사로 확인했습니다. 무작위 모델이나 "
                "라벨을 섞어 학습한 모델의 지도와 상관이 거의 없었습니다. 그림 위쪽은 영상, 아래쪽은 겹친 지도입니다. "
                "다만 통과가 곧 모델이 옳다는 증거는 아닙니다.")),
    ("Limitations", "Limits",
     {0: "Why this is a demonstration, not a validation",
      13: "No external set", 16: "One small public benchmark; nothing here shows the result travels",
      14: "Image-level split", 17: "The gate proves disjoint images, not disjoint patients",
      15: "Attribution only", 18: f"No lesion masks, so no localisation metric; maps are not proof"},
     dict(notes="한계 세 가지입니다. 외부 자료가 없다는 것, 분할이 표본 단위라는 것, 그리고 병변 마스크가 없어서 "
                "국소화 지표를 계산할 수 없고 Grad-CAM은 귀속일 뿐 증거가 아니라는 것입니다. 외부 검증이 가장 큰 "
                "빈칸입니다.")),
    ("Take-home", "Summary",
     {0: "What to take from this",
      1: ["Two gates passed before any training",
          "[[AUROC]] held; [[2|calibration]] did not",
          "Grad-CAM is attribution, not proof"]},
     dict(notes="정리합니다. 게이트는 학습 전에 두 개가 통과했습니다. 판별력은 유지됐지만 보정은 그렇지 않았고, "
                "Grad-CAM은 귀속일 뿐 증거가 아닙니다. 이 슬라이드의 숫자는 모두 결과 파일에서 읽어 온 것이라 "
                "결과가 바뀌면 덱도 같이 바뀝니다.")),
]


def build(out, band=False):
    out = Path(out)
    nd.make_deck(out, palette=PALETTE, band=band, force=True)
    prs = Presentation(out)
    lay = {l.name: l for l in prs.slide_layouts}
    for name, section, content, opt in SLIDES:
        s = prs.slides.add_slide(lay[name])
        slot = {p.placeholder_format.idx: p for p in s.placeholders}
        for idx, value in content.items():
            nd.put_rich(slot[idx], value)
        if section and 20 in slot:
            nd.fill(slot[20], section)
        if "picture" in opt:
            nd.fit_picture(slot[30], opt["picture"], opt.get("align", "l"), trim=True)
        if "table" in opt:
            rows = opt["table"]
            tbl = t.plain_table(slot[21], len(rows), len(rows[0]), rows[0])
            for col, width in zip(tbl.columns, opt["widths"]):
                col.width = Inches(width)
            for r, row in enumerate(rows[1:], start=1):
                for c, text in enumerate(row):
                    t.set_cell(tbl, r, c, text)
        tf = s.notes_slide.notes_text_frame
        tf.text = opt["notes"]
        nd.set_lang(tf)
    nd.drop_empty_bands(prs)
    prs.save(out)
    t.post_process(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--band", metavar="OUT", help="write the same slides with the section band to OUT")
    a = ap.parse_args()
    print("wrote", build(a.band, band=True) if a.band else build(HERE / "demo4_pneumoniamnist_cnn.pptx"))
