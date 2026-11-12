"""Reference-blank false-positive rates for each OCR, group and field.

Run after run_ocr_accuracy.py. A false positive is a populated OCR value against
a blank normalized Human 1 value within an established matched comparison.
These are reference-discordant additions, not adjudicated hallucinations.
"""
import argparse
import csv
from pathlib import Path
from analyse_accuracy import ROOT,write

def rates(row):
    fp=int(row['candidate_only_values'])
    blank=fp+int(row['both_missing'])
    populated=int(row['correct'])+int(row['substitutions'])+fp
    return dict(false_positive_values=fp,reference_blank_cells=blank,
        false_positive_rate_among_reference_blanks=fp/blank if blank else '',
        populated_ocr_values=populated,
        unsupported_share_of_populated_ocr=fp/populated if populated else '',
        compared_cells=int(row['compared_cells']),
        false_positive_share_of_all_compared_cells=fp/int(row['compared_cells']) if int(row['compared_cells']) else '')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=ROOT/'OUTPUTS/hcc_pseudonymised_agreement/05_ocr_accuracy_vs_Human_1')
    p.add_argument('--output',type=Path,default=ROOT/'OUTPUTS/hcc_pseudonymised_agreement/06_ocr_false_positives_vs_Human_1')
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    for source,name,byfield in [('accuracy_summary.csv','false_positive_rates',False),('all_field_accuracy.csv','field_false_positive_rates',True)]:
        with (args.input/source).open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        result=[]
        for row in rows:
            identity={k:row[k] for k in ['ocr_experiment','group_level','group_code']+(['field'] if byfield else [])}
            result.append(dict(**identity,**rates(row)))
        write(args.output/(name+'.csv'),result,['ocr_experiment'])
        for level in ('aggregate','district','facility'):
            write(args.output/(level+'_'+name+'.csv'),[r for r in result if r['group_level']==level],['ocr_experiment'])
    (args.output/'README.md').write_text(
        '# OCR false positives against Human 1\n\nFalse positives = populated OCR cells against normalized blank Human 1 cells. The primary rate divides these by all blank Human 1 cells (false positives + both-missing cells). The unsupported share divides by all populated OCR cells (correct + substitutions + false positives). A third column divides by all compared cells. They answer different questions and are not interchangeable.\n\n'
        'The same 14 facilities, field exclusions, normalization, matched cards and matched visits as the OCR accuracy analysis apply. Card-level fields are counted once per matched card. All-missing Human 1 fields and the explicitly excluded fields do not contribute. Unmatched records are not scored. Different models have different matched subsets and denominators. A blank in Human 1 does not establish that the OCR value is clinically wrong; these additions need source-form adjudication.\n',encoding='utf-8')
    with (args.output/'aggregate_false_positive_rates.csv').open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f): print(row)

if __name__=='__main__':
    main()
