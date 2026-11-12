"""Summarize exact human and shared-card OCR agreement by field type."""

import argparse
from collections import defaultdict
from pathlib import Path

from analyse_accuracy import CATEGORICAL, write
from extraction_effort import PATIENT_TYPES, TEST_TYPES, VISIT_TYPES
from ocr_false_positive_rates import rates
from three_way_ocr_agreement import (
    REPORTS, aligned_cells, candidate_key, reference_key, rows, summarize_cells,
)

MODELS = ("gpt56_terra", "gpt41_mini", "qwen", "gpt4o_mini", "nemotron")
FIELD_TYPES = {
    "Categorical": CATEGORICAL | {
        "sex", "guardian_relation", "mother_status_enrolment", "stopped_lt6m", "stopped_ge6m",
    } | {f"hiv_test_{i}_{kind}" for i in range(3) for kind in ("type", "result")},
    "Visit date": {"visit_date"},
    "Next appointment date": {"next_appointment_date"},
    "HIV testing dates": {
        f"hiv_test_{i}_sample_date" for i in range(3)
    } | {f"hiv_test_{i}_date_received" for i in range(3)},
    "Other dates": {"birth_date", "transfer_in_date", "art_start_date"},
    "Anthropometrics": {"weight_kg", "height_cm", "birth_weight_kg", "muac_cm"},
    "Age at visit": {"age_months"},
    "Enrolment age and NVP duration": {"age_at_enrolment", "nvp_duration"},
    "CPT": {"cpt"},
    "Birth cohort": {"birth_cohort_month", "birth_cohort_year"},
    "Identifiers": {"hcc_reg_no", "unique_child_id"},
    "NVP start (legacy field)": {"nvp_start_date"},
}
FIELD_TYPE = {field: name for name, fields in FIELD_TYPES.items() for field in fields}
COUNT_FIELDS = (
    "compared_cells", "reference_populated", "correct", "substitutions",
    "omissions", "errors", "candidate_only_values", "both_missing",
)
FORM_GROUPS = {
    "checkbox_or_circled_category": "Categorical (circled or ticked)",
    "handwritten_text_or_number": "Handwritten, excluding dates",
    "date": "Dates",
    "preprinted_visit_age": "Preprinted",
    "identifier_or_printed_context": "Mixed identifier",
}
FORM_TYPES = PATIENT_TYPES | VISIT_TYPES | {
    f"hiv_test_{i}_{suffix}": kind for i in range(4) for suffix, kind in TEST_TYPES.items()
} | {"age_months": "preprinted_visit_age"}


def aggregate_fields(folder):
    return [r for r in rows(folder / "all_field_accuracy.csv") if r["group_level"] == "aggregate"]


def pairwise(model, reference, fields):
    by_field = [dict(model=model, reference=reference, field_type=FIELD_TYPE[r["field"]], **r)
                for r in fields]
    by_type = []
    total_errors = sum(int(row["errors"]) for row in by_field)
    for kind in FIELD_TYPES:
        selected = [r for r in by_field if r["field_type"] == kind]
        if not selected:
            continue
        stats = {k: sum(int(r[k]) for r in selected) for k in COUNT_FIELDS}
        n, agree, different = (stats[k] for k in ("reference_populated", "correct", "substitutions"))
        assert n == agree + stats["errors"] and stats["errors"] == different + stats["omissions"]
        by_type.append(dict(
            model=model, reference=reference, field_type=kind, fields=len(selected), **stats,
            accuracy=agree / n if n else "",
            disagreement_rate=stats["errors"] / n if n else "",
            agreement_when_both_populated=agree / (agree + different) if agree + different else "",
            share_of_errors=stats["errors"] / total_errors if total_errors else "",
            **{k: v for k, v in rates(stats).items() if k != "compared_cells"},
        ))
    return by_type, by_field


def three_way(model, folders, human, allowed):
    grouped = defaultdict(list)
    for cell in aligned_cells(human, rows(folders[0] / "paired_values.csv"),
                              rows(folders[1] / "paired_values.csv")):
        field = cell[0][2]
        if field in allowed:
            grouped[field].append(cell)
    by_field = [dict(model=model, field=field, field_type=FIELD_TYPE[field], **summarize_cells(cells))
                for field, cells in sorted(grouped.items())]
    by_type = []
    for kind, fields in FIELD_TYPES.items():
        stats = summarize_cells(cell for field in sorted(fields) for cell in grouped.get(field, ()))
        if stats["cards_with_aligned_cells"]:
            by_type.append(dict(model=model, field_type=kind, **stats))
    return by_type, by_field


def combined_fields(human_fields, ocr_fields):
    ocr = {(r["field"], r["model"]): r for r in ocr_fields}
    human = {r["field"]: r for r in human_fields}
    for kind, fields in FIELD_TYPES.items():
        for field in sorted(fields & human.keys()):
            r = human[field]
            agree = int(r["correct"])
            h1_values = int(r["reference_populated"])
            h2_values = agree + int(r["substitutions"]) + int(r["candidate_only_values"])
            combined = dict(
                field_type=kind, field=field, h1_populated=h1_values, h2_populated=h2_values,
                human_exact_matches=agree, h2_vs_h1=agree / h1_values if h1_values else "",
                h1_vs_h2=agree / h2_values if h2_values else "", human_cohens_kappa=r["kappa"],
                human_kappa_pairs=r["kappa_n"],
            )
            for model in MODELS:
                row = ocr.get((field, model), {})
                combined[f"{model}_accuracy_on_human_consensus"] = row.get("ocr_accuracy_on_human_consensus", "")
                combined[f"{model}_consensus_matches"] = row.get("all_three_agree", "")
                combined[f"{model}_consensus_cells"] = row.get("human_consensus", "")
            yield combined


