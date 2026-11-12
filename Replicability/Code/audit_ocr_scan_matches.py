"""Measure OCR card matches recoverable through established human-to-scan links."""

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from match_cards import ROOT, run, write

HERE = Path(__file__).resolve().parent
DETAIL_FIELDS = (
    "model reference district_code facility_code human_card_id ocr_card_id "
    "human_hcc ocr_hcc birth_date_check status current_human_for_scan"
).split()
PAIR_FIELDS = (
    "district_code facility_code left_card_id right_card_id match_method "
    "left_hcc right_hcc left_birth_date right_birth_date"
).split()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def links_by_human(path, domain):
    links = defaultdict(set)
    for row in read_csv(path):
        if row["source_domain"] == domain and row["link_status"] == "established_match":
            human = row["source_card_id"]
            scan_ids = row["ocr_source_card_ids"].split(" | ")
            prefix = row["facility_code"] + "_"
            if any(not scan.startswith(prefix + "OCR_") for scan in scan_ids) or not human.startswith(prefix):
                raise ValueError(f"Invalid scan link for {human}")
            links[human].update(scan_ids)
    return links


def check_links(model, reference, links, pairs, unresolved, excluded):
    matched_scans = {r["left_card_id"]: r["right_card_id"] for r in pairs}
    unmatched_scans = {r["source_card_id"]: r for r in unresolved if r["side"] == "left"}
    unmatched_humans = {r["source_card_id"]: r for r in unresolved if r["side"] == "right"}
    eligible_humans = set(matched_scans.values()) | unmatched_humans.keys()
    scan_claims = defaultdict(set)
    for human in eligible_humans:
        for scan in links.get(human, ()):
            scan_claims[scan].add(human)

    detail = []
    for human, reference_row in sorted(unmatched_humans.items()):
        candidates = links.get(human, ())
        for scan in sorted(candidates):
            ocr_row = unmatched_scans.get(scan)
            owner = matched_scans.get(scan, "")
            if len(candidates) > 1 or len(scan_claims[scan]) > 1:
                status = "ambiguous_crosswalk"
            elif owner:
                status = "scan_already_paired"
            elif scan in excluded:
                status = "scan_excluded"
            elif ocr_row is None:
                status = "scan_not_in_model"
            else:
                assert (reference_row["district_code"], reference_row["facility_code"]) == (
                    ocr_row["district_code"], ocr_row["facility_code"]
                )
                status = "additional_scan_match"
            human_dob = reference_row["birth_date"]
            ocr_dob = ocr_row["birth_date"] if ocr_row else ""
            dob_check = ""
            if ocr_row:
                if not human_dob or not ocr_dob:
                    dob_check = "missing"
                elif " | " in human_dob or " | " in ocr_dob:
                    dob_check = "multiple_values"
                else:
                    dob_check = "agree" if human_dob == ocr_dob else "differ"
            detail.append(dict(
                model=model, reference=reference, district_code=reference_row["district_code"],
                facility_code=reference_row["facility_code"], human_card_id=human, ocr_card_id=scan,
                human_hcc=reference_row["hcc"], ocr_hcc=ocr_row["hcc"] if ocr_row else "",
                birth_date_check=dob_check, status=status, current_human_for_scan=owner,
            ))
    return detail


