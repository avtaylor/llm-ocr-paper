"""Rebuild selected agreement reports using DATA_ANN_HCC_PSEUDONYMISED and bundled matching rules."""
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
REPORTS = ROOT / "OUTPUTS/hcc_pseudonymised_agreement"

def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def call(script, *args):
    subprocess.run([sys.executable, str(HERE / script), *map(str, args)], cwd=ROOT, check=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", default=["gpt56_terra", "gpt41_mini", "qwen", "gpt4o_mini", "nemotron"],
                        choices=["gpt56_terra", "gpt41_mini", "qwen", "gpt4o_mini", "nemotron"],
                        help="Models for field analyses; all five run in the scan-assisted comparisons.")
    args = parser.parse_args()
    REPORTS.mkdir(parents=True, exist_ok=True)
    call("match_cards.py")
    call("run_ocr_card_matches.py")
    for ref, cand in (("Human_1", "Human_2"), ("Human_2", "Human_1")):
        call("analyse_accuracy.py", "--reference", ref, "--candidate", cand,
             "--matches", REPORTS / "03_card_matches_Human_1_vs_Human_2")
    for ref in ("Human_1", "Human_2"):
        call("run_ocr_accuracy.py", "--reference", ref)

    call("run_scan_assisted_ocr_performance.py")
    call("run_scan_assisted_ocr_performance.py", "--shared-human-cards")
    call("three_way_ocr_agreement.py")
    import field_type_agreement
    field_type_agreement.MODELS = tuple(args.models)
    sys.argv = [str(HERE / "field_type_agreement.py")]
    field_type_agreement.main()
    print("Completed selected agreement reports:", REPORTS)

if __name__ == "__main__":
    main()
