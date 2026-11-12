# Location-coded structured datasets

Facility codes used are F1-F16 and district codes are D1-D4. Card filenames start with HCC_<identifier> or UID_<identifier>, followed by __ and the stable source_card_id, then _visits_export.csv. NO_ID explicitly marks missing identifiers. Source_card_id values remain F<facility>_<domain>_<sequence>, distinguishing repeated identifiers. Individual Human 1 and OCR CSVs are in cards/F* folders alongside canonical merged visits.csv files. Human 2 CSVs are in Human_2/F*. Count the merged files OR the individual cards, never both.

Human filenames preserve recognised original identifier stems. The original OCR PDF retains the same source_card_id across models. batch_membership.csv links cards to batches, and human_card_correspondence.csv records established human matches. Full filename reconstruction and raw-source lookup are in the separately held key.

We appled a reversible LOCATION PSEUDONYMISATION. Patient identifiers, clinical dates and other clinical values are retained except for location coding. It is not full patient anonymisation. Scanned documents/images and raw API payloads are not included or redacted. Keep the reconstruction key separate from any shared data.

Source-path columns are removed; absolute user paths are cleared. Facility/district labels in text and configured HCC facility prefixes are location-coded. Original row order is preserved for reconstruction.
