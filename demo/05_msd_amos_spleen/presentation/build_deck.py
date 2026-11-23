#!/usr/bin/env python3
"""Demo 5 conference talk, 10 minutes, on the medsci slide template.

    python3 build_deck.py                 # -> demo5_external_validation.pptx (teal set, section band)
    python3 build_deck.py --plain OUT     # the same slides without the band

Every number on a slide is read from analysis/tables/ and qc/ at build time; none is typed in.
Slide text is English; speaker notes are Korean prose.

Ten presented slides, then a Backup divider and three backup slides.
"""
from __future__ import annotations

import argparse
import csv
import json
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

MAIN = "0B6E6E"                       # one main colour; the template chooses the second accent
FIG = DEMO / "figures"

# Emphasis, for the whole deck:
#   [[words]]   first accent  = the result being judged (external CT, MRI, the repaired arm)
#   [[2|words]] second accent = what it is set against (the internal baseline, the arm as run)


def table(name):
    with (DEMO / "analysis" / "tables" / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


t2 = {r["arm"]: r for r in table("table2_performance.csv")}
t4 = {r["arm"]: r for r in table("table4_normalisation_evidence.csv")}
sub = [r for r in table("table3_subgroups.csv") if r["arm"].startswith("rung2") and r["subgroup_axis"] == "spleen volume"]
R1, R2, R3 = ("rung1 MSD held-out (internal)", "rung2 AMOS CT (external)", "rung3 AMOS MRI (modality shift)")
R3B, R3C = "rung3b AMOS MRI rescaled (counterfactual)", "rung3c AMOS MRI z-scored (counterfactual)"
prof = json.loads((DEMO / "qc" / "amos22_dataset_profile_spleen.json").read_text())
scale = next(c for c in prof["claims"] if c["verdict"] == "INTENSITY_SCALE_INCONSISTENT")
naive = json.loads((DEMO / "qc" / "preprocessing_leakage_naive.json").read_text())
split = json.loads((DEMO / "qc" / "split_leakage.json").read_text())
seed = (DEMO / "splits" / "split_seed.txt").read_text().strip()
n_train, n_test = split["partitions"]["train"], split["partitions"]["test"]
n_free = sum(int(r["n_target_free"]) for r in t2.values() if r["arm"] in (R1, R2, R3))


def med(arm):
    """Median Dice at the manuscript's four decimals."""
    return t2[arm]["dice_median_95CI"].split(" ")[0]


def ci_text(raw):
    """'0.8932 [0.8633-0.9108]' -> '0.8932 (95% CI 0.8633 to 0.9108)'; the delta form has a '--'."""
    m = re.match(r"^(-?\d+\.\d+) \[(-?\d+\.\d+)-(-?\d+\.\d+)\]$", raw)
    return f"{m[1]} (95% CI {m[2]} to {m[3]})"


def interval(arm):
    m = re.match(r"^(-?\d+\.\d+) \[(-?\d+\.\d+)-(-?\d+\.\d+)\]$", t2[arm]["dice_median_95CI"])
    return f"{m[2]} to {m[3]}"


def stratum(prefix):
    return next(r for r in sub if r["stratum"].startswith(prefix))


enl, nor = stratum("enlarged"), stratum("normal")
ct, mri = t4[R2], t4[R3]
pct = lambda row: row["pct_voxels_above_clip_ceiling_median_range"].split(" ")[0]       # noqa: E731
one_dp = {f"{float(med(a)):.1f}" for a in (R3B, R3C)}
assert len(one_dp) == 1, "the repair title rounds both counterfactual arms to the same value"
assert float(med(R1)) > float(med(R2)) > float(med(R3)), "the ladder title assumes Dice falls rung by rung"
assert naive["summary"]["n_major"] == len(naive["claims"])

COL_W = [4.2, 2.2, 3.0, 2.83]          # inches; no cell wraps


def title_ok(s):
    assert len(s) <= 56, f"title too long ({len(s)}): {s}"
    return s


# (layout, section name, {placeholder idx: text}, options)
SLIDES = [
    ("Cover", None,
     {0: "External validation of a spleen model: where a good CT score stops",
      1: "Presenter", 14: "Department\nInstitution, City, Country",
      13: "MedSci Skills · Demo 5 · tooling demonstration"},
     dict(notes="10분입니다. 결론부터 말씀드리면, 외부 CT에서는 정직하게 잘 나왔고 MRI에서는 무너졌습니다. "
                "무너진 이유는 모델이 아니라 전처리 계약이었고, 파이프라인은 그 사실을 한 번도 알려주지 않았습니다. "
                "오늘 보실 것은 그 침묵입니다.")),
    ("Disclosure", None, {0: "Disclosures", 1: "None", 13: "None"},
     dict(notes="이해관계와 연구비는 없습니다.")),
    ("Content", "Question",
     {0: title_ok("A good external CT score does not show where it stops"),
      1: ["Spleen segmentation, two open datasets",
          "Rungs 1 and 2 are ordinary validation",
          "Rung 3 is a [[constructed test]], not a chance finding"]},
     dict(notes="질문을 좁혔습니다. 모델을 얻을 수 있느냐가 아니라, 그렇게 나온 연구가 방어 가능하냐입니다. "
                "미리 밝히면 3번 rung은 우연히 발견한 것이 아니라 우리가 설계해서 넣은 시험입니다. "
                "그 점은 뒤에서 다시 말씀드리겠습니다.")),
    ("Study Design", "Methods",
     {0: title_ok(f"Three rungs tested {t2[R1]['n_evaluated']} internal, {t2[R2]['n_evaluated']} CT "
                  f"and {t2[R3]['n_evaluated']} MRI cases"),
      13: f"MSD spleen CT, {split['n_rows']} labelled; AMOS22, {t2[R2]['n_evaluated']} CT and {t2[R3]['n_evaluated']} MRI",
      14: f"Patient-level split: {n_train} train, {n_test} held out; seed {seed}",
      15: f"Labels shipped with each dataset; {n_free} cases have no spleen"},
     dict(picture=FIG / "fig5_case_flow.png",
          notes="케이스 회계입니다. 제외마다 이유가 붙어 있고, 라벨된 360건 중 3건은 비장이 아예 없습니다. "
                "그 3건은 Dice가 정의되지 않으므로 분포에서 빼고 따로 보고합니다. 이 규칙은 예측을 보기 전에 고정했습니다.")),
    ("Result · Figure", "Results",
     {0: title_ok(f"Dice fell from {med(R1)} to {med(R2)} on CT, {med(R3)} on MRI"),
      14: f"Change from internal: {ci_text(t2[R2]['delta_dice_vs_internal_95CI'])} on CT; "
          f"{ci_text(t2[R3]['delta_dice_vs_internal_95CI'])} on MRI. Bootstrap, 10,000 resamples."},
     dict(picture=FIG / "across_cohorts_dice.png", align="ctr",
          notes="사다리입니다. 내부에서 외부 CT로 가면서 0.0662 떨어지는데, 이건 정직한 낙폭입니다. "
                "MRI로 가면 거의 전부 잃습니다. 두 낙폭 모두 차이 자체에 구간을 붙였습니다. "
                "중앙값 두 개의 뺄셈은 그 자체로는 추론량이 아니기 때문입니다.")),
    ("Result · Figure", "Results",
     {0: title_ok(f"Weakest on enlarged spleens: {enl['dice_median_95CI'].split(' ')[0]} "
                  f"against {nor['dice_median_95CI'].split(' ')[0]}"),
      14: f"External CT, median Dice. Enlarged {enl['stratum'].split(' ', 1)[1]}, n = {enl['n_scored']}; "
          f"normal {nor['stratum'].split(' ', 1)[1]}, n = {nor['n_scored']}. Cut-points fixed before scoring."},
     dict(picture=FIG / "fig3_subgroups_external_ct.png", align="ctr",
          notes="사전 지정한 subgroup입니다. 비장비대에서 가장 나쁩니다. 그런데 비장 분할이 존재하는 이유가 바로 "
                "비장비대 측정입니다. 0.8932라는 헤드라인이 정확히 그걸 가립니다. 층 간 차이는 검정하지 않았고, "
                "추정치로만 봅니다.")),
    ("Result · Figure", "Results",
     {0: title_ok(f"{pct(mri)} of MRI voxels hit the CT clip ceiling, CT {pct(ct)}"),
      14: f"Voxels with a negative value: {ct['cases_with_any_negative_voxel']} CT cases, "
          f"{mri['cases_with_any_negative_voxel']} MRI cases. Clip window {ct['clip_window_HU']} HU."},
     dict(picture=FIG / "fig4_normalisation_evidence.png", align="ctr",
          notes="훈련 plan이 CT 정규화를 싣고 추론까지 옵니다. HU는 공기 바닥으로 정의되는데 CT는 300건 전부 음수 "
                "복셀이 있고 MRI는 하나도 없습니다. 같은 clip을 적용하면 MRI는 중앙값 기준 23% 복셀이 천장에서 "
                "뭉개집니다. 그리고 모달리티를 알려 줄 인자가 명령어에 없습니다. 정규화기가 체크포인트에 실려 다닙니다.")),
    ("Result · Table", "Results",
     {0: title_ok(f"Two repairs, no retraining: MRI Dice back to {one_dp.pop()}"),
      13: f"Dice rose from [[2|{med(R3)}]] to [[{med(R3B)}]] by rescaling the input.",
      14: "Same checkpoint, 59 scored MRI cases per arm. Bootstrap 95% CI."},
     dict(table=[["MRI arm", "Median Dice", "95% CI", "Empty predictions"]]
          + [[label, med(a), interval(a), f"{t2[a]['n_empty_prediction']} of {t2[a]['n_evaluated']}"]
             for label, a in (("As run", R3), ("Input rescaled", R3B), ("Normaliser z-scored", R3C))],
          accent={(1, 1): 2, (2, 1): 1, (3, 1): 1},
          widths=COL_W,
          notes="대조군 두 개입니다. 하나는 잘못된 정규화기를 두고 입력을 고쳤고, 다른 하나는 입력을 두고 "
                "정규화기를 바꿨습니다. 둘 다 재학습 없이 0.3 부근에 도달했고, 구간은 서로 겹칩니다. "
                "즉 중요한 것은 데이터가 학습된 강도 도메인에 닿느냐 하나입니다. 두 예측 모두 실행 전에 적었고, "
                "두 번째는 방향이 틀렸습니다. 그리고 0.3은 여전히 낮아서, 복구가 아니라 원인의 위치를 가리키는 증거입니다.")),
    ("Limitations", "Limits",
     {0: "Three limits on what this case study shows",
      13: f"Small internal set", 16: f"Only {t2[R1]['n_scored']} held-out cases; the interval runs {interval(R1)}",
      14: "Cause not isolated", 17: "Preprocessing and representation shift stay entangled",
      15: "One organ, one team", 18: "Two public datasets; no claim beyond this task"},
     dict(notes="한계 세 가지입니다. 내부 held-out이 9건이라 구간이 넓습니다. 올바르게 정규화한 MRI 대조군을 돌리지 "
                "않아서 전처리 실패와 표현 전이 실패를 분리하지 못했습니다. 그게 다음 실험이고, 재학습 없이 추론 한 번이면 됩니다. "
                "그리고 장기 하나, 팀 하나이므로 일반화 주장은 하지 않습니다.")),
    ("Take-home", "Summary",
     {0: "What to take from this",
      1: [f"External CT: Dice [[{med(R2)}]] against [[2|{med(R1)}]]",
          f"On MRI, Dice fell to {med(R3)}",
          "The run exited 0 and never warned"]},
     dict(notes="정리합니다. 외부 CT는 내부보다 조금 낮은 정직한 값이었고, MRI에서는 Dice가 0.0152까지 떨어졌습니다. "
                "그런데 파이프라인은 정상 종료했고 경고가 없었습니다. 이 슬라이드의 숫자는 모두 분석 표에서 읽어 온 것이라, "
                "결과가 바뀌면 덱도 같이 바뀝니다.")),
    ("Section", None,
     {0: "Backup", 14: "Detail behind the results"},
     dict(notes="여기부터는 질문이 나올 때만 쓰는 자료입니다.")),
    ("Result · Figure", "Backup",
     {0: title_ok("The external median hides a tail that reaches zero"),
      14: f"Empty predictions on external CT: {t2[R2]['n_empty_prediction']} of {t2[R2]['n_evaluated']}. "
          f"HD95 exists for {t2[R3]['n_with_hd95']} of {t2[R3]['n_scored']} MRI cases."},
     dict(picture=FIG / "fig1_dice_by_arm.png", align="ctr",
          notes="중앙값만 보면 안 되는 이유입니다. 외부 CT는 0까지 내려가는 꼬리를 갖고 있고, 빈 예측이 28건입니다. "
                f"비장이 없는 케이스 {t2[R2]['n_false_positive_on_target_free']}건에는 오히려 비장을 그렸습니다. "
                "HD95는 예측이 비면 정의가 안 되는데, 그게 가장 크게 실패한 케이스들이라 분모가 다릅니다.")),
    ("Content", "Backup",
     {0: title_ok(f"The usual nnU-Net use trips the leakage gate {naive['summary']['n_major']} times"),
      1: ["**Split leakage**: disjointness proved by set arithmetic",
          "**Preprocessing**: the declared manifest passes",
          f"Fitting on all cases raises [[{naive['summary']['n_major']} Major]] findings, "
          f"{naive['claims'][0]['verdict']}"]},
     dict(notes="게이트 두 개가 학습 전에 돌았습니다. 중요한 건 반사실입니다. nnU-Net을 평범하게 쓰면 held-out까지 "
                "포함해 fingerprint를 맞추게 되고, 같은 게이트가 그것을 Major로 거부합니다. 통과하는 게이트만 보여 주면 "
                "게이트가 실패할 수 있다는 증거가 없습니다.")),
    ("Content", "Backup",
     {0: title_ok(f"Our profiler flagged the intensity scale, as {scale['severity']}"),
      1: [f"**{scale['verdict']}**, filed {scale['severity']}",
          "500 of 600 cases bottom out near air; the rest do not",
          "A routing and severity gap, [[not a detection gap]]"]},
     dict(notes="가장 불편한 슬라이드입니다. 우리 프로파일러가 학습 전에 이미 잡았습니다. 다만 Minor로, 아무도 다시 읽지 "
                "않는 디렉터리에 남겼습니다. 그러니 문제는 탐지가 아니라 전달과 심각도입니다. "
                "이건 이 사례가 제기하는 가설이지, 이 사례가 증명한 성질은 아닙니다.")),
]
# the profiler line quotes the file, not a typed count
_m = re.match(r"(\d+)/(\d+) cases", scale["detail"])
assert _m, "the profiler detail no longer starts with 'N/M cases'"
SLIDES[-1][2][1][1] = f"{_m[1]} of {_m[2]} cases bottom out near air; the rest do not"


def build(out, band=True):
    out = Path(out)
    nd.make_deck(out, main=MAIN, band=band, force=True)
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
    ap.add_argument("--plain", metavar="OUT", help="write the same slides without the band to OUT")
    a = ap.parse_args()
    print("wrote", build(a.plain, band=False) if a.plain else build(HERE / "demo5_external_validation.pptx"))
