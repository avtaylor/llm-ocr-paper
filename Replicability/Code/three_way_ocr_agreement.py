"""Score exact agreement on cells shared by Human 1, Human 2 and each OCR."""

import argparse
import csv
from collections import Counter
from pathlib import Path

from analyse_accuracy import ROOT, write

REPORTS = ROOT / "OUTPUTS/selected_agreement"


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def candidate_key(row):
    return row["candidate_card_id"], row["candidate_visit_index"], row["field"]


def reference_key(row):
    return row["reference_card_id"], row["reference_visit_index"], row["field"]


def aligned_cells(human, h1_ocr, h2_ocr):
    h2_index = {candidate_key(row): row for row in h2_ocr}
    for left in h1_ocr:
        key = candidate_key(left)
        right = h2_index.get(key)
        if right is None:
            continue
        # All three pairwise links must identify the same cell, including the
        # independently matched H1-H2 visit and the shared OCR visit.
        reference = human.get((reference_key(left), reference_key(right)))
        if reference is None:
            continue
        h1, h2 = reference
        ocr = left["candidate_normalized"]
        if (h1, h2, ocr) != (left["reference_normalized"], right["reference_normalized"],
                              right["candidate_normalized"]):
            raise ValueError(f"Normalized values changed between reports for {key}")
        if any(left[k] != right[k] for k in ("district_code", "facility_code", "level")):
            raise ValueError(f"Inconsistent group or field level for {key}")
        yield key, left["level"], h1, h2, ocr


def summarize_cells(cells):
    counts = Counter()
    cards, visits = set(), set()
    for key, level, h1, h2, ocr in cells:
        cards.add(key[0])
        if level == "visit":
            visits.add(key[:2])
        if not (h1 and h2):
            continue
        counts["both_humans_populated"] += 1
        counts["ocr_matches_h1"] += ocr == h1
        counts["ocr_matches_h2"] += ocr == h2
        if h1 != h2:
            continue
        counts["human_consensus"] += 1
        if h1 == ocr:
            counts["all_three_agree"] += 1
        elif not ocr:
            counts["ocr_blank_on_consensus"] += 1
        else:
            counts["ocr_different_on_consensus"] += 1

    both = counts["both_humans_populated"]
    consensus = counts["human_consensus"]
    agree = counts["all_three_agree"]
    return dict(
        cards_with_aligned_cells=len(cards), aligned_visits=len(visits),
        both_humans_populated=both, human_consensus=consensus, all_three_agree=agree,
        humans_differ=both - consensus,
        ocr_blank_on_consensus=counts["ocr_blank_on_consensus"],
        ocr_different_on_consensus=counts["ocr_different_on_consensus"],
        h1_h2_agreement=consensus / both if both else "",
        ocr_h1_agreement=counts["ocr_matches_h1"] / both if both else "",
        ocr_h2_agreement=counts["ocr_matches_h2"] / both if both else "",
        three_way_agreement=agree / both if both else "",
        ocr_accuracy_on_human_consensus=agree / consensus if consensus else "",
    )


def score(human, h1_ocr, h2_ocr):
    return summarize_cells(aligned_cells(human, h1_ocr, h2_ocr))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--human", type=Path,
                        default=REPORTS / "04_accuracy_Human_2_vs_Human_1" / "paired_values.csv")
    parser.add_argument("--ocr", type=Path, default=REPORTS / "16_ocr_shared_human_card_performance")
    parser.add_argument("--output", type=Path, default=REPORTS / "17_three_way_ocr_agreement")
    args = parser.parse_args()
    human = {(reference_key(row), candidate_key(row)):
             (row["reference_normalized"], row["candidate_normalized"]) for row in rows(args.human)}
    result = []
    for coverage in rows(args.ocr / "aggregate_performance.csv"):
        if coverage["reference"] != "Human_1":
            continue
        model = coverage["model"]
        comparisons = args.ocr / "comparisons"
        h1 = comparisons / f"OCR_{model}_vs_Human_1" / "paired_values.csv"
        h2 = comparisons / f"OCR_{model}_vs_Human_2" / "paired_values.csv"
        stats = score(human, rows(h1), rows(h2))
        assert stats["cards_with_aligned_cells"] == int(coverage["matched_cards"])
        result.append(dict(model=model, **stats))
    args.output.mkdir(parents=True, exist_ok=True)
    write(args.output / "aggregate_three_way_agreement.csv", result, ["model"])


if __name__ == "__main__":
    main()
