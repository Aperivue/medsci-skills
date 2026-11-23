#!/usr/bin/env python3
"""Demo 2 conference talk, 10 minutes, on the medsci slide template.

    python3 build_deck.py                 # -> demo2_bcg_meta_analysis.pptx (mono palette, plain: no section band)
    python3 build_deck.py --band OUT      # the same slides with the section band, written to OUT

Every number on a slide is read from analysis/tables/ at build time; none is typed in.
Slide text is English; speaker notes are Korean prose.

Emphasis in this deck, one meaning each for the whole deck:
    [[words]]    first accent  = the point of the slide
    [[2|words]]  second accent = what that point is set against
"""
from __future__ import annotations

import argparse
import csv
import re
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
FIGURES = DEMO / "analysis" / "figures"
PALETTE = "mono"

m = {r["metric"]: r["value"] for r in csv.DictReader((TABLES / "meta_results.csv").open())}
per_study = list(csv.DictReader((TABLES / "per_study_escalc.csv").open()))
loo = list(csv.DictReader((TABLES / "leave_one_out.csv").open()))

k = int(float(m["k_trials"]))
n_part = f"{int(float(m['total_participants'])):,}"
n_below1 = sum(float(r["RR"]) < 1 for r in per_study)    # trials whose point estimate favours BCG
loo_lo, loo_hi = min(float(r["RR"]) for r in loo), max(float(r["RR"]) for r in loo)
assert len(per_study) == k, "one row per trial"
assert float(m["pred_interval_lb"]) < 1 < float(m["pred_interval_ub"]), "the slides say the prediction interval crosses 1"
assert float(m["pooled_RR_uci"]) < 1, "the slides say the confidence interval excludes 1"
assert all(float(r["RR_uci"]) < 1 for r in loo), "the leave-one-out row says every interval excludes 1"
assert float(m["egger_p"]) > 0.05 and float(m["ranktest_p"]) > 0.05, "the funnel slide says neither test is significant"


def f(key, nd_=3):
    """Decimals as the manuscript prints them: 3 for RR, tau2, p and tau; pass 1 for I2, 2 for Q and z."""
    return f"{float(m[key]):.{nd_}f}"


def f3(value):
    return f"{float(value):.3f}"


COL_W = [5.2, 2.2, 2.2, 2.63]     # inches; the first column carries the long row labels


