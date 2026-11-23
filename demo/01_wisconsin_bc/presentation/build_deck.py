#!/usr/bin/env python3
"""Demo 1 conference talk, 10 minutes, on the medsci slide template.

    python3 build_deck.py                 # -> demo1_wisconsin_bc.pptx (pine palette, section band)
    python3 build_deck.py --plain OUT     # the same slides without the band, for the comparison image

Every number on a slide is read from analysis/tables/ and data/ at build time; none is typed in.
Slide text is English; speaker notes are Korean prose.
"""
from __future__ import annotations

import argparse
import csv
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

TABLES = DEMO / "analysis" / "tables"
PALETTE = "pine"

acc = {r["Model"]: r for r in csv.DictReader((TABLES / "diagnostic_accuracy.csv").open())}
delong = list(csv.DictReader((TABLES / "auc_comparison_delong.csv").open()))
lr = acc["Logistic Regression"]
table1 = list(csv.DictReader((TABLES / "table1_features_by_class.csv").open()))
diagnosis = [r["diagnosis"] for r in csv.DictReader((DEMO / "data" / "wisconsin_breast_cancer.csv").open())]
n_all, n_mal = len(diagnosis), diagnosis.count("malignant")
with (DEMO / "data" / "wisconsin_breast_cancer.csv").open() as fh:
    n_feat = len(next(csv.reader(fh))) - 2          # every column but target and diagnosis
n_test = sum(int(lr[k]) for k in ("TP", "FP", "FN", "TN"))
test_mal, test_ben = int(lr["TP"]) + int(lr["FN"]), int(lr["FP"]) + int(lr["TN"])
p_lo, p_hi = min(float(r["DeLong_p"]) for r in delong), max(float(r["DeLong_p"]) for r in delong)
assert all(float(r["DeLong_p"]) > 0.05 for r in delong), "the 'no difference' slides assume every DeLong p > 0.05"
best_brier = min(acc.values(), key=lambda r: float(r["Brier"]))
assert best_brier is lr, "the calibration line names logistic regression"
worst_brier = max(acc.values(), key=lambda r: float(r["Brier"]))


def f3(value):
    """Three decimals, as the manuscript prints them (the tables store 1.0 and 0.02)."""
    return f"{float(value):.3f}"


def ci(row, key):
    return f"{f3(row[key])} ({f3(row[key + '_lo'])} to {f3(row[key + '_hi'])})"


COL_W = [2.7, 3.5, 2.0, 2.0, 2.03]     # inches; the interval column is the wide one


