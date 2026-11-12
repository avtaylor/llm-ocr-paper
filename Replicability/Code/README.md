# Selected agreement scripts

Run from the project root:

```powershell
python CODE/ANALYSIS/Selected_Agreement/run_selected_agreements.py
```

Inputs: project `DATA_ANN` plus the two bundled matching configuration files. 
Outputs: `OUTPUTS/selected_agreement`. Original scripts and previous `OUTPUTS/replicable` reports are unchanged.

| Requested analysis | Selected script | Outputs |
| --- | --- | --- |
| All OCR experiments versus H1, excluding GPT-OCR general | run_ocr_accuracy.py | 05_ocr_accuracy_vs_Human_1; aggregate, district, facility and per-field reports |
| Matched cards and visits | match_cards.py, run_ocr_card_matches.py, analyse_accuracy.py | 03_card_matches_*, matched_card_pairs.csv, card_visit_coverage.csv and accuracy_summary.csv in comparison folders |
| H1 versus H2 and H2 versus H1 | analyse_accuracy.py | 04_accuracy_Human_2_vs_Human_1 and 04_accuracy_Human_1_vs_Human_2 |
| Models versus H1 and H2 | run_ocr_accuracy.py | 05_ocr_accuracy_vs_Human_1 and 05_ocr_accuracy_vs_Human_2 |
| Pairwise on shared human cards, three-way and human consensus | run_selected_agreements.py, three_way_ocr_agreement.py | 16_ocr_shared_human_card_performance and 17_three_way_ocr_agreement |
| Per-field model/human and bidirectional human agreement | analyse_accuracy.py, field_type_agreement.py | all_field_accuracy.csv; 18_field_type_agreement/pairwise_by_field.csv and combined_agreement_by_field.csv |
| Grouped field-type and recording-method agreement | field_type_agreement.py | 18_field_type_agreement/*by_type.csv and agreement_by_recording_method.csv |

Five experiments are included: gpt56_terra, gpt41_mini, qwen, gpt4o_mini and nemotron. To restrict reports to your chosen best models, for example:

```powershell
python CODE/ANALYSIS/Selected_Agreement/run_selected_agreements.py --models gpt56_terra qwen
```

The overall model comparisons include all five experiments. Run the full workflow before running dependent report scripts separately. A subsequent run overwrites reports with the same names; use the latest shared-card summary to identify the models in that run.