def save_pairs(output, manifest, pairs, added, unresolved, crosswalk):
    unmatched = {r["source_card_id"]: r for r in unresolved}
    assisted_pairs = []
    for row in added:
        ocr = unmatched[row["ocr_card_id"]]
        human = unmatched[row["human_card_id"]]
        assisted_pairs.append(dict(
            district_code=row["district_code"], facility_code=row["facility_code"],
            left_card_id=ocr["source_card_id"], right_card_id=human["source_card_id"],
            match_method="established_scan_crosswalk",
            left_hcc=ocr["hcc"], right_hcc=human["hcc"],
            left_birth_date=ocr["birth_date"], right_birth_date=human["birth_date"],
        ))
    combined = pairs + assisted_pairs
    assert len({r["left_card_id"] for r in combined}) == len(combined)
    assert len({r["right_card_id"] for r in combined}) == len(combined)
    totals = manifest["totals"]
    totals.update(matched_pairs=len(combined), left_unmatched=totals["left_cards"] - len(combined),
                  right_unmatched=totals["right_cards"] - len(combined))
    manifest.update(
        baseline_pairs=len(pairs), added_scan_pairs=len(assisted_pairs),
        scan_crosswalk=crosswalk,
        method=manifest["method"] + " Then add established one-to-one scan links for still-unmatched cards.",
    )
    output.mkdir(parents=True, exist_ok=True)
    write(output / "matched_card_pairs.csv", combined, PAIR_FIELDS)
    write(output / "added_scan_pairs.csv", assisted_pairs, PAIR_FIELDS)
    manifest["matched_card_pairs_sha256"] = hashlib.sha256((output / "matched_card_pairs.csv").read_bytes()).hexdigest()
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def audit(args):
    args.output.mkdir(parents=True, exist_ok=True)
    models = sorted(path.parent.name for path in (args.data / "OCR").glob("*/visits.csv") if path.parent.name != "gpt_ocr")
    if not models:
        raise ValueError(f"No OCR data under {args.data}")
    crosswalk = dict(path=str(args.crosswalk.resolve()),
                     sha256=hashlib.sha256(args.crosswalk.read_bytes()).hexdigest())
    summary, detail, differences = [], [], []
    for reference, domain in (("Human_1", "H1"), ("Human_2", "H2")):
        links = links_by_human(args.crosswalk, domain)
        for model in models:
            with TemporaryDirectory(dir=args.output) as temp:
                directory = Path(temp)
                with redirect_stdout(io.StringIO()):
                    run(argparse.Namespace(
                        data=args.data, left="OCR_" + model, right=reference,
                        overrides=args.overrides, hints=args.hints, output=directory,
                    ))
                manifest = json.loads((directory / "run_manifest.json").read_text())
                totals = manifest["totals"]
                pairs = read_csv(directory / "matched_card_pairs.csv")
                unresolved = read_csv(directory / "unmatched_cards.csv")
                excluded = {r["source_card_id"] for r in read_csv(directory / "excluded_cards.csv")
                            if r["side"] == "left"}
            established_path = args.data / "established_card_pairs.csv"
            if established_path.exists():
                established = [r for r in read_csv(established_path)
                               if r["model"] == model and r["reference"] == reference]
                # Values are drawn from the current pseudonymised data, while the
                # validated correspondences contain stable IDs only.
                ocr_cards, human_cards = {}, {}
                for pair in pairs:
                    ocr_cards[pair["left_card_id"]] = (pair["left_hcc"], pair["left_birth_date"])
                    human_cards[pair["right_card_id"]] = (pair["right_hcc"], pair["right_birth_date"])
                for row in unresolved:
                    cards = ocr_cards if row["side"] == "left" else human_cards
                    cards[row["source_card_id"]] = (row["hcc"], row["birth_date"])
                fixed = []
                for row in established:
                    a, b = row["left_card_id"], row["right_card_id"]
                    if a not in ocr_cards or b not in human_cards:
                        raise ValueError(f"Established correspondence is missing or excluded: {model}, {reference}, {a}, {b}")
                    if not a.startswith(row["facility_code"] + "_") or not b.startswith(row["facility_code"] + "_"):
                        raise ValueError("Established correspondence crosses facility")
                    fixed.append(dict(
                        district_code=row["district_code"], facility_code=row["facility_code"],
                        left_card_id=a, right_card_id=b, match_method=row["match_method"],
                        left_hcc=ocr_cards[a][0], right_hcc=human_cards[b][0],
                        left_birth_date=ocr_cards[a][1], right_birth_date=human_cards[b][1],
                    ))
                current_pairs = {(r["left_card_id"], r["right_card_id"]) for r in pairs}
                fixed_pairs = {(r["left_card_id"], r["right_card_id"]) for r in fixed}
                retained_baseline = len(current_pairs & fixed_pairs)
                for a, b in sorted(current_pairs - fixed_pairs):
                    differences.append(dict(model=model, reference=reference, left_card_id=a,
                        right_card_id=b, status="recomputed_pair_superseded_by_established_correspondences"))
                for a, b in sorted(fixed_pairs - current_pairs):
                    differences.append(dict(model=model, reference=reference, left_card_id=a,
                        right_card_id=b, status="retained_previously_established_pair"))
                summary.append(dict(
                    model=model, reference=reference, eligible_human_cards=totals["right_cards"],
                    baseline_matches=retained_baseline, additional_scan_matches=len(fixed) - retained_baseline,
                    scan_assisted_matches=len(fixed),
                    remaining_unmatched_human_cards=totals["right_cards"] - len(fixed),
                    added_with_different_birth_date=sum(
                        r["left_birth_date"] != r["right_birth_date"] for r in fixed
                        if (r["left_card_id"], r["right_card_id"]) not in current_pairs
                        and r["left_birth_date"] and r["right_birth_date"]),
                ))
                output = args.output / "matches" / f"OCR_{model}_vs_{reference}"
                save_pairs(output, manifest, fixed, [], unresolved, crosswalk)
                manifest.update(
                    baseline_pairs=retained_baseline, added_scan_pairs=len(fixed) - retained_baseline,
                    established_correspondences=dict(path=str(established_path.resolve()),
                        sha256=hashlib.sha256(established_path.read_bytes()).hexdigest()),
                    method="Previously established one-to-one card correspondences, retained by stable IDs; current data used for scoring.",
                )
                write(output / "added_scan_pairs.csv", [r for r in fixed
                      if (r["left_card_id"], r["right_card_id"]) not in current_pairs], PAIR_FIELDS)
                (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                continue
            rows = check_links(model, reference, links, pairs, unresolved, excluded)
            added = [r for r in rows if r["status"] == "additional_scan_match"]
            assert len({r["human_card_id"] for r in added}) == len({r["ocr_card_id"] for r in added}) == len(added)
            summary.append(dict(
                model=model, reference=reference, eligible_human_cards=totals["right_cards"],
                baseline_matches=len(pairs), additional_scan_matches=len(added),
                scan_assisted_matches=len(pairs) + len(added),
                remaining_unmatched_human_cards=totals["right_unmatched"] - len(added),
                added_with_different_birth_date=sum(r["birth_date_check"] == "differ" for r in added),
            ))
            detail.extend(rows)
            save_pairs(args.output / "matches" / f"OCR_{model}_vs_{reference}", manifest,
                       pairs, added, unresolved, crosswalk)
    write(args.output / "match_coverage.csv", summary, list(summary[0]))
    write(args.output / "scan_link_review.csv", detail, DETAIL_FIELDS)
    write(args.output / "established_pair_reconciliation.csv", differences, ["model", "reference", "left_card_id", "right_card_id", "status"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "DATA_ANN_HCC_PSEUDONYMISED")
    parser.add_argument("--crosswalk", type=Path,
                        default=ROOT / "DATA_ANN_HCC_PSEUDONYMISED/established_scan_links.csv")
    parser.add_argument("--overrides", type=Path, default=HERE / "card_match_overrides.json")
    parser.add_argument("--hints", type=Path, default=HERE / "card_filename_identifiers.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "OUTPUTS/hcc_pseudonymised_agreement/14_ocr_scan_matching")
    audit(parser.parse_args())
