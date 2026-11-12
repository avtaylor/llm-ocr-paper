"""Describe extraction field slots and independent source observations per card.

Classification checked against the local HTML extraction template and two
representative Version 3 scans. These are potential reading tasks, not time
weights or counts of completed/visible values on every card.
"""
import argparse
import csv
import json
from collections import Counter,defaultdict
from pathlib import Path
from analyse_accuracy import ROOT,write

PATIENT_TYPES={
 'unique_child_id':'identifier_or_printed_context',
 'hcc_reg_no':'handwritten_text_or_number','transfer_in_date':'date',
 'birth_cohort_month':'handwritten_text_or_number','birth_cohort_year':'handwritten_text_or_number',
 'child_name':'handwritten_text_or_number','guardian_name':'handwritten_text_or_number',
 'physical_address':'handwritten_text_or_number','sex':'checkbox_or_circled_category',
 'child_age':'handwritten_text_or_number','agrees_to_fup':'checkbox_or_circled_category',
 'guardian_relation':'handwritten_text_or_number','guardian_phone':'handwritten_text_or_number',
 'mother_status_enrolment':'checkbox_or_circled_category','art_reg_no':'handwritten_text_or_number',
 'art_start_date':'date','age_at_enrolment':'handwritten_text_or_number',
 'nvp_start_date':'handwritten_text_or_number','two_p_duration_days':'handwritten_text_or_number',
 'nvp_duration':'handwritten_text_or_number',
 'birth_date':'date','birth_weight_kg':'handwritten_text_or_number'}
VISIT_TYPES={
 'age_months':'identifier_or_printed_context','visit_date':'date',
 'height_cm':'handwritten_text_or_number','weight_kg':'handwritten_text_or_number','muac_cm':'handwritten_text_or_number',
 'wasting_malnutrition':'checkbox_or_circled_category','breastfeeding':'checkbox_or_circled_category',
 'stopped_lt6m':'checkbox_or_circled_category','stopped_ge6m':'checkbox_or_circled_category',
 'mother_status':'checkbox_or_circled_category','abdominal_exam':'checkbox_or_circled_category',
 'hiv_testing':'checkbox_or_circled_category','hiv_infection':'checkbox_or_circled_category',
 'cpt':'handwritten_text_or_number','follow_up':'checkbox_or_circled_category','next_appointment_date':'date'}
TEST_TYPES={'sample_date':'date','type':'checkbox_or_circled_category','sample_id':'handwritten_text_or_number',
            'result':'checkbox_or_circled_category','date_received':'date'}
