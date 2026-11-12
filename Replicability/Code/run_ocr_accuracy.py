"""Run each coded OCR experiment against a human reference at all reporting levels.

python CODE/ANALYSIS/Replicable/run_ocr_accuracy.py
python CODE/ANALYSIS/Replicable/run_ocr_accuracy.py --reference Human_2
Outputs: OUTPUTS/selected_agreement/05_ocr_accuracy_vs_<reference>.
Individual model reports remain in their 04_accuracy_* directories.
"""
import argparse
import csv
import json
from pathlib import Path
from types import SimpleNamespace
from analyse_accuracy import ROOT,run,write

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'DATA_ANN')
    parser.add_argument('--reference',choices=['Human_1','Human_2'],default='Human_1')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    args.output=args.output or ROOT/'OUTPUTS/selected_agreement'/('05_ocr_accuracy_vs_'+args.reference)
    report_names=['accuracy_summary','selected_indicator_summary','all_field_accuracy',
                  'categorical_accuracy_kappa','date_accuracy','numeric_accuracy','age_date_sensitivity']
    combined={name:[] for name in report_names}
    models=[]
    for folder in sorted((args.data/'OCR').iterdir()):
        if not folder.is_dir() or folder.name == 'gpt_ocr': continue
        model='OCR_'+folder.name
        output=ROOT/'OUTPUTS/selected_agreement'/('04_accuracy_'+model+'_vs_'+args.reference)
        run(SimpleNamespace(data=args.data,reference=args.reference,candidate=model,matches=None,output=output))
        manifest=json.loads((output/'run_manifest.json').read_text())
        for name in report_names:
            with (output/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f))
            combined[name].extend(dict(ocr_experiment=model,**r) for r in rows)
        models.append(dict(model=model,eligible_fields=len(manifest['eligible_fields']),
                           matched_cards=manifest['matched_cards'],report_folder=str(output)))
    args.output.mkdir(parents=True,exist_ok=True)
    for name,rows in combined.items():
        write(args.output/(name+'.csv'),rows,['ocr_experiment','group_level','group_code'])
        for level in ('aggregate','district','facility'):
            write(args.output/(level+'_'+name+'.csv'),[r for r in rows if r['group_level']==level],['ocr_experiment','group_code'])
    write(args.output/'model_report_index.csv',models,['model','eligible_fields','matched_cards','report_folder'])
    # Independently reconcile every additive statistic at both grouping levels.
    for model in [r['model'] for r in models]:
        rows=[r for r in combined['accuracy_summary'] if r['ocr_experiment']==model]
        aggregate=next(r for r in rows if r['group_level']=='aggregate')
        for level in ('district','facility'):
            grouped=[r for r in rows if r['group_level']==level]
            for key in ('reference_populated','correct','errors','substitutions','omissions','matched_cards','matched_visits'):
                assert sum(int(r[key]) for r in grouped)==int(aggregate[key]),(model,level,key)
        assert int(aggregate['correct'])+int(aggregate['errors'])==int(aggregate['reference_populated'])
    (args.output/'README.md').write_text(
        f'# OCR agreement against {args.reference}\n\nAll five selected models use the same analyse_accuracy.py policy, restricted to the 14 comparison facilities and saved one-to-one card matches. Each CSV is available combined and separately at aggregate, district and facility levels. Rates pool reference-populated cells; do not average facility percentages. Kappa is categorical only and uses both-populated pairs. Date/numeric tolerances use valid paired values; reference-populated alternatives are also provided. Invalid and extreme recorded values are retained in exact agreement and flagged separately.\n\n'
        'Matched card/visit coverage and eligible shared fields differ between models. These are conditional agreement rates on the matched subset, not a strictly paired model ranking or end-to-end extraction performance. Birth date and visit age/date contribute to matching, so sensitivity reports are included. Full disagreements, excluded fields, largest errors and visit coverage are in the individual model report folders.\n',encoding='utf-8')
    print('COMBINED REPORT:',args.output)
    print('All model totals reconcile at district and facility levels.')
    from render_ocr_agreement_tables import main as render_tables
    render_tables(folder=args.output,reference=args.reference)

if __name__=='__main__':
    main()
