#!/usr/bin/env python3
"""Demo 3 conference talk, 10 minutes, on the medsci slide template.

    python3 build_deck.py                 # -> demo3_nhanes_obesity.pptx (stone palette, section band)
    python3 build_deck.py --plain OUT     # the same slides without the band

Every number on a slide is read from analysis/tables/ at build time; none is typed in.
Slide text is English; speaker notes are Korean prose.

Emphasis, for the whole deck: [[first accent]] = the point of the slide (the estimate or finding);
[[2|second accent]] = what that point is set against (the self-report estimate against HbA1c,
association against cause).
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

T = DEMO / "analysis" / "tables"
F = DEMO / "analysis" / "figures"
PALETTE = "stone"

k = {r["metric"]: r["value"] for r in csv.DictReader((T / "key_scalars.csv").open())}
primary = {r["term"]: r for r in csv.DictReader((T / "regression_or.csv").open())}
OB = "Obesity (BMI>=30 vs <30)"
assert float(primary[OB]["estimate"]) == max(
    float(r["estimate"]) for term, r in primary.items() if term not in ("(Intercept)", "Age (per year)")
), "the forest title says obesity has the largest adjusted odds of the model"
assert abs(float(k["aOR_obesity_hba1c"]) - float(k["aOR_obesity"])) < 0.25, \
    "the sensitivity title says the HbA1c estimate is nearly the same"


def f(key, nd_=2):
    return f"{float(k[key]):.{nd_}f}"


def n(key):
    return f"{int(float(k[key])):,}"


def p_text(value):
    value = float(value)
    return "p < 0.001" if value < 0.001 else f"p = {value:.3f}"


N = n("analytic_N")
CI_W = [4.6, 2.0, 2.2, 3.43]            # inches; the sensitivity table
PREV_W = [5.0, 3.0, 4.23]               # inches; the prevalence table


def ci(prefix):
    return f"{f(prefix + '_ci_lo')} to {f(prefix + '_ci_hi')}"


def ci1(prefix):
    return f"{f(prefix + '_ci_lo', 1)} to {f(prefix + '_ci_hi', 1)}"


# (layout, section name, {placeholder idx: text}, options)
SLIDES = [
    ("Cover", None,
     {0: "Obesity and diabetes in US adults: a survey-weighted association in NHANES 2017–2018",
      1: "Presenter", 14: "Department\nInstitution, City, Country",
      13: "MedSci Skills · Demo 3 · tooling demonstration"},
     dict(notes="10분입니다. 복합표본 설계를 무시하고 그냥 로지스틱을 돌리는 게 이 분야에서 가장 흔한 "
                "실수입니다. 여기서는 가중치·층·PSU를 전부 반영했고, 그래서 구간이 단순 분석보다 넓습니다.")),
    ("Disclosure", None, {0: "Disclosures", 1: "None", 13: "None"},
     dict(notes="이해관계와 연구비는 없습니다.")),
    ("Result · Table", "Question",
     {0: f"Weighted prevalence: obesity {f('weighted_obesity_prev_pct', 1)}%, "
         f"diabetes {f('weighted_diabetes_prev_pct', 1)}%",
      13: "Question: is [[obesity]] linked to diabetes after adjusting for age, sex and race?",
      14: f"US adults aged 20 or older, n = {N}. Weighted to the US population. "
          "analysis/tables/key_scalars.csv"},
     dict(table=[["Measure", "Weighted %", "95% CI"],
                 ["Obesity (BMI 30 or more)", f("weighted_obesity_prev_pct", 1), ci1("weighted_obesity")],
                 ["Diabetes (self-reported)", f("weighted_diabetes_prev_pct", 1), ci1("weighted_diabetes")]],
          widths=PREV_W,
          notes="가중 유병률입니다. NHANES는 특정 집단을 과대표집하므로 가중치 없이 센 비율은 "
                "미국 인구를 추정하지 않습니다. 구간도 설계를 반영해 계산했습니다. 질문은 하나입니다. "
                "나이, 성별, 인종을 보정한 뒤에도 비만이 당뇨와 연관되는가.")),
    ("Study Design", "Methods",
     {0: f"{N} adults remained after a stated exclusion cascade",
      13: f"US adults aged 20 or older; NHANES 2017–2018",
      14: f"Survey-weighted logistic regression, {f('n_strata', 0)} strata",
      15: "Self-reported diabetes; obesity is BMI 30 or more"},
     dict(picture=F / "strobe_flow.png",
          notes="STROBE 흐름도입니다. 제외마다 이유와 숫자가 붙고, 빼기가 정확히 분석 대상 수로 떨어집니다. "
                "이 산술이 안 맞으면 아래 모든 숫자가 의심스러워집니다. 오른쪽은 대상, 설계, 결과 정의입니다.")),
    ("Result · Figure", "Results",
     {0: "Obesity had the largest adjusted odds of the model",
      14: f"Design-based logistic regression, n = {N}; covariates are age, sex and race/ethnicity. "
          f"Obesity {p_text(k['aOR_obesity_p'])}."},
     dict(picture=F / "forest_or.png", align="ctr",
          notes="조정 오즈비 숲그림입니다. 설계 기반 회귀라 표준오차가 단순 무작위표본 가정보다 큽니다. "
                "공변량은 나이, 성별, 인종이고, 무엇을 왜 넣었는지가 이 결과의 신뢰도를 결정합니다.")),
    ("Key Finding", "Results",
     {0: f"Obesity carried {f('aOR_obesity')}-fold adjusted odds of diabetes",
      13: f("aOR_obesity"), 14: "adjusted odds ratio, obesity against no obesity",
      15: f"95% CI {ci('aOR_obesity')} · {p_text(k['aOR_obesity_p'])} · n = {N}",
      16: "analysis/tables/regression_or.csv"},
     dict(notes="핵심 숫자입니다. 조정 오즈비와 95% 신뢰구간입니다. 구간의 아래쪽 끝도 2를 넘으므로 "
                "연관이 우연이라고 보기는 어렵습니다. 다만 단면연구라 방향은 말할 수 없습니다.")),
    ("Result · Table", "Results",
     {0: "The HbA1c definition gave nearly the same odds ratio",
      13: f"Obesity: [[{f('aOR_obesity_hba1c')}]] by HbA1c against [[2|{f('aOR_obesity')}]] by self-report.",
      14: "Adjusted for age, sex and race/ethnicity. analysis/tables/regression_or_hba1c_sensitivity.csv"},
     dict(table=[["Outcome", "n", "Adjusted OR", "95% CI"],
                 ["Self-reported diabetes", N, f("aOR_obesity"), ci("aOR_obesity")],
                 ["HbA1c 6.5% or more", n("sens_n_hba1c"), f("aOR_obesity_hba1c"), ci("aOR_obesity_hba1c")]],
          widths=CI_W,
          notes="민감도 분석입니다. 결과를 자가보고 대신 HbA1c 6.5% 이상으로 정의해도 오즈비가 거의 같습니다. "
                "자가보고는 진단받지 않은 당뇨를 놓칠 수 있어서, 이 일치가 결과를 뒷받침합니다. "
                "두 정의가 같은 사람들을 가리키는 것은 아닙니다.")),
    ("Limitations", "Limits",
     {0: "Three reasons to read this as association only",
      13: "Cross-sectional", 16: "Exposure and outcome were measured together, so there is no order in time",
      14: "Self-reported diabetes", 17: "Undiagnosed cases are missed; the HbA1c outcome gave a similar estimate",
      15: "One BMI cutoff", 18: "Residual confounding by diet, activity and income is likely"},
     dict(notes="한계 세 가지입니다. 단면연구라 연관성까지만 말할 수 있고, 그건 취향이 아니라 설계의 한계입니다. "
                "자가보고 결과는 HbA1c로 확인했지만 완전히 해소되지는 않습니다. 비만은 BMI 하나로 정의했고, "
                "식이·활동·사회경제적 요인은 보정하지 못했습니다.")),
    ("Take-home", "Summary",
     {0: "What to take from this",
      1: [f"[[{f('aOR_obesity')}-fold]] adjusted odds of diabetes",
          "Same answer with an HbA1c outcome",
          "An association, [[2|not a cause]]"]},
     dict(notes="정리합니다. 비만과 당뇨의 조정 오즈비는 약 3배였고, HbA1c로 정의해도 같은 결과였습니다. "
                "다만 단면연구라 원인이라고는 말하지 않습니다. 이 슬라이드의 숫자는 모두 분석 표에서 읽어 온 것입니다.")),
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
    ap.add_argument("--plain", metavar="OUT", help="write the same slides without the band to OUT")
    a = ap.parse_args()
    print("wrote", build(a.plain, band=False) if a.plain else build(HERE / "demo3_nhanes_obesity.pptx"))