# (layout, section name, {placeholder idx: text}, options)
SLIDES = [
    ("Cover", None,
     {0: "Three routine classifiers on fine-needle aspirate morphometry: accuracy reported to STARD",
      1: "Presenter", 14: "Department\nInstitution, City, Country",
      13: "MedSci Skills · Demo 1 · tooling demonstration"},
     dict(notes="10분입니다. 진단정확도 연구 한 편을 처음부터 끝까지 돌린 예시입니다. 데이터가 쉬워서 숫자 자체는 "
                "자랑거리가 아니고, 보실 것은 보고 방식입니다. 참조표준, 흐름도, 구간, 그리고 모형 사이의 비교입니다.")),
    ("Disclosure", None, {0: "Disclosures", 1: "None", 13: "None"},
     dict(notes="이해관계와 연구비는 없습니다.")),
    ("Result · Table", "Question",
     {0: "Do three routine classifiers differ on the same aspirates?",
      13: f"{n_feat} such measurements per aspirate. Reference standard: [[histopathology]].",
      14: f"Mean (SD) over all {n_all} aspirates. analysis/tables/table1_features_by_class.csv"},
     dict(table=[["Measurement", f"Malignant (n = {n_mal})", f"Benign (n = {n_all - n_mal})"]]
          + [[r["Feature"].capitalize(), r["Malignant_mean_SD"], r["Benign_mean_SD"]] for r in table1[:3]],
          widths=[4.2, 4.0, 4.03],
          notes="질문은 하나입니다. 같은 측정값을 넣었을 때 흔히 쓰는 세 모형이 서로 다른가. 표는 넣는 값의 예입니다. "
                "핵의 크기와 질감 같은 측정값이 악성과 양성에서 이만큼 다릅니다. 참조표준은 조직 진단입니다.")),
    ("Study Design", "Methods",
     {0: f"One aspirate is the unit; {n_test} were held out before fitting",
      13: f"{n_all} aspirates, {n_mal} malignant; public Wisconsin dataset",
      14: "Stratified 70/30 split, seed recorded",
      15: "Histopathologic diagnosis for every sample"},
     dict(picture=DEMO / "figures" / "stard_flow.png",
          notes="STARD 흐름도입니다. 분석 단위는 흡인 검체 한 건이고, 층화 분할의 시드가 기록돼 있습니다. "
                "오른쪽 세 줄은 대상, 분할, 참조표준입니다. 모든 검체에 조직 진단이 있습니다.")),
    ("Result · Figure", "Results",
     {0: "The three ROC curves cannot be told apart by eye",
      14: f"Held-out set, n = {n_test} ({test_mal} malignant, {test_ben} benign). DeLong 95% CI."},
     dict(picture=DEMO / "analysis" / "figures" / "roc_curve.png", align="ctr",
          notes="세 모형의 ROC 곡선입니다. 모두 왼쪽 위에 붙어 있어서 눈으로는 구별되지 않습니다. "
                "이 데이터에서는 흔한 모습이고, 그래서 다음 장의 구간과 검정이 필요합니다.")),
    ("Key Finding", "Results",
     {0: "Near-perfect discrimination on the held-out set",
      13: f3(lr["AUC"]), 14: "area under the ROC curve, logistic regression",
      15: f"95% CI {f3(lr['AUC_lo'])} to {f3(lr['AUC_hi'])} · n = {n_test}",
      16: "analysis/tables/diagnostic_accuracy.csv"},
     dict(notes="로지스틱 회귀의 AUC와 95% 신뢰구간입니다. 구간의 아래쪽 끝도 매우 높습니다. "
                "다만 이 벤치마크는 정제된 자료여서, 이 숫자를 임상 성능으로 읽으면 안 됩니다.")),
    ("Result · Table", "Results",
     {0: "Same AUC; logistic regression was best calibrated",
      13: f"Pairwise DeLong p from {p_lo:.2f} to {p_hi:.2f}. Brier: [[lowest]] against [[2|highest]].",
      14: "Sensitivity and specificity at threshold 0.5, with 95% CI. Lower Brier score is better."},
     dict(table=[["Model", "AUC (95% CI)", "Sensitivity", "Specificity", "Brier"]]
          + [[m, ci(r, "AUC"), f3(r["Thr0.5_Sens"]), f3(r["Thr0.5_Spec"]), f3(r["Brier"])] for m, r in acc.items()],
          accent={(1 + list(acc).index("Logistic Regression"), 4): 1,      # the best-calibrated model
                  (1 + list(acc).index(worst_brier["Model"]), 4): 2},     # and the one it is set against
          notes="세 모형을 한 표에 놓았습니다. 쌍별 DeLong 검정에서 차이가 없었습니다. 구별되는 것은 마지막 열입니다. "
                "Brier 점수가 가장 낮은 것이 로지스틱 회귀이고, 확률을 그대로 쓰려면 이 열이 중요합니다.")),
    ("Limitations", "Limits",
     {0: "Three reasons this is a demonstration and not a validation",
      13: "A curated benchmark", 16: "Easy cases are over-represented; accuracy in practice would be lower",
      14: "No external set", 17: "One source, one split; nothing here shows the result travels",
      15: f"{lr['FN']} of {test_mal} malignant samples missed", 18: "At threshold 0.5; the threshold was not chosen in advance"},
     dict(notes="한계 세 가지입니다. 정제된 벤치마크이고, 외부 자료가 없고, 임계값 0.5에서 악성 검체를 놓친 것이 있습니다. "
                "임계값을 사후에 고르면 낙관 편향이 생기므로 여기서는 고르지 않았습니다.")),
    ("Take-home", "Summary",
     {0: "What to take from this",
      1: ["Discrimination: [[2|no difference]] between the models",
          "[[Calibration]], not AUC, separated them",
          "Every number here is read from the tables"]},
     dict(notes="정리합니다. 판별력은 세 모형이 같았고, 갈린 것은 보정이었습니다. 그리고 이 슬라이드의 숫자는 모두 "
                "분석 표에서 읽어 온 것이라, 결과가 바뀌면 덱도 같이 바뀝니다. 감사합니다.")),
]


def build(out, band=True):
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
            nd.fit_picture(slot[30], opt["picture"], opt.get("align", "l"))
        if "table" in opt:
            rows = opt["table"]
            tbl = t.plain_table(slot[21], len(rows), len(rows[0]), rows[0])
            for col, width in zip(tbl.columns, opt.get("widths", COL_W)):
                col.width = Inches(width)
            for r, row in enumerate(rows[1:], start=1):
                for c, text in enumerate(row):
                    t.set_cell(tbl, r, c, text, accent=opt.get("accent", {}).get((r, c), False))
        tf = s.notes_slide.notes_text_frame
        tf.text = opt["notes"]
        nd.set_lang(tf)
    nd.drop_empty_bands(prs)
    prs.save(out)
    t.post_process(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plain", metavar="OUT", help="write the same slides without the band to OUT")
    a = ap.parse_args()
    print("wrote", build(a.plain, band=False) if a.plain else build(HERE / "demo1_wisconsin_bc.pptx"))
