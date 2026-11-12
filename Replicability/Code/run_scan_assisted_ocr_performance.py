"""Save scan-assisted OCR correspondences and score OCR against both human references."""

import argparse
import hashlib
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from analyse_accuracy import ROOT, run, write
from audit_ocr_scan_matches import HERE, PAIR_FIELDS, audit, read_csv
from match_cards import run as match_cards
from ocr_false_positive_rates import rates

REPORTS = ROOT / "OUTPUTS/hcc_pseudonymised_agreement"


def shared_card_matches(args, coverage):
    args.output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=args.output) as temp:
        folder = Path(temp)
        with redirect_stdout(io.StringIO()):
            match_cards(argparse.Namespace(
                data=args.data, left="Human_1", right="Human_2",
                overrides=args.overrides, hints=args.hints, output=folder,
            ))
        human_pairs = read_csv(folder / "matched_card_pairs.csv")
        human_pairs_hash = hashlib.sha256((folder / "matched_card_pairs.csv").read_bytes()).hexdigest()

    matches = args.output / "matches"
    cohort = []
    scored = []
    for model in sorted({row["model"] for row in coverage}):
        h1_name, h2_name = f"OCR_{model}_vs_Human_1", f"OCR_{model}_vs_Human_2"
        source = args.match_output / "matches"
        h1 = {r["right_card_id"]: r for r in read_csv(source / h1_name / "matched_card_pairs.csv")}
        h2 = {r["right_card_id"]: r for r in read_csv(source / h2_name / "matched_card_pairs.csv")}
        selected1, selected2 = [], []
        for pair in human_pairs:
            a, b = pair["left_card_id"], pair["right_card_id"]
            left, right = h1.get(a), h2.get(b)
            scan1 = left["left_card_id"] if left else ""
            scan2 = right["left_card_id"] if right else ""
            same_scan = bool(scan1 and scan1 == scan2)
            if same_scan:
                for row in (left, right):
                    assert all(row[k] == pair[k] for k in ("district_code", "facility_code"))
                selected1.append(left)
                selected2.append(right)
            cohort.append(dict(
                model=model, district_code=pair["district_code"], facility_code=pair["facility_code"],
                human_1_card_id=a, human_2_card_id=b, ocr_scan_for_h1=scan1,
                ocr_scan_for_h2=scan2, included=same_scan,
            ))
        for name, reference, rows in ((h1_name, "Human_1", selected1), (h2_name, "Human_2", selected2)):
            output = matches / name
            output.mkdir(parents=True, exist_ok=True)
            pair_file = output / "matched_card_pairs.csv"
            write(pair_file, rows, PAIR_FIELDS)
            manifest = json.loads((source / name / "run_manifest.json").read_text())
            manifest["full_scan_assisted_pairs"] = manifest.pop("totals")["matched_pairs"]
            manifest["baseline_pairs_in_shared_cohort"] = sum(
                r["match_method"] != "established_scan_crosswalk" for r in rows
            )
            manifest["added_scan_pairs_in_shared_cohort"] = len(rows) - manifest["baseline_pairs_in_shared_cohort"]
            del manifest["baseline_pairs"], manifest["added_scan_pairs"]
            manifest.update(
                shared_human_pairs=len(human_pairs), shared_human_pairs_sha256=human_pairs_hash,
                matched_pairs=len(rows), matched_card_pairs_sha256=hashlib.sha256(pair_file.read_bytes()).hexdigest(),
                method=manifest["method"] + " Restrict to shared H1-H2 pairs with the same OCR scan.",
            )
            (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            scored.append(dict(model=model, reference=reference, scan_assisted_matches=len(rows)))
    write(args.output / "shared_card_cohort.csv", cohort, ["model", "included"])
    return matches, scored, len(human_pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "DATA_ANN_HCC_PSEUDONYMISED")
    parser.add_argument("--crosswalk", type=Path,
                        default=ROOT / "DATA_ANN_HCC_PSEUDONYMISED/established_scan_links.csv")
    parser.add_argument("--overrides", type=Path, default=HERE / "card_match_overrides.json")
    parser.add_argument("--hints", type=Path, default=HERE / "card_filename_identifiers.csv")
    parser.add_argument("--match-output", type=Path, default=REPORTS / "14_ocr_scan_matching")
    parser.add_argument("--shared-human-cards", action="store_true",
                        help="Score only H1-H2 pairs linked to the same scan in each experiment.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    args.output = args.output or REPORTS / (
        "16_ocr_shared_human_card_performance" if args.shared_human_cards else "15_ocr_scan_assisted_performance"
    )
    audit(argparse.Namespace(data=args.data, crosswalk=args.crosswalk, overrides=args.overrides,
                             hints=args.hints, output=args.match_output))
    coverage = read_csv(args.match_output / "match_coverage.csv")
    matches = args.match_output / "matches"
    scope = ""
    if args.shared_human_cards:
        matches, coverage, shared_count = shared_card_matches(args, coverage)
        scope = (f"The eligible cohort is the {shared_count} paired Human 1 and Human 2 cards. "
                 "Each experiment is scored on the subset linked to the same OCR scan for both humans. "
                 "Visit alignment is computed separately against each reference. "
                 "See shared_card_cohort.csv for included and excluded pairs.\n\n")

    combined = []
    for case in coverage:
        reference = case["reference"]
        candidate = "OCR_" + case["model"]
        comparison = f"{candidate}_vs_{reference}"
        output = args.output / "comparisons" / comparison
        print(f"Scoring {comparison}", flush=True)
        with redirect_stdout(io.StringIO()):
            run(argparse.Namespace(data=args.data, reference=reference, candidate=candidate,
                                   matches=matches / comparison, output=output))
        rows = read_csv(output / "accuracy_summary.csv")
        aggregate, = [row for row in rows if row["group_level"] == "aggregate"]
        assert int(aggregate["matched_cards"]) == int(case["scan_assisted_matches"])
        for level in ("district", "facility"):
            for column in ("matched_cards", "matched_visits", "reference_populated", "correct",
                           "candidate_only_values", "substitutions", "both_missing"):
                assert int(aggregate[column]) == sum(int(r[column]) for r in rows if r["group_level"] == level)
        combined.extend(dict(model=case["model"], reference=reference, **row, **{
            key: value for key, value in rates(row).items() if key != "compared_cells"
        }) for row in rows)

    for level in ("aggregate", "district", "facility"):
        write(args.output / f"{level}_performance.csv",
              [row for row in combined if row["group_level"] == level], ["model", "reference"])
    (args.output / "README.md").write_text(
        "# Scan-assisted OCR performance\n\n"
        "The 14 OCR comparison facilities are used throughout. Previously established one-to-one pairs are "
        "retained by stable card IDs, including prior scan-assisted matches, "
        "within district and facility. The proposed H2 link for 1064 is held in the separate "
        "identifier review CSV and is outside this run.\n\n" + scope +
        "Accuracy is exact normalized agreement divided by populated reference values. "
        "Unsupported share is populated OCR values against a blank human reference divided "
        "by all populated OCR values on compared cells. The CSVs also report the rate among "
        "reference blanks. Cards and visits outside the matched sets are coverage gaps. "
        "Reference blanks need scan review to determine whether an OCR value is correct. "
        "Previously established correspondences take precedence over recomputed identifier matches; see established_pair_reconciliation.csv. See the per-comparison reports for field exclusions and visit alignment.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
