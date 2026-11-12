"""Rebuild selected agreement reports using DATA_ANN and bundled matching rules."""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from match_cards import ROOT
from analyse_accuracy import run, write

HERE = Path(__file__).resolve().parent
REPORTS = ROOT / "OUTPUTS/selected_agreement"

def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def call(script, *args):
    subprocess.run([sys.executable, str(HERE / script), *map(str, args)], cwd=ROOT, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=["gpt56_terra", "gpt41_mini", "qwen", "gpt4o_mini", "nemotron"],
                        choices=["gpt56_terra", "gpt41_mini", "qwen", "gpt4o_mini", "nemotron"],
                        help="Models for shared-card and field analyses; all five still run in the overall comparison.")
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    call("match_cards.py")
    call("run_ocr_card_matches.py")
    for ref, cand in (("Human_1", "Human_2"), ("Human_2", "Human_1")):
        call("analyse_accuracy.py", "--reference", ref, "--candidate", cand,
             "--matches", REPORTS / "03_card_matches_Human_1_vs_Human_2")
    for ref in ("Human_1", "Human_2"):
        call("run_ocr_accuracy.py", "--reference", ref)

    human_pairs = rows(REPORTS / "03_card_matches_Human_1_vs_Human_2/matched_card_pairs.csv")
    shared = REPORTS / "16_ocr_shared_human_card_performance"
    combined, cohort = [], []
    for model in args.models:
        folders = [REPORTS / f"03_card_matches_OCR_{model}_vs_{ref}" for ref in ("Human_1", "Human_2")]
        indexes = [{r["right_card_id"]: r for r in rows(f / "matched_card_pairs.csv")} for f in folders]
        selected = [[], []]
        for pair in human_pairs:
            a = indexes[0].get(pair["left_card_id"])
            b = indexes[1].get(pair["right_card_id"])
            included = bool(a and b and a["left_card_id"] == b["left_card_id"])
            cohort.append(dict(model=model, human_1_card_id=pair["left_card_id"],
                               human_2_card_id=pair["right_card_id"], included=included))
            if included:
                selected[0].append(a)
                selected[1].append(b)
        for ref, source, pairs in zip(("Human_1", "Human_2"), folders, selected):
            name = f"OCR_{model}_vs_{ref}"
            matches = shared / "matches" / name
            matches.mkdir(parents=True, exist_ok=True)
            manifest = json.loads((source / "run_manifest.json").read_text())
            manifest["selected_shared_card_pairs"] = len(pairs)
            (matches / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            write(matches / "matched_card_pairs.csv", pairs, list(rows(source / "matched_card_pairs.csv")[0]))
            output = shared / "comparisons" / name
            run(SimpleNamespace(data=ROOT / "DATA_ANN", reference=ref, candidate="OCR_" + model,
                                matches=matches, output=output))
            combined.extend(dict(model=model, reference=ref, **r) for r in rows(output / "accuracy_summary.csv"))
    write(shared / "shared_card_cohort.csv", cohort, ["model", "included"])
    for level in ("aggregate", "district", "facility"):
        write(shared / f"{level}_performance.csv", [r for r in combined if r["group_level"] == level], ["model", "reference"])
    call("three_way_ocr_agreement.py")
    import field_type_agreement
    field_type_agreement.MODELS = tuple(args.models)
    sys.argv = [str(HERE / "field_type_agreement.py")]
    field_type_agreement.main()
    print("Completed selected agreement reports:", REPORTS)

if __name__ == "__main__":
    main()