TYPES=['checkbox_or_circled_category','handwritten_text_or_number','date','identifier_or_printed_context']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'OUTPUTS/selected_agreement/10_extraction_effort')
    args=p.parse_args()
    taxonomy=[]
    for field,kind in PATIENT_TYPES.items():
        note=''
        if field=='unique_child_id': note='Identifier may be printed/sticker or handwritten; separate mixed-modality category.'
        if field=='child_age': note='Optional software field; not a separate verified printed box on the inspected form. Excluded from recommended core task count.'
        if field=='nvp_start_date': note='Legacy name: inspected form shows child age (days) at NVP initiation, not a date. Date HTML input is a schema mismatch; do not reinterpret source values automatically.'
        if field=='age_at_enrolment': note='2P child age at enrolment in the inspected four-cell enrolment grid.'
        if field=='two_p_duration_days': note='2P duration is a separate physical field, absent from the current CSV export schema. Proposed field name; no values imputed.'
        if field=='nvp_duration': note='NVP duration, separate from 2P duration and the two enrolment ages.'
        if field in {'child_name','guardian_name','physical_address','guardian_phone'}: note='May be redacted/not observable in study scans. Count only if in extraction scope and visible.'
        taxonomy.append(dict(section='patient_details_once',field=field,recording_type=kind,source_observation=field,
            repeated_per='card',optional_software_field=field=='child_age',possibly_redacted=field in {'child_name','guardian_name','physical_address','guardian_phone'},notes=note))
    for index in range(4):
        for suffix,kind in TEST_TYPES.items():
            field=f'hiv_test_{index}_{suffix}'
            taxonomy.append(dict(section='hiv_testing',field=field,recording_type=kind,source_observation=field,
                repeated_per='hiv_test_block',optional_software_field=False,possibly_redacted=False,
                notes='Fourth physical HIV-test block is present on inspected forms but omitted by the three-test batch converter.' if index==3 else ''))
    for field,kind in VISIT_TYPES.items():
        note=''
        if field=='age_months': note='Preprinted row label, usually not an independently handwritten value.'
        if field in {'stopped_lt6m','stopped_ge6m'}: note='Two binary output columns encode one stopped-breastfeeding source selection. Legacy m suffix differs from inspected printed six-week wording.'
        taxonomy.append(dict(section='visit_information',field=field,recording_type=kind,
            source_observation='breastfeeding_stopped' if field in {'stopped_lt6m','stopped_ge6m'} else field,
            repeated_per='documented_visit',optional_software_field=False,possibly_redacted=False,notes=note))
    profiles=[]
    for section,types in [('patient_details_once',PATIENT_TYPES),('one_hiv_test_block',TEST_TYPES),('one_visit',VISIT_TYPES)]:
        exported={f:k for f,k in types.items() if f!='two_p_duration_days'}
        count=Counter(exported.values())
        profiles.append(dict(view='export_field_slots',section=section,**{k:count[k] for k in TYPES},total=sum(count.values())))
        logical=dict(types)
        if section=='patient_details_once': logical.pop('child_age')
        if section=='one_visit': logical.pop('stopped_ge6m')
        count=Counter(logical.values())
        profiles.append(dict(view='independent_core_source_observations',section=section,**{k:count[k] for k in TYPES},total=sum(count.values())))
    scenarios=[]
    for blocks in (0,1,2,3,4):
        for visits in (0,1,5,10,15,25):
            checks=3+2*blocks+8*visits
            handwriting=14+blocks+4*visits
            dates=3+2*blocks+2*visits
            printed=1+visits
            scenarios.append(dict(hiv_test_blocks=blocks,documented_visits=visits,checkbox_or_category_tasks=checks,
                handwritten_text_or_number_tasks=handwriting,date_tasks=dates,identifier_or_printed_context_tasks=printed,
                independent_core_observations=checks+handwriting+dates+printed,
                observations_excluding_printed_context=checks+handwriting+dates,
                full_schema_field_slots_including_optional_child_age=21+5*blocks+16*visits,
                independent_core_if_four_personal_detail_fields_redacted=checks+handwriting+dates+printed-4))
    args.output.mkdir(parents=True,exist_ok=True)
    write(args.output/'field_recording_type_dictionary.csv',taxonomy,['section','field','recording_type'])
    write(args.output/'section_effort_counts.csv',profiles,['view','section','total'])
    write(args.output/'per_card_effort_scenarios.csv',scenarios,['hiv_test_blocks','documented_visits'])
    (args.output/'README.md').write_text(
        '# Extraction effort definitions\n\nA task is one source field or category decision, not one printed option or one repeated exported value. Checkbox includes circles/ticks on preprinted alternatives. Dates are counted separately from other handwriting. Child identifiers can be printed/stickers or handwritten and have a mixed-modality category; preprinted visit age is context.\n\n'
        'Recommended core: patient details 21 = 3 selections + 14 text/number + 3 dates + 1 identifier. The enrolment grid contains four separate handwritten fields: 2P enrolment age, NVP enrolment age, 2P duration and NVP duration. Each HIV block 5 = 2 selections + 1 sample ID + 2 dates. Each visit 15 = 8 selections + 4 numbers + 2 dates + 1 printed age label. Total = 21 + 5T + 15V. This excludes optional child_age and merges the two stopped-breastfeeding outputs into one source decision. District, facility, file names/paths and pseudonymous IDs are metadata and excluded. Repeated birth date/weight on page 2 count only once.\n\n'
        'Software export view still has 21 patient columns and 16 visit columns, giving 21 + 5T + 16V slots. It includes optional child_age but lacks a dedicated 2P duration column. The extended dictionary has 58 entries: 57 existing clinical columns plus proposed two_p_duration_days; this documents missing coverage, not newly extracted data. The batch converter retains three HIV test blocks; the inspected physical cards and Human 2 template provide four. The first annotator omitted sample IDs and other fields, and analysis exclusions further reduce scored cells; these are not measures of full extraction scope.\n\n'
        'nvp_start_date is a legacy schema name: inspected Version 3 forms show NVP initiation AGE, so the source effort category is text/number. Do not automatically reinterpret existing values or alter dates without a separate schema/data audit. The stopped breastfeeding printed wording is six weeks on these forms, despite legacy m column names. Optional/redacted fields are identified explicitly. For masked names/address/phone, subtract up to four tasks if they were not observable. One category group counts once, regardless of its number of alternatives. Actual workload depends on populated/visible fields, handwriting, corrections and review; these counts are not minutes or equally weighted cognitive effort.\n\n'
        'Sources inspected: CODE/FINAL/pink-card-html-only-ai-v5/pink-form-original.html; CODE/BEDROCK_BATCH/convert_bedrock_output.py; DATA/Samples/SampleA1815.pdf pages 1-2; DATA/Samples/SampleL16.pdf page 1. No source datasets or accuracy rules were modified.\n',encoding='utf-8')
    assert len(taxonomy)==58
    assert len(set(r['field'] for r in taxonomy))==58
    assert next(r['total'] for r in profiles if r['view']=='export_field_slots' and r['section']=='one_visit')==16
    for row in profiles: print(row)
    print('Example: three HIV blocks and ten visits',next(r for r in scenarios if r['hiv_test_blocks']==3 and r['documented_visits']==10))

if __name__=='__main__':
    main()