def by_recording_method(combined):
    grouped = defaultdict(list)
    for row in combined:
        group = FORM_GROUPS[FORM_TYPES[row["field"]]]
        grouped[group].append(dict(recording_method=group, **row))

    summaries = []
    for group in FORM_GROUPS.values():
        fields = grouped.get(group, [])
        if not fields or group == FORM_GROUPS["identifier_or_printed_context"]:
            continue
        exact = sum(row["human_exact_matches"] for row in fields)
        summary = dict(recording_method=group, fields=len(fields), human_exact_matches=exact)
        for ref, metric in (("h1", "h2_vs_h1"), ("h2", "h1_vs_h2")):
            n = sum(row[f"{ref}_populated"] for row in fields)
            summary[f"{ref}_populated"] = n
            summary[metric] = exact / n if n else ""
        for model in MODELS:
            correct = sum(int(row[f"{model}_consensus_matches"] or 0) for row in fields)
            n = sum(int(row[f"{model}_consensus_cells"] or 0) for row in fields)
            summary[f"{model}_consensus_matches"] = correct
            summary[f"{model}_consensus_cells"] = n
            summary[f"{model}_accuracy_on_human_consensus"] = correct / n if n else ""
        summaries.append(summary)
    return [row for group in FORM_GROUPS.values() for row in grouped.get(group, ())], summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--human", type=Path, default=REPORTS / "04_accuracy_Human_2_vs_Human_1")
    parser.add_argument("--ocr", type=Path, default=REPORTS / "16_ocr_shared_human_card_performance")
    parser.add_argument("--output", type=Path, default=REPORTS / "18_field_type_agreement")
    args = parser.parse_args()
    human_fields = aggregate_fields(args.human)
    allowed = {r["field"] for r in human_fields}
    if allowed - FIELD_TYPE.keys():
        raise ValueError(f"Unclassified fields: {sorted(allowed - FIELD_TYPE.keys())}")
    human = {(reference_key(r), candidate_key(r)): (r["reference_normalized"], r["candidate_normalized"])
             for r in rows(args.human / "paired_values.csv")}
    comparisons = args.ocr / "comparisons"
    pair_types, pair_fields = pairwise("Human_2", "Human_1", human_fields)
    triple_types, triple_fields = [], []
    for model in MODELS:
        folders = [comparisons / f"OCR_{model}_vs_{ref}" for ref in ("Human_1", "Human_2")]
        for folder, ref in zip(folders, ("Human_1", "Human_2")):
            selected = [r for r in aggregate_fields(folder) if r["field"] in allowed]
            types, fields = pairwise(model, ref, selected)
            pair_types.extend(types)
            pair_fields.extend(fields)
        types, fields = three_way(model, folders, human, allowed)
        triple_types.extend(types)
        triple_fields.extend(fields)

    combined = list(combined_fields(human_fields, triple_fields))
    recording_fields, recording_summary = by_recording_method(combined)
    args.output.mkdir(parents=True, exist_ok=True)
    for name, records in (
        ("pairwise_by_type", pair_types), ("pairwise_by_field", pair_fields),
        ("three_way_by_type", triple_types), ("three_way_by_field", triple_fields),
        ("combined_agreement_by_field", combined),
        ("combined_agreement_by_recording_method_and_field", recording_fields),
        ("agreement_by_recording_method", recording_summary),
    ):
        write(args.output / f"{name}.csv", records, ["model"])
    write(args.output / "field_types.csv",
          [dict(field=field, field_type=FIELD_TYPE[field]) for field in sorted(allowed)], ["field", "field_type"])
    (args.output / "README.md").write_text(
        "# Agreement by field type\n\n"
        "Human 2 is compared with Human 1 on their shared cards across the 14 facilities. "
        "Each OCR is scored on the subset of those cards matched to the same OCR card in both references. "
        "GPT app is excluded. All reports use fields eligible in the H2-versus-H1 comparison, "
        "so fields blank throughout H1, including HIV sample IDs, are excluded from the OCR–H2 summaries too.\n\n"
        "Pairwise exact agreement divides matches by populated reference values. Errors include omissions and "
        "different populated values. Unsupported additions are reported separately. The per-field CSV retains "
        "existing date and numeric tolerance statistics and kappa for the seven designated categorical indicators. "
        "CPT is its own group. The legacy NVP start field is separated from the other date fields.\n\n"
        "Three-way agreement uses aligned cells populated by both humans. OCR accuracy on human consensus "
        "uses the subset where the human values also agree. Blank OCR values count as disagreements. "
        "The combined table shows both directions of human agreement, each divided by the number of "
        "populated values in its reference, alongside OCR accuracy on human consensus. "
        "The recording-method tables use the form inventory. The preprinted group contains only visit age. "
        "Unique child ID has a mixed recording method and appears only in the per-field table. "
        "The legacy NVP start field is grouped with handwriting "
        "because the inspected form asks for initiation age. Group rates pool cell counts. "
        "Age and visit date help align visits, so agreement on these fields is conditional on matching. "
        "Identifiers may contribute to card matching.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
