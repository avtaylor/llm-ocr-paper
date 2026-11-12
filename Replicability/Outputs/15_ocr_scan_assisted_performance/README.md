# Scan-assisted OCR performance

The 14 OCR comparison facilities are used throughout. Previously established one-to-one card correspondences, including scan-assisted matches, are retained by stable IDs within district and facility. The proposed H2 link for 1064 is held in the separate identifier review CSV and is outside this run.

Accuracy is exact normalized agreement divided by populated reference values. Unsupported share is populated OCR values against a blank human reference divided by all populated OCR values on compared cells. The CSVs also report the rate among reference blanks. Cards and visits outside the matched sets are coverage gaps. Reference blanks need scan review to determine whether an OCR value is correct. See the per-comparison reports for field exclusions and visit alignment.

Previously established correspondences take precedence over recomputed identifier matches. See 14_ocr_scan_matching/established_pair_reconciliation.csv for differences. Current pseudonymised clinical values are used for all scoring.
