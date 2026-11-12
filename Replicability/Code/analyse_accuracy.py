"""Reference-based field agreement on DATA_ANN_HCC_PSEUDONYMISED matched cards; standard library only.

python CODE/ANALYSIS/Replicable/analyse_accuracy.py
python CODE/ANALYSIS/Replicable/analyse_accuracy.py --reference Human_1 --candidate OCR_qwen

Run match_cards.py for the two datasets first; either saved orientation is accepted.
Kappa is limited to seven categorical indicators. No inference of ground truth.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter,defaultdict
from datetime import date,datetime
from decimal import Decimal,InvalidOperation
from pathlib import Path
from statistics import median
from match_cards import ROOT,load,hcc,uid
from ocr_experiment_facilities import OCR_EXPERIMENT_FACILITIES,FACILITY_DISTRICT_CODES

ALIASES={'age_at_visit_months':'age_months','breastfeeding_type':'breastfeeding','age_at_enrolment_days':'age_at_enrolment'}
VISIT=set('age_months visit_date height_cm weight_kg muac_cm wasting_malnutrition breastfeeding stopped_lt6m stopped_ge6m mother_status abdominal_exam hiv_testing hiv_infection cpt follow_up next_appointment_date'.split())
META={'hcc_match_suffix'} | set('district facility facility_type facilitiy_location file_name folder_name pdf_file_name district_code facility_code source_card_id file_path comparison_site'.split())
EXPLICIT={'agrees_to_fup','agreed_to_fup'}|{f'hiv_test_3_{s}' for s in ('sample_date','type','sample_id','result','date_received')}
NUMERIC=set('birth_cohort_year birth_weight_kg age_months height_cm weight_kg muac_cm child_age age_at_enrolment cpt stopped_lt6m stopped_ge6m'.split())
CATEGORICAL=set('wasting_malnutrition breastfeeding mother_status abdominal_exam hiv_testing hiv_infection follow_up'.split())
SELECTED={'birth_date','weight_kg','height_cm','birth_weight_kg','cpt','age_months','visit_date','next_appointment_date'}|CATEGORICAL
TOLERANCES={'weight_kg':0.1,'birth_weight_kg':0.1,'height_cm':1,'age_months':1}

def clean(v):
    text=('' if v is None else str(v)).strip()
    return '' if text.casefold() in {'na','n/a','none','null','nan'} else text

def norm(field,value):
    s=clean(value)
    if not s: return ''
    if field in CATEGORICAL:
        # Match the earlier OCR convention for formatting-only code variants.
        # Do not infer clinical synonyms or choose among multiple labels.
        return re.sub(r'[^a-z0-9]+','',s.casefold())
    if field in {'age_at_enrolment','nvp_duration'}:
        t=re.sub(r'\s+','',s.casefold())
        if re.fullmatch(r'\d+(?:\.0+)?',t):
            n=str(int(Decimal(t))); return {'1':'1 day','6':'6 weeks'}.get(n,n)
        m=re.fullmatch(r'(\d+)(days?|d|weeks?|wks?|w)',t)
        rev=re.fullmatch(r'(days?|d|weeks?|wks?|w)(\d+)',t)
        if m or rev:
            n,unit=m.groups() if m else tuple(reversed(rev.groups()))
            return str(int(n))+' '+('day' if unit.startswith('d') else 'weeks')
    if field=='hcc_reg_no': return hcc(s)
    if field in {'unique_child_id','art_reg_no','guardian_phone'} or 'sample_id' in field: return uid(s)
    if 'date' in field:
        for fmt in ('%Y-%m-%d','%d/%m/%Y','%d/%m/%y','%d-%m-%Y','%d-%m-%y','%Y/%m/%d'):
            try: return datetime.strptime(s,fmt).date().isoformat()
            except ValueError: pass
    if field in NUMERIC:
        try:
            n=Decimal(s)
            if n.is_finite(): return str(n.normalize())
        except InvalidOperation: pass
    return re.sub(r'\s+',' ',s).casefold()

def kappa(pairs):
    n=sum(pairs.values())
    if not n: return dict(kappa='',kappa_n=0,kappa_observed_agreement='',kappa_status='no_pairs')
    a,b=Counter(),Counter(); same=0
    for (x,y),count in pairs.items():
        a[x]+=count; b[y]+=count
        if x==y: same+=count
    observed=same/n; expected=sum(a[x]*b[x] for x in a)/n**2
    return dict(kappa=(observed-expected)/(1-expected) if expected<1 else '',kappa_n=n,
                kappa_observed_agreement=observed,kappa_status='calculated' if expected<1 else 'undefined_single_category')

def difference(field,a,b):
    if not a or not b: return ''
    try:
        if 'date' in field: return (date.fromisoformat(b)-date.fromisoformat(a)).days
        if field in NUMERIC:
            x,y=Decimal(a),Decimal(b)
            if x.is_finite() and y.is_finite(): return float(y-x)
    except (ValueError,InvalidOperation): pass
    return ''

def pair_visits(a,b,stages):
    left=set(range(len(a))); right=set(range(len(b))); pairs=[]
    for fields in stages:
        lg,rg=defaultdict(list),defaultdict(list)
        for indices,rows,groups in [(left,a,lg),(right,b,rg)]:
            for i in sorted(indices):
                key=tuple(norm(f,rows[i].get(f,'')) for f in fields)
                if all(key): groups[key].append(i)
        for key in sorted(lg.keys()&rg.keys()):
            if len(lg[key])==len(rg[key])==1:
                i,j=lg[key][0],rg[key][0]
                pairs.append((i,j,'+'.join(fields))); left.remove(i); right.remove(j)
    return pairs,left,right

def metrics(rows):
    counts=Counter(r['status'] for r in rows)
    n=counts['agree']+counts['different']+counts['candidate_missing']
    return dict(compared_cells=len(rows),reference_populated=n,correct=counts['agree'],
        substitutions=counts['different'],omissions=counts['candidate_missing'],
        errors=counts['different']+counts['candidate_missing'],
        candidate_only_values=counts['reference_missing'],both_missing=counts['both_missing'],
        accuracy=counts['agree']/n if n else '',disagreement_rate=(n-counts['agree'])/n if n else '')

def field_metrics(rows,field):
    result=metrics(rows)
    complete=[r for r in rows if r['reference_normalized'] and r['candidate_normalized']]
    if field in CATEGORICAL:
        result.update(kappa(Counter((r['reference_normalized'],r['candidate_normalized']) for r in complete)))
        union=[r for r in rows if r['reference_normalized'] or r['candidate_normalized']]
        alt=kappa(Counter((r['reference_normalized'],r['candidate_normalized']) for r in union))
        result.update(kappa_missing_as_category=alt['kappa'],kappa_missing_as_category_n=alt['kappa_n'])
    else:
        gaps=[abs(r['signed_difference']) for r in complete if r['signed_difference']!='']
        result.update(valid_pairs=len(gaps),both_populated_invalid_pairs=len(complete)-len(gaps),
            mean_absolute_error=sum(gaps)/len(gaps) if gaps else '',median_absolute_error=median(gaps) if gaps else '')
        tolerances=[1,7,14] if 'date' in field else [TOLERANCES[field]] if field in TOLERANCES else []
        for t in tolerances:
            count=sum(d<=t for d in gaps)
            result[f'within_{t:g}_valid_pair_rate']=count/len(gaps) if gaps else ''
            result[f'within_{t:g}_reference_populated_rate']=count/result['reference_populated'] if result['reference_populated'] else ''
    return result

def write(path,rows,default):
    fields=list(dict.fromkeys(k for r in rows for k in r)) or default
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def run(args):
    ref,_,rp=load(args.data,args.reference); cand,_,cp=load(args.data,args.candidate)
    for cards in (ref,cand):
        for card in cards.values():
            card['rows']=[{ALIASES.get(k,k):v for k,v in r.items()} for r in card['rows']]
    rf={k for c in ref.values() for r in c['rows'] for k in r}-META
    cf={k for c in cand.values() for r in c['rows'] for k in r}-META
    empty={f for f in rf if all(not clean(r.get(f,'')) for c in ref.values() for r in c['rows'])}
    excluded=empty|EXPLICIT|{f for f in rf|cf if 'path' in f or f.startswith('source_')}
    fields=sorted((rf&cf)-excluded)
    matchdir=args.matches or ROOT/'OUTPUTS/hcc_pseudonymised_agreement'/('03_card_matches_'+args.reference+'_vs_'+args.candidate)
    if not matchdir.exists() and not args.matches:
        matchdir=ROOT/'OUTPUTS/hcc_pseudonymised_agreement'/('03_card_matches_'+args.candidate+'_vs_'+args.reference)
    manifest=json.loads((matchdir/'run_manifest.json').read_text())
    orientation=(manifest['left'],manifest['right'])
    if orientation not in [(args.reference,args.candidate),(args.candidate,args.reference)]: raise ValueError('Matching datasets do not match requested reference/candidate')
    for item in manifest['inputs']:
        if hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError('Matched input has changed; rerun match_cards.py first')
    with (matchdir/'matched_card_pairs.csv').open(encoding='utf-8-sig',newline='') as f: pairs=list(csv.DictReader(f))
    if orientation==(args.candidate,args.reference):
        for pair in pairs:
            pair['left_card_id'],pair['right_card_id']=pair['right_card_id'],pair['left_card_id']
    records=[]; sensitivity=[]; coverage=[]; issues=[]
    for pair in pairs:
        a,b=ref[pair['left_card_id']],cand[pair['right_card_id']]
        if (a['district'],a['facility'])!=(b['district'],b['facility']): raise ValueError('Cross-group pair')
        context=dict(district_code=a['district'],facility_code=a['facility'],reference_card_id=a['id'],candidate_card_id=b['id'])
        def compare(field,av,bv,level,method,ri='',ci='',target=records):
            x,y=norm(field,av),norm(field,bv)
            status='both_missing' if not x and not y else 'reference_missing' if not x else 'candidate_missing' if not y else 'agree' if x==y else 'different'
            target.append(dict(**context,field=field,level=level,visit_match_method=method,reference_visit_index=ri,candidate_visit_index=ci,
                reference_value=av,candidate_value=bv,reference_normalized=x,candidate_normalized=y,
                status=status,signed_difference=difference(field,x,y)))
        for field in sorted(set(fields)-VISIT):
            values=[]
            for side,card in [('reference',a),('candidate',b)]:
                variants={norm(field,r.get(field,'')) for r in card['rows']}-{''}
                if len(variants)>1:
                    issues.append(dict(**context,issue='inconsistent_card_field',side=side,field=field,values=' | '.join(sorted(variants))))
                values.append(next((r.get(field,'') for r in card['rows'] if clean(r.get(field,''))),''))
            compare(field,*values,'card','card_once')
        vp,ul,ur=pair_visits(a['rows'],b['rows'],[('age_months','visit_date'),('visit_date',),('age_months',)])
        for i,j,method in vp:
            for field in sorted(set(fields)&VISIT):
                compare(field,a['rows'][i].get(field,''),b['rows'][j].get(field,''),'visit',method,i+1,j+1)
        coverage.append(dict(**context,reference_visits=len(a['rows']),candidate_visits=len(b['rows']),matched_visits=len(vp),reference_unmatched_visits=len(ul),candidate_unmatched_visits=len(ur)))
        for side,indices,card in [('reference',ul,a),('candidate',ur,b)]:
            for i in sorted(indices):
                issues.append(dict(**context,issue='unmatched_visit',side=side,visit_index=i+1,age_months=card['rows'][i].get('age_months',''),visit_date=card['rows'][i].get('visit_date','')))
        for field,stages,method in [('visit_date',[('age_months',)],'age_only'),('age_months',[('visit_date',)],'date_only')]:
            pp,_,_=pair_visits(a['rows'],b['rows'],stages)
            for i,j,_ in pp:
                compare(field,a['rows'][i].get(field,''),b['rows'][j].get(field,''),'visit',method,i+1,j+1,target=sensitivity)
    scopes=[('aggregate','ALL')]+[('district',d) for d in sorted({FACILITY_DISTRICT_CODES[f] for f in OCR_EXPERIMENT_FACILITIES})]+[('facility',f) for f in OCR_EXPERIMENT_FACILITIES]
    summary=[]; byfield=[]; selected=[]; sensitivities=[]
    for level,code in scopes:
        def inscope(r): return level=='aggregate' or r[level+'_code']==code
        rr=[r for r in records if inscope(r)]; cc=[r for r in coverage if inscope(r)]
        scope=dict(group_level=level,group_code=code)
        summary.append(dict(**scope,field_scope='all_eligible_fields',matched_cards=len(cc),matched_visits=sum(r['matched_visits'] for r in cc),reference_unmatched_visits=sum(r['reference_unmatched_visits'] for r in cc),candidate_unmatched_visits=sum(r['candidate_unmatched_visits'] for r in cc),**metrics(rr)))
        selected.append(dict(**scope,field_scope='15_requested_indicators',**metrics([r for r in rr if r['field'] in SELECTED])))
        for field in fields:
            fieldrows=[r for r in rr if r['field']==field]
            if field in SELECTED: stats=field_metrics(fieldrows,field)
            else: stats=metrics(fieldrows)
            byfield.append(dict(**scope,field=field,**stats))
        for field in ('visit_date','age_months'):
            sr=[r for r in sensitivity if inscope(r) and r['field']==field]
            sensitivities.append(dict(**scope,field=field,pairing='age_only' if field=='visit_date' else 'date_only',**field_metrics(sr,field)))
    out=args.output or ROOT/'OUTPUTS/hcc_pseudonymised_agreement'/('04_accuracy_'+args.candidate+'_vs_'+args.reference)
    out.mkdir(parents=True,exist_ok=True)
    for name,data in [('accuracy_summary',summary),('selected_indicator_summary',selected),('all_field_accuracy',byfield),
        ('categorical_accuracy_kappa',[r for r in byfield if r['field'] in CATEGORICAL]),
        ('date_accuracy',[r for r in byfield if r['field'] in {'birth_date','visit_date','next_appointment_date'}]),
        ('numeric_accuracy',[r for r in byfield if r['field'] in {'weight_kg','height_cm','birth_weight_kg','age_months','cpt'}]),
        ('age_date_sensitivity',sensitivities),('card_visit_coverage',coverage),('review_issues',issues),
        ('disagreements',[r for r in records if r['status'] not in {'agree','both_missing'}])]:
        write(out/(name+'.csv'),data,['field','status'])
    write(out/'excluded_fields.csv',[dict(field=f,reason='all_missing_in_full_reference' if f in empty else 'explicit_exclusion') for f in sorted(excluded)],['field','reason'])
    write(out/'paired_values.csv',records,['field','status'])
    largest=[]
    for field in sorted(SELECTED-CATEGORICAL):
        rr=[r for r in records if r['field']==field and r['signed_difference'] not in ('',0)]
        largest.extend(sorted(rr,key=lambda r:-abs(r['signed_difference']))[:20])
    write(out/'largest_absolute_errors.csv',largest,['field','signed_difference'])
    (out/'run_manifest.json').write_text(json.dumps(dict(reference=args.reference,candidate=args.candidate,
        eligible_fields=fields,excluded_fields=sorted(excluded),matched_cards=len(pairs),
        OCR_EXPERIMENT_FACILITIES=OCR_EXPERIMENT_FACILITIES,
        input_hashes=manifest['inputs'],matching_manifest_sha256=hashlib.sha256((matchdir/'run_manifest.json').read_bytes()).hexdigest()),indent=2),encoding='utf-8')
    (out/'README.md').write_text(
        '# Reference-based agreement\n\nHuman 1 is a comparison reference, not adjudicated truth. Accuracy = exact normalized matches / populated reference cells; candidate missing values count as errors. Values against reference blanks are reported separately. Both-missing values are excluded. Aggregate rates pool cells, not facility percentages. All eligible shared fields form the main summary; a separate summary restricts to the 15 requested indicators. Card fields count once using first populated values and inconsistent repetitions are flagged. Visit fields count per matched visit. Unmatched cards and visits are coverage gaps, excluded from the cell denominator.\n\n'
        'Facility/district membership and manual exclusions come from the saved card matches. All-missing reference fields are detected over the full reference before filtering. Agreement to follow-up and the fourth HIV test are excluded. NA and empty values are equivalent. Categorical codes ignore capitalization, spaces and punctuation (On ART equals OnART; N.A.D. equals NAD), matching the earlier OCR convention. Other text ignores case/extra whitespace; numeric values compare as decimals; HCC facility prefixes are removed; dates use ISO/day-first formats. Bare 1 and 6 in enrolment age/NVP duration mean 1 day and 6 weeks respectively. No clinical synonym recoding or multi-label interpretation is applied.\n\n'
        'Kappa is computed separately for the seven categorical indicators using both-populated pairs; the alternative treats one-sided missingness as a category. No pooled/numeric/date kappa. Date errors use valid calendar pairs and days; thresholds 1,7,14 days. Numeric tolerances: 0.1 kg weight/birth weight, 1 cm height, 1 month age. CPT is numeric recorded dosage units, with no inferred unit conversion. Tolerance rates are supplied for valid pairs and populated reference denominators. Invalid recorded numeric/date strings remain in exact agreement, but are excluded from error magnitudes and flagged by counts. Extreme values are retained; largest errors are listed.\n\n'
        'Visit matching uses unique age+date, date, then age, with no positional fallback. Age/date agreement is influenced by selection; independent age-only pairing for visit date and date-only pairing for age are reported separately. Some card matches use birth date, making birth agreement conditional on that selection. Clinical monitoring means abdominal_exam; mother status is visit-level mother_status. No confidence intervals are estimated for clustered visits.\n',encoding='utf-8')
    assert sum(r['reference_populated'] for r in summary if r['group_level']=='facility')==summary[0]['reference_populated']
    print('OVERALL',summary[0]); print('SELECTED',selected[0])
    print('FIELDS',len(fields),'MATCHED_CARDS',len(pairs))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,default=ROOT/'DATA_ANN_HCC_PSEUDONYMISED')
    p.add_argument('--reference',default='Human_1')
    p.add_argument('--candidate',default='Human_2')
    p.add_argument('--matches',type=Path)
    p.add_argument('--output',type=Path)
    run(p.parse_args())