# (layout, section name, {placeholder idx: text}, options)
SLIDES = [
    ("Cover", None,
     {0: f"BCG vaccination and tuberculosis: a random-effects meta-analysis of {k} trials",
      1: "Presenter", 14: "Department\nInstitution, City, Country",
      13: "MedSci Skills · Demo 2 · tooling demonstration"},
     dict(notes=f"10분입니다. 고전적인 BCG 데이터셋 {k}개 시험의 메타분석입니다. 통합 추정치는 위험을 절반 가까이 낮추지만, "
                f"이 발표에서 정말 볼 것은 이질성입니다. I²가 {f('I2_percent', 0)}% 수준이면 요약치 하나를 그대로 읽는 것이 정직하지 않습니다.")),
    ("Disclosure", None, {0: "Disclosures", 1: "None", 13: "None"},
     dict(notes="이해관계와 연구비는 없습니다.")),
    ("Key Finding", "Results",
     {0: f"BCG roughly halved tuberculosis risk in {k} trials",
      13: f("pooled_RR"), 14: "pooled risk ratio, BCG against control",
      15: f"95% CI {f('pooled_RR_lci')} to {f('pooled_RR_uci')} · {k} trials · {n_part} participants",
      16: "analysis/tables/meta_results.csv"},
     dict(notes=f"통합 위험비는 {f('pooled_RR')}이고 95% 신뢰구간은 {f('pooled_RR_lci')}에서 {f('pooled_RR_uci')}입니다. "
                f"시험 {k}개, 대상자 {n_part}명입니다. 평균적으로는 결핵 위험이 절반 정도로 줄었다는 뜻입니다. "
                f"다만 이 숫자는 평균 효과의 정밀도일 뿐이고, 다음 장부터 그 평균이 얼마나 대표성이 있는지 봅니다.")),
    ("Result · Figure", "Results",
     {0: "Trial estimates scatter widely around the pooled one",
      14: f"{k} trials, {n_part} participants. {n_below1} of {k} trial estimates below 1. "
          f"Random effects (REML), tau² {f('tau2')}."},
     dict(picture=FIGURES / "forest.png", align="ctr",
          notes=f"숲그림입니다. 시험별 추정치가 한쪽에 몰려 있지 않고 넓게 퍼져 있고, 점추정치가 1보다 작은 시험은 {k}개 중 {n_below1}개입니다. "
                f"통합값 하나만 인용하면 그 퍼짐이 사라집니다.")),
    ("Result · Table", "Results",
     {0: f"At I² {f('I2_percent', 1)}%, a new trial could show no benefit",
      13: "[[Prediction interval]] crosses 1; [[2|confidence interval]] does not.",
      14: f"Q = {f('Q', 2)} on {m['Q_df']} df, tau² = {f('tau2')}. Leave-one-out: pooled RR with each trial omitted in turn."},
     dict(table=[["Interval", "Lower", "Upper", "Excludes 1"],
                 ["95% confidence interval, pooled RR", f("pooled_RR_lci"), f("pooled_RR_uci"), "Yes"],
                 ["95% prediction interval, a new trial", f("pred_interval_lb"), f("pred_interval_ub"), "No"],
                 ["Leave-one-out pooled RR, range", f3(loo_lo), f3(loo_hi), "Yes, every interval"]],
          accent={(2, 3): 1,       # the prediction interval: the point
                  (1, 3): 2},      # the confidence interval it is set against
          widths=[5.2, 2.0, 2.0, 3.03],
          notes=f"핵심 슬라이드입니다. 신뢰구간은 평균 효과의 정밀도이고, 예측구간은 새 시험이 어디에 떨어질지를 말합니다. "
                f"신뢰구간은 {f('pooled_RR_lci')}에서 {f('pooled_RR_uci')}로 1을 벗어나지만, 예측구간은 {f('pred_interval_lb')}에서 "
                f"{f('pred_interval_ub')}로 1을 넘어갑니다. 한 시험을 빼도 통합값은 {f3(loo_lo)}에서 {f3(loo_hi)} 사이라 "
                f"특정 시험 하나가 결과를 끌고 가지는 않습니다. 통합 RR만 보고하면 예측구간 사실이 보이지 않습니다.")),
    ("Result · Figure", "Results",
     {0: "Neither small-study test found funnel asymmetry",
      14: f"Egger z = {f('egger_z', 2)}, p = {f('egger_p')}. Rank test tau = {f('ranktest_tau')}, p = {f('ranktest_p')}. "
          f"k = {k}, so power is low."},
     dict(picture=FIGURES / "funnel.png", align="ctr",
          notes=f"깔때기 그림과 두 검정 모두 유의하지 않습니다. 다만 k가 {k}이면 이 검정들은 검정력이 낮습니다. "
                f"'출판편향 없음'이 아니라 '이 표본으로는 판단 못 함'이 정확한 서술입니다.")),
    ("Limitations", "Limits",
     {0: "Three limits on reading the pooled value as the answer",
      13: "Very high heterogeneity", 16: f"I² {f('I2_percent', 1)}%: one summary does not describe a future trial",
      14: f"Only {k} trials", 17: "Egger and rank tests have little power at this size",
      15: "Illustrative search counts", 18: "Trials are metafor's dat.bcg; no risk-of-bias or GRADE rating was done"},
     dict(notes="한계 세 가지입니다. 이질성이 매우 커서 요약치 하나가 새 시험을 설명하지 못합니다. 시험이 적어 비대칭 검정의 검정력이 낮습니다. "
                "그리고 이 분석은 방법 시연이라 PRISMA 상류 단계의 검색 건수는 예시이고, 연구별 비뚤림 평가와 GRADE는 범위 밖입니다. "
                "그 사실을 숨기지 않고 적었습니다.")),
    ("Take-home", "Summary",
     {0: "What to take from this",
      1: [f"Pooled [[2|RR {f('pooled_RR')}]]: risk about halved",
          f"[[Prediction interval]] {f('pred_interval_lb')} to {f('pred_interval_ub')}",
          f"Bias tests: no asymmetry, but k = {k}"]},
     dict(notes=f"정리합니다. 통합 RR {f('pooled_RR')}는 위험이 절반 가까이 줄었다는 평균입니다. 그러나 예측구간이 "
                f"{f('pred_interval_lb')}에서 {f('pred_interval_ub')}라 새 시험에서 효과가 없을 수도 있습니다. "
                f"비대칭 검정은 유의하지 않았지만 시험 수가 적어 결론을 내리지 못합니다.")),
]

for _name, _sec, _content, _opt in SLIDES:      # the length rules of the brief, checked at build time
    plain = lambda s: re.sub(r"\[\[(?:2\|)?(.*?)\]\]", r"\1", s)
    if _name in ("Key Finding", "Result · Figure", "Result · Table", "Limitations"):
        assert len(_content[0]) <= 55, f"title too long: {_content[0]}"
    if _name == "Take-home":
        assert all(len(plain(x)) <= 45 for x in _content[1]), "take-home line too long"


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
    ap.add_argument("--band", metavar="OUT", help="write the same slides with the section band to OUT")
    a = ap.parse_args()
    print("wrote", build(a.band, band=True) if a.band else build(HERE / "demo2_bcg_meta_analysis.pptx"))
