#!/usr/bin/env python3
"""Demo 6 resident lecture, 30 minutes, on the medsci slide template: The Circle of Willis.

    python3 build_deck.py                 # -> demo6_circle_of_willis.pptx (pine palette, section band)

Structure: opening case, roadmap table, three parts with a section slide each, two quizzes, summary table,
take-home, references. Slide text is English; speaker notes are Korean prose. Every figure is cropped from a
CC BY article (assets/SOURCES.md); the numbers are in the dicts below, each with the article and section it
is quoted from.

Emphasis in this deck: [[...]] (first accent) is the number or phrase to read on the slide; [[2|...]] (second
accent) is what that is set against.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parents[2] / "skills" / "present-paper" / "templates" / "slide_template"
sys.path.insert(0, str(TEMPLATE))

import build_slide_template as t      # noqa: E402
import new_deck as nd                 # noqa: E402

FIG = HERE / "figures"
OUT = HERE / "demo6_circle_of_willis.pptx"
PALETTE = "pine"

# Numbers, each with the article and section it is quoted from.
K = {  # Kizilgoz 2022, Sci Rep: 867 adults without cerebrovascular disease, 1.5-T TOF MRA
    "n": 867,                                            # Results, Table 1
    "complete_n": 358, "complete_pct": 41.29,            # Results, Table 1 (entirely complete)
    "partial_pct": 48.09, "incomplete_pct": 10.62,       # Results, Table 1
    "ant_A": 75.78, "ant_G": 16.49, "ant_H": 2.88,       # Results, Table 2 (anterior types A, G, H)
    "post_A": 53.98, "post_D": 16.15, "post_E": 27.57,   # Results, Table 2 (posterior types A, D, E)
    "hypoplasia_mm": 0.8,                                # Methods: a segment under 0.8 mm was called hypoplastic
}
R = {  # Rangus 2022, Int J Stroke: 991 patients with ischaemic stroke or TIA, 3-T TOF MRA
    "n": 991,                                            # Methods/Results, study population
    "fpca_pct": 33.3, "fpca_uni": 25.6, "fpca_bi": 7.7,  # Results, posterior circulation
    "a1_pct": 6.7,                                       # Results, anterior circulation (A1 agenesis or hypoplasia)
    "multi_n": 238, "reclass_n": 20, "reclass_pct": 8.4,  # Results, stroke pattern reclassification
}
W = {"ppta_lo": 0.061, "ppta_hi": 0.6}                    # Wang 2022, Front Neurol (review), Introduction
C = {"acoa_ruptured_lo": 23, "acoa_ruptured_hi": 40}      # Chen 2020, Front Neurol (review), Abstract
Z = {"a1_hypo_pct": 27, "a1_aplasia_pct": 9, "n": 1739}   # Zampakis 2015, Insights Imaging, Results (CTA series)
assert abs(100 * K["complete_n"] / K["n"] - K["complete_pct"]) < 0.01
assert abs(K["complete_pct"] + K["partial_pct"] + K["incomplete_pct"] - 100) < 0.01
assert abs(100 * R["reclass_n"] / R["multi_n"] - R["reclass_pct"]) < 0.05
assert abs(R["fpca_uni"] + R["fpca_bi"] - R["fpca_pct"]) < 0.01

SRC = {  # short credits shown on the slides; full citations on the last slide and in assets/SOURCES.md
    "greggio": "Greggio et al., BMC Med Imaging 2025, Fig 2A (CC BY 4.0), cropped",
    "chen": "Chen et al., Front Neurol 2020, Fig 1A (CC BY 4.0), cropped",
    "kiz3": "Kizilgoz et al., Sci Rep 2022, Fig 3 (CC BY 4.0), classification after Chen et al. 2004",
    "kiz4": "Kizilgoz et al., Sci Rep 2022, Fig 4 (CC BY 4.0), classification after Chen et al. 2004",
    "kiz4b": "Schematic: Kizilgoz et al., Sci Rep 2022, Fig 4 (CC BY 4.0), cropped, classification after Chen et al. 2004. "
             "Numbers: Rangus et al., Int J Stroke 2022",
    "kiz5": "Kizilgoz et al., Sci Rep 2022, Fig 5 (CC BY 4.0), cropped",
    "rangus1": "Rangus et al., Int J Stroke 2022, Fig 1 (CC BY 4.0), cropped",
    "rangus2": "Rangus et al., Int J Stroke 2022, Fig 2 (CC BY 4.0), cropped",
    "wang": "Wang and Yu, Front Neurol 2022, Fig 1A (CC BY 4.0), cropped",
    "liu": "Liu et al., Neurol Sci 2021, Fig 1 (CC BY 4.0)",
    "zam": "Image and A1 finding: Zampakis et al., Insights Imaging 2015, Fig 6 (CC BY 4.0). 23% to 40%: Chen et al., Front Neurol 2020",
}
REFS = [  # short form; full citations are in assets/SOURCES.md
    "Kizilgoz V, et al. Sci Rep 2022;12:17611",
    "Rangus I, et al. Int J Stroke 2022;17:770-776",
    "Greggio J, et al. BMC Med Imaging 2025;25:33",
    "Chen J, et al. Front Neurol 2020;11:1020",
    "Wang Y, Yu J. Front Neurol 2022;13:928608",
    "Zampakis P, et al. Insights Imaging 2015;6:33-42",
    "Liu Y, et al. Neurol Sci 2021;42:5335-5342",
]

P1, P2, P3 = "The normal ring", "Variants", "Why it matters"

# (layout, section name, {placeholder idx: text}, options)
# options: notes, pics={idx: file} (crop to fill the slot), fit={idx: file} (whole picture), source (credit line),
# table (rows), answer (idx of the Quiz answer that appears on click)
SLIDES = [
    ("Cover", None,
     {0: "The Circle of Willis", 1: "Presenter", 13: "Example lecture · anatomy and variants",
      14: "Department\nInstitution, City, Country"},
     dict(notes="안녕하십니까. 오늘은 circle of Willis를 정상 구조, 변이, 그리고 변이가 임상에서 바꾸는 것 순서로 보겠습니다.")),

    ("Imaging · DSA Pair", None,
     {0: "Infarcts in three territories at once: three embolic sources, or one?", 20: "Opening case",
      40: "DWI: left PCA and ACA territories", 41: "DWI: left MCA territory"},
     dict(pics={30: "rangus1_a.png", 31: "rangus1_b.png"}, source=SRC["rangus1"],
          notes="증례부터 보겠습니다. 급성 뇌경색 환자의 DWI입니다.\n\n"
                "왼쪽 영상에서는 왼쪽 PCA와 ACA 영역에, 오른쪽 영상에서는 왼쪽 MCA 영역에 병변이 있습니다. 세 혈관 영역에 동시에 생긴 경색입니다.\n\n"
                "이렇게 여러 영역에 걸친 경색을 보면 보통 심장이나 대동맥 같은 근위부 색전원을 먼저 떠올립니다. 이 환자의 답은 강의 뒷부분에서 다시 보겠습니다.")),

    ("Table", "Roadmap",
     {0: "Three parts: the ring, its variants, what the variants change"},
     dict(table=[["Part", "What to know", "Why it matters"],
                 [P1, "A1, AComA, PComA and P1 around the two carotid ends and the basilar tip",
                  "The route between the three inflows"],
                 [P2, "Small or absent segments; fetal-type PCA", f"A ring with no variant: {K['complete_pct']:.0f}%"],
                 [P3, "Infarct territory, collateral flow, aneurysm sites", "Stroke pattern and treatment planning"]],
          widths=[2.6, 5.4, 4.2],
          notes="오늘 내용은 세 부분입니다. 먼저 정상 고리를 이루는 분절을 보고, 다음으로 어떤 변이가 얼마나 흔한지 보고, "
                "마지막으로 그 변이가 경색 판독과 동맥류에서 무엇을 바꾸는지 보겠습니다.")),

    ("Section", None, {13: "01", 0: P1, 14: "AComA, A1, PComA and P1"},
     dict(notes="첫 부분, 정상 구조입니다.")),

    ("Imaging · Full Center", None,
     {0: "Seven segments close the ring", 40: "AComA, two A1, two PComA, two P1",
      41: "The MCA is not part of the ring"},
     dict(pics={30: "greggio_vr.png"}, source=SRC["greggio"],
          notes="TOF MRA를 volume rendering으로 위에서 내려다본 영상입니다.\n\n"
                "앞쪽에서는 양쪽 A1이 anterior communicating artery로 이어집니다. 뒤쪽에서는 basilar artery 끝에서 나온 양쪽 P1이 "
                "posterior communicating artery를 통해 ICA와 이어집니다.\n\n"
                "고리를 이루는 분절은 AComA 하나, A1 둘, PComA 둘, P1 둘, 모두 일곱 개입니다. MCA는 ICA에서 바로 이어지는 가지라서 고리에 들어가지 않습니다.")),

    ("Lessons", P1,
     {0: "The same ring seen directly",
      1: ["1 AComA · 2 A2 · 3 A1", "4 MCA · 5 ICA · 6 basilar artery", "Here the right A1 is the smaller one"]},
     dict(pics={30: "chen_specimen_a.png"}, source=SRC["chen"],
          notes="같은 구조를 실제 혈관 사진으로 보겠습니다. 번호는 1번이 AComA, 2번이 A2, 3번이 A1, 4번이 MCA, 5번이 ICA, 6번이 basilar artery입니다.\n\n"
                "이 사진에서는 오른쪽 A1이 왼쪽보다 가늡니다. 정상 구조를 보여 드리려고 고른 사진에도 이미 변이가 들어 있습니다. 다음 부분의 주제입니다.")),

    ("Section", None, {13: "02", 0: P2, 14: "How often, and which segments"},
     dict(notes="둘째 부분, 변이입니다.")),

    ("Key Finding", P2,
     {0: "On MRA, a ring with no variant was the minority",
      13: f"{K['complete_pct']:.0f}%", 14: "had every segment present and normal in size",
      15: f"{K['complete_n']} of {K['n']} adults without cerebrovascular disease · 1.5-T TOF MRA · "
          f"Kizilgoz et al. 2022; a segment under {K['hypoplasia_mm']} mm counted as hypoplastic"},
     dict(notes=f"튀르키예의 한 병원에서 뇌혈관 질환 병력이 없는 성인 {K['n']}명의 TOF MRA를 본 연구입니다.\n\n"
                f"모든 분절이 있고 굵기도 정상인 고리는 {K['complete_pct']:.0f}퍼센트였습니다. 나머지는 앞쪽이나 뒤쪽, 또는 양쪽 모두에 변이가 있었습니다.\n\n"
                f"이 연구는 지름 {K['hypoplasia_mm']}밀리미터 미만을 hypoplasia로 봤습니다. 기준과 검사 방법에 따라 숫자는 연구마다 달라집니다. "
                "기억하실 것은 교과서 그림 같은 고리가 절반에 못 미친다는 점입니다.")),

    ("Result · Figure", P2,
     {0: f"Anterior part: a small or absent AComA was the most common variant ({K['ant_G']:.0f}%)"},
     dict(fit={30: "kiz_anterior.png"},
          source=f"Type A normal {K['ant_A']:.1f}% · G small or absent AComA {K['ant_G']:.1f}% · "
                 f"H small or absent A1 {K['ant_H']:.1f}%. " + SRC["kiz3"],
          notes="앞쪽 변이를 열 가지 유형으로 그린 도식입니다. A가 정상이고 넷 중 셋이 여기에 들어갑니다.\n\n"
                "그다음으로 흔한 것이 아랫줄 G, AComA가 가늘거나 없는 경우입니다. H는 한쪽 A1이 가늘거나 없고 반대쪽 ACA가 양쪽 A2를 모두 내는 형태입니다.\n\n"
                "나머지 유형은 각각 2퍼센트 이하로 드뭅니다.")),

    ("Result · Figure", P2,
     {0: "Posterior part: nearly half had a variant, most often an absent PComA"},
     dict(fit={30: "kiz_posterior.png"},
          source=f"Type A normal {K['post_A']:.1f}% · E both PComAs absent {K['post_E']:.1f}% · "
                 f"D one PComA absent {K['post_D']:.1f}%. " + SRC["kiz4"],
          notes="뒤쪽은 변이가 더 흔합니다. 정상인 A형이 절반을 조금 넘습니다.\n\n"
                "가장 흔한 변이는 E, 양쪽 PComA가 모두 안 보이는 경우이고, 다음이 D, 한쪽만 안 보이는 경우입니다. 이때 앞 순환과 뒤 순환은 고리로 이어지지 않습니다.\n\n"
                "윗줄 B와 C는 fetal-type PCA입니다. 이 연구에서는 드물었지만 임상적으로 중요해서 따로 보겠습니다.")),

    ("Imaging · DSA Pair", None,
     {0: "The two absences to look for on MRA", 20: P2, 40: "Absent left A1", 41: "Both PComAs absent"},
     dict(pics={30: "kiz_mra_absent_a1.png", 31: "kiz_mra_absent_pcoms.png"}, source=SRC["kiz5"],
          notes="실제 MRA입니다. 왼쪽 영상에서는 왼쪽 A1이 보이지 않고, 오른쪽 ICA에서 올라온 ACA가 양쪽 A2를 모두 채웁니다.\n\n"
                "오른쪽 영상에서는 양쪽 PComA가 모두 보이지 않습니다. 앞에서 본 도식의 H형과 E형입니다.\n\n"
                "MRA를 볼 때 A1과 PComA가 양쪽에 다 있는지를 정해 놓고 확인하시면 됩니다.")),

    ("Lessons", P2,
     {0: "Fetal-type PCA: the PComA is larger than P1",
      1: ["The PCA fills from the ICA",
          f"Seen in [[{R['fpca_pct']:.0f}%]] of {R['n']} stroke patients",
          f"One side {R['fpca_uni']}%, both sides {R['fpca_bi']}%"]},
     dict(pics={30: "kiz_fetal_b.png"}, source=SRC["kiz4b"],
          notes="Fetal-type PCA는 PComA가 P1보다 굵은 경우입니다. 이때 PCA는 basilar artery가 아니라 ICA에서 혈류를 받습니다.\n\n"
                f"베를린의 뇌졸중 코호트 {R['n']}명에서는 셋 중 한 명꼴로 보였고, 한쪽만 있는 경우가 양쪽보다 많았습니다.\n\n"
                "흔한 변이이고, PCA 영역 경색의 원인 혈관이 달라진다는 점에서 중요합니다.")),

    ("Imaging · Case", None,
     {0: "Persistent trigeminal artery: a carotid-basilar link outside the ring", 20: P2,
      1: ["From the cavernous ICA to the basilar artery, between AICA and SCA",
          f"Reported in {W['ppta_lo']}% to {W['ppta_hi']}%",
          "The proximal basilar and vertebral arteries may be small"]},
     dict(pics={30: "wang_ppta_a.png"}, source=SRC["wang"],
          notes="고리 밖에서 앞뒤 순환을 잇는 혈관도 있습니다. 가장 흔한 것이 persistent trigeminal artery입니다.\n\n"
                "별표가 그 혈관입니다. Cavernous ICA에서 나와 AICA와 SCA 사이에서 basilar artery로 들어갑니다.\n\n"
                "드문 변이지만, 이 혈관이 있으면 근위부 basilar artery와 vertebral artery가 가늘 수 있습니다. 협착으로 잘못 읽지 않도록 주의하시면 됩니다.")),

    ("Imaging · Quiz", None,
     {0: "Quiz 1", 1: ["TOF MRA, seen from above", "Which segment of the ring is missing?"],
      50: "The right PComA. The left PComA and both A1s are present"},
     dict(pics={30: "kiz_mra_absent_rpcom.png"}, source=SRC["kiz5"], answer=50,
          notes="퀴즈입니다. TOF MRA를 위에서 본 영상입니다. 고리에서 빠진 분절을 찾아보시기 바랍니다.\n\n"
                "(클릭) 오른쪽 PComA가 보이지 않습니다. 왼쪽 PComA와 양쪽 A1은 보입니다.")),

    ("Section", None, {13: "03", 0: P3, 14: "Territory, collateral flow, aneurysm"},
     dict(notes="셋째 부분, 변이가 임상에서 바꾸는 것입니다.")),

    ("Imaging · 1×3", None,
     {0: "One territory after all: a left fetal PCA puts all three under the left ICA", 20: P3,
      40: "DWI: PCA and ACA", 41: "DWI: MCA", 42: "MRA: left fetal PCA (arrow)",
      1: f"{R['reclass_n']} of {R['multi_n']} multi-territory patterns ({R['reclass_pct']}%) became one territory "
         "once the variant was read"},
     dict(pics={30: "rangus1_a.png", 31: "rangus1_b.png", 32: "rangus1_c.png"}, source=SRC["rangus1"],
          notes="처음 증례로 돌아가겠습니다. 세 번째 영상이 이 환자의 MRA입니다. 화살표가 왼쪽 fetal-type PCA입니다.\n\n"
                "왼쪽 PCA가 ICA에서 나오기 때문에 PCA, ACA, MCA 영역의 병변이 모두 왼쪽 ICA 하나의 공급 영역에 들어갑니다. 색전원을 세 곳이 아니라 왼쪽 경동맥 쪽에서 찾아야 합니다.\n\n"
                f"이 코호트에서 여러 영역 경색으로 분류했던 {R['multi_n']}명 가운데 {R['reclass_n']}명이 변이를 반영하자 한 영역 경색으로 바뀌었습니다. 모두 fetal-type PCA가 있었습니다.")),

    ("Imaging · Case", None,
     {0: "With both carotids narrowed, the AComA is the route between the two sides", 20: P3,
      1: ["Severe left ICA stenosis (1)", "AComA present (2)", "Right ICA nearly occluded (3)"]},
     dict(fit={30: "liu_fig1.png"}, source=SRC["liu"],
          notes="측부순환입니다. 양쪽 경동맥에 병변이 있는 환자입니다. 1번 화살표가 왼쪽 ICA의 심한 협착, 3번이 거의 막힌 오른쪽 ICA입니다.\n\n"
                "2번 화살표가 AComA입니다. 한쪽 ICA의 혈류가 반대쪽 반구로 넘어가는 길이 이 혈관입니다. AComA나 A1이 없으면 이 길이 없습니다.\n\n"
                "경동맥 병변이 있는 환자의 영상을 볼 때 고리의 어느 분절이 남아 있는지를 같이 적어 주시면 됩니다.")),

    ("Lessons", P3,
     {0: "Unequal A1s: look at the AComA for an aneurysm",
      1: [f"AComA: {C['acoa_ruptured_lo']}% to {C['acoa_ruptured_hi']}% of ruptured intracranial aneurysms",
          "Most AComA aneurysm patients had a small A1 (one CTA series)",
          "With one A1 absent, both A2s depend on the other side"]},
     dict(pics={30: "zampakis_fig6.png"}, source=SRC["zam"],
          notes="마지막은 동맥류입니다. AComA는 파열 동맥류가 가장 흔한 자리로 알려져 있습니다.\n\n"
                "한 CTA 연구에서는 AComA 동맥류 환자의 대부분에서 한쪽 A1이 가늘었습니다. 다만 그것이 동맥류의 원인인지는 밝혀지지 않았다고 저자들이 적었습니다. 이 CTA에서도 흰 화살표가 가는 오른쪽 A1이고, 환자에게 AComA 동맥류가 있었습니다.\n\n"
                "치료 계획에서도 중요합니다. 한쪽 A1이 없으면 양쪽 A2가 반대쪽 A1 하나에 의존합니다.")),

    ("Table", None,
     {0: "Summary by part"},
     dict(table=[["Part", "Remember"],
                 [P1, "Seven segments: AComA, two A1, two PComA, two P1"],
                 [P2, f"No variant in {K['complete_pct']:.0f}%; AComA and PComA are most often small or absent; "
                      f"fetal PCA in a third of stroke patients"],
                 [P3, "Read the vessels before naming the infarct territory; unequal A1s point to the AComA"]],
          widths=[2.6, 9.6],
          notes="정리하겠습니다. 표의 세 줄이 오늘 세 부분입니다.")),

    ("Imaging · Quiz", None,
     {0: "Quiz 2", 1: ["DWI showed infarcts in the left thalamus, the pons and the cerebellum", "One territory, or two?"],
      50: "Two. Both PCAs are fetal-type (arrows), so the thalamus is supplied from the ICA"},
     dict(pics={30: "rangus2_c.png"}, source=SRC["rangus2"], answer=50,
          notes="두 번째 퀴즈입니다. DWI에서 왼쪽 thalamus, pons, cerebellum에 경색이 있던 환자의 MRA입니다. 한 영역 경색일까요, 두 영역일까요.\n\n"
                "(클릭) 두 영역입니다. 화살표처럼 양쪽 PCA가 모두 fetal-type이라서 thalamus는 ICA에서, pons와 cerebellum은 vertebrobasilar system에서 공급받습니다.")),

    ("Take-home", "Summary",
     {0: "Three things to remember",
      1: [f"A textbook ring is the exception: [[{K['complete_pct']:.0f}%]] on MRA",
          "Name the missing segment: AComA, A1, PComA or P1",
          "Read the vessels before naming the [[2|infarct territory]]"]},
     dict(notes="세 가지만 기억하시면 됩니다. 교과서 그림 같은 고리는 절반이 안 됩니다. MRA나 CTA를 볼 때는 빠진 분절의 이름을 적습니다. "
                "그리고 경색의 혈관 영역은 혈관 영상을 본 다음에 정합니다. 감사합니다.")),

    ("Content", "References",
     {0: "Figures: seven open-access articles, all CC BY 4.0", 1: REFS},
     dict(notes="그림은 모두 CC BY로 공개된 논문에서 가져왔고, 장마다 출처를 적었습니다.")),
]


def build(out):
    out = Path(out)
    nd.make_deck(out, palette=PALETTE, band=True, force=True)
    prs = Presentation(out)
    lay = {l.name: l for l in prs.slide_layouts}
    for name, section, content, opt in SLIDES:
        s = prs.slides.add_slide(lay[name])
        slot = {p.placeholder_format.idx: p for p in s.placeholders}
        for idx, value in content.items():
            nd.put_rich(slot[idx], value)
        if section and 20 in slot:
            nd.fill(slot[20], section)
        for idx, f in opt.get("pics", {}).items():
            slot[idx].insert_picture(str(FIG / f))              # square slot, crops to fill: for CT/MR/DSA frames
        dark = name.startswith("Imaging")
        for idx, f in opt.get("fit", {}).items():
            nd.fit_picture(slot[idx], FIG / f, align="ctr" if dark else "l")   # whole figure, not cropped
        if "table" in opt:
            rows = opt["table"]
            tbl = t.plain_table(slot[21], len(rows), len(rows[0]), rows[0], size=20, row_h=1.05)
            tbl.rows[0].height = Inches(0.5)             # the header is one line; the body rows hold two
            for r in range(1, len(rows)):
                for c in range(len(rows[0])):
                    t.set_cell(tbl, r, c, rows[r][c], size=20, bold=(c == 0))
            for col, width in zip(tbl.columns, opt["widths"]):
                col.width = Inches(width)
        if "source" in opt:
            nd.credit(s, opt["source"])
        if "answer" in opt:
            nd.appear_on_click(s, [slot[opt["answer"]]])
        tf = s.notes_slide.notes_text_frame
        tf.text = opt["notes"]
        nd.set_lang(tf)
    nd.drop_empty_bands(prs)
    prs.save(out)
    t.post_process(out)
    return out


if __name__ == "__main__":
    print("wrote", build(OUT))
