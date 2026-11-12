"""Create plain Markdown tables from the combined OCR/Human 1 CSV reports."""
import csv
from pathlib import Path
from analyse_accuracy import ROOT

MODELS=[('OCR_gpt4o_mini','4o-mini'),('OCR_gpt41_mini','4.1-mini'),
        ('OCR_gpt56_terra','5.6-terra'),('OCR_nemotron','Nemotron'),('OCR_qwen','Qwen')]
LABELS={'wasting_malnutrition':'Wasting/malnutrition','breastfeeding':'Breastfeeding','mother_status':'Mother status',
        'abdominal_exam':'Clinical monitoring','hiv_testing':'HIV testing','hiv_infection':'HIV infection','follow_up':'Follow-up',
        'birth_date':'Birth date','visit_date':'Visit date','next_appointment_date':'Next appointment',
        'weight_kg':'Weight (kg)','height_cm':'Height (cm)','birth_weight_kg':'Birth weight (kg)',
        'age_months':'Age (months)','cpt':'CPT (recorded units)'}

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(v) for v in row)+' |' for row in rows])

def pct(value): return f'{100*float(value):.2f}%' if value not in ('',None) else '—'
def num(value):
    if value in ('',None): return '—'
    number=float(value)
    return f'{0.0 if abs(number)<0.0005 else number:.3f}'

def main(folder=None,reference='Human_1'):
    folder=folder or ROOT/'OUTPUTS/hcc_pseudonymised_agreement/05_ocr_accuracy_vs_Human_1'
    def read(name):
        with (folder/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
    summary=read('accuracy_summary')
    def get(rows,model,field=None,level='aggregate',code='ALL'):
        return next(r for r in rows if r['ocr_experiment']==model and r['group_level']==level and r['group_code']==code and (field is None or r['field']==field))
    text=[f'OCR agreement against {reference.replace("_"," ")}. Accuracy uses populated reference values; missing OCR entries count as errors. Kappa uses both-populated categorical pairs. Different matched subsets prevent a strictly paired model ranking.\n']
    rows=[]
    for model,label in MODELS:
        r=get(summary,model)
        rows.append([label,r['matched_cards'],r['matched_visits'],r['reference_populated'],r['correct'],r['substitutions'],r['omissions'],pct(r['accuracy']),pct(r['disagreement_rate'])])
    text+=['Aggregate results\n',table(['OCR','Cards','Visits','Reference cells','Correct','Different','Missing OCR','Accuracy','Disagreement'],rows)]
    categorical=read('categorical_accuracy_kappa')
    fields=['wasting_malnutrition','breastfeeding','mother_status','abdominal_exam','hiv_testing','hiv_infection','follow_up']
    rows=[]
    for field in fields:
        row=[LABELS[field]]
        for model,label in MODELS:
            r=get(categorical,model,field)
            row.append(pct(r['accuracy'])+' / '+num(r['kappa']))
        rows.append(row)
    text+=['Categorical results: accuracy / kappa\n',table(['Indicator']+[label for _,label in MODELS],rows)]
    dates=read('date_accuracy'); rows=[]
    for field in ['birth_date','visit_date','next_appointment_date']:
        for model,label in MODELS:
            r=get(dates,model,field)
            rows.append([LABELS[field],label,pct(r['accuracy']),r['valid_pairs'],num(r['mean_absolute_error']),num(r['median_absolute_error'])]+[pct(r[f'within_{t}_valid_pair_rate']) for t in (1,7,14)])
    text+=['Dates: absolute errors in days; tolerance percentages use valid pairs\n',table(['Field','OCR','Exact accuracy','Valid pairs','Mean error','Median error','±1 day','±7 days','±14 days'],rows)]
    numeric=read('numeric_accuracy'); rows=[]
    for field in ['weight_kg','height_cm','birth_weight_kg','age_months','cpt']:
        t='0.1' if field in ('weight_kg','birth_weight_kg') else '1'
        for model,label in MODELS:
            r=get(numeric,model,field)
            rows.append([LABELS[field],label,pct(r['accuracy']),r['valid_pairs'],num(r['mean_absolute_error']),num(r['median_absolute_error']),('±'+t) if field!='cpt' else '—',pct(r.get(f'within_{t}_valid_pair_rate')) if field!='cpt' else '—'])
    text+=['Numerical results: errors in the indicated units; tolerances use valid pairs\n',table(['Field','OCR','Exact accuracy','Valid pairs','Mean error','Median error','Tolerance','Within tolerance'],rows)]
    for level in ['district','facility']:
        codes=sorted({r['group_code'] for r in summary if r['group_level']==level},key=lambda x:int(x[1:]))
        rows=[[code]+[pct(get(summary,model,level=level,code=code)['accuracy']) for model,_ in MODELS] for code in codes]
        text += [level.capitalize()+' accuracy\n',table([level.capitalize()]+[label for _,label in MODELS],rows)]
    text+=['Unmatched cards and visits do not enter cell accuracy. Age and visit date help pair visits; see age_date_sensitivity.csv for independent pairing checks. Extreme and invalid values are retained in exact agreement; error magnitudes exclude invalid pairs. All detailed district/facility indicator results are supplied in the CSV reports.\n']
    (folder/'agreement_tables.md').write_text('\n\n'.join(text),encoding='utf-8')
    print(folder/'agreement_tables.md')

if __name__=='__main__':
    main()
