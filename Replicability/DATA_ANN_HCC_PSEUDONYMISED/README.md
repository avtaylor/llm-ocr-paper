# HCC-pseudonymised structured data

Separate copy of DATA_ANN. HCC numbers are replaced by random, facility-specific codes shared across all human and OCR datasets. Identifier-bearing card filenames and filename references use stable source_card_id values. hcc_match_suffix is a random coded matching aid preserving the original numeric-suffix equality; exclude it from field scoring. Use CODE/ANALYSIS/HCC_Pseudonymised_Agreement for compatible matching and scoring. No original-to-replacement mappings are included here.

Previously cleared unique_child_id and HIV sample ID columns remain cleared. Other clinical values, including dates and any remaining identifier fields, are preserved. This is pseudonymisation, not full anonymisation. Individual cards and merged visits are duplicate representations: do not count both. reconstruction_validation.csv describes the earlier location-coding stage; its reconstruction statuses are superseded here.
