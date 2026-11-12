"""One-to-one card matching within coded district/facility groups.

python CODE/ANALYSIS/Replicable/match_cards.py
python CODE/ANALYSIS/Replicable/match_cards.py --left OCR_qwen --right Human_1
python CODE/ANALYSIS/Replicable/match_cards.py --left OCR_qwen --right Human_2

Reads DATA_ANN only. Coded manual decisions are in card_match_overrides.json.
No source rows/cards are edited or deduplicated. Ambiguity is never resolved by
row order. Matching uses identifiers and birth dates, not visit measurements.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from ocr_experiment_facilities import OCR_EXPERIMENT_FACILITIES, FACILITY_DISTRICT_CODES

ROOT=Path(__file__).resolve().parents[3]

def clean(v):
    s=str(v or '').strip()
    return '' if s.lower() in {'na','n/a','none','null','nan'} else s

def uid(v):
    return re.sub('[^A-Z0-9]','',clean(v).upper())

def hcc(v):
    s=re.sub(r'(?<=\d)\.0+$','',clean(v).upper())
    s=re.sub(r'^F\d+_','',s)
    s=re.sub(r'^AREA18[_ /-]*|^AREA[_ /-]*','',s)
    s=re.sub(r'^[A-Z]+[ /_]*(?=\d)','',s)
    s=re.sub('[^A-Z0-9]','',s)
    return s.lstrip('0') or ('0' if s else '')

def suffix(v):
    s=re.sub(r'(?<=\d)\.0+$','',clean(v))
    m=re.search(r'(\d+)$',s)
    return m.group(1).lstrip('0') or '0' if m else ''

def birth(v):
    s=clean(v)
    if not s: return ''
    for fmt in ('%Y-%m-%d','%d/%m/%Y','%d/%m/%y','%d-%m-%Y','%d-%m-%y','%Y/%m/%d'):
        try: return datetime.strptime(s,fmt).date().isoformat()
        except ValueError: pass
    return ''

def write(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def load(data,name):
    if name=='Human_1': paths=[data/'Human_1/visits.csv']; domain='H1'
    elif name=='Human_2': paths=sorted((data/'Human_2').glob('F*/*.csv')); domain='H2'
    elif name.startswith('OCR_'): paths=[data/'OCR'/name[4:]/'visits.csv']; domain='OCR'
    else: raise ValueError('Use Human_1, Human_2 or OCR_<model_folder>')
    if not paths: raise ValueError(f'No source files for {name}')
    cards={}
    for path in paths:
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if not {'source_card_id','district_code','facility_code','hcc_reg_no','unique_child_id','birth_date'}<=set(reader.fieldnames or []):
                raise ValueError(f'Missing required columns: {path}')
            rows=list(reader)
        if not rows and domain=='H2':
            match_id=re.search(r'F\d+_H2_\d+',path.stem)
            if not match_id: raise ValueError(f'Cannot identify empty card: {path}')
            rows=[dict(source_card_id=match_id.group(),facility_code=path.parent.name,
                       district_code=FACILITY_DISTRICT_CODES[path.parent.name],_empty=True)]
        for r in rows:
            card=r['source_card_id']; facility=r['facility_code']; district=r['district_code']
            if facility not in FACILITY_DISTRICT_CODES or FACILITY_DISTRICT_CODES[facility]!=district:
                raise ValueError(f'Invalid district/facility in {path}')
            if not card.startswith(facility+'_'): raise ValueError(f'Invalid card ID: {card}')
            item=cards.setdefault(card,dict(id=card,facility=facility,district=district,rows=[],source=path))
            if (item['facility'],item['district'],item['source'])!=(facility,district,path):
                raise ValueError(f'Card ID reused: {card}')
            if not r.get('_empty'): item['rows'].append(r)
    for item in cards.values():
        rr=item['rows']
        item['hccs']={hcc(r.get('hcc_reg_no')) for r in rr}-{''}
        item['uids']={uid(r.get('unique_child_id')) for r in rr}-{''}
        item['births']={birth(r.get('birth_date')) for r in rr}-{''}
        item['suffixes']={suffix(r.get('hcc_reg_no')) for r in rr}-{''}
        item['inconsistent']=any(len(item[k])>1 for k in ('hccs','uids','births'))
    return cards,domain,paths

def keys(card):
    if card['inconsistent']: return set()
    return {('hcc',v) for v in card['hccs'] | card.get('filename_hccs',set())} | {('uid',v) for v in card['uids'] | card.get('filename_uids',set())}

def candidate_graph(left,right):
    graph={}
    for a,x in left.items():
        graph[a]={b for b,y in right.items() if
                  (x['district'],x['facility'])==(y['district'],y['facility']) and keys(x)&keys(y)}
    return graph

def reciprocal_unique(graph):
    reverse=defaultdict(set)
    for a,bs in graph.items():
        for b in bs: reverse[b].add(a)
    return [(a,next(iter(bs))) for a,bs in graph.items() if len(bs)==1 and len(reverse[next(iter(bs))])==1]

def match(left,right,manual=()):
    pairs=[]; remaining_l=dict(left); remaining_r=dict(right)
    def assign(a,b,method):
        if a not in remaining_l or b not in remaining_r: raise ValueError('Nonunique manual/card assignment')
        x,y=remaining_l[a],remaining_r[b]
        if (x['district'],x['facility'])!=(y['district'],y['facility']): raise ValueError('Cross-group assignment prohibited')
        pairs.append((a,b,method)); del remaining_l[a]; del remaining_r[b]
    for a,b in manual: assign(a,b,'user_confirmed')
    graph=candidate_graph(remaining_l,remaining_r)
    for a,b in reciprocal_unique(graph): assign(a,b,'unique_identifier')
    graph=candidate_graph(remaining_l,remaining_r)
    # Use DOB to disambiguate repeated identifiers; identical duplicate cards stay ambiguous.
    graph={a:{b for b in bs if remaining_l[a]['births'] & remaining_r[b]['births']} for a,bs in graph.items()}
    for a,b in reciprocal_unique(graph): assign(a,b,'identifier_and_birth_date')
    graph={a:{b for b,y in remaining_r.items() if
        not x['inconsistent'] and not y['inconsistent'] and
        (x['district'],x['facility'])==(y['district'],y['facility']) and
        x['suffixes']&y['suffixes'] and x['births']&y['births']}
        for a,x in remaining_l.items()}
    for a,b in reciprocal_unique(graph): assign(a,b,'hcc_suffix_and_birth_date')
    final_graph=candidate_graph(remaining_l,remaining_r)
    for a,x in remaining_l.items():
        final_graph[a].update(b for b,y in remaining_r.items() if
            not x['inconsistent'] and not y['inconsistent'] and
            (x['district'],x['facility'])==(y['district'],y['facility']) and
            x['suffixes']&y['suffixes'] and x['births']&y['births'])
    return pairs,remaining_l,remaining_r,final_graph

def run(args):
    left,ld,lp=load(args.data,args.left); right,rd,rp=load(args.data,args.right)
    with args.hints.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            for cards in (left,right):
                if row['source_card_id'] in cards:
                    item=cards[row['source_card_id']]
                    if item['facility']!=row['facility_code']: raise ValueError('Filename evidence crosses facility')
                    item['filename_hccs']={row['filename_hcc_key']}-{''}
                    item['filename_uids']={row['filename_uid_key']}-{''}
    if args.left==args.right: raise ValueError('Choose two different datasets')
    decisions=json.loads(args.overrides.read_text())
    exclusions=[]
    for side,domain,cards in [('left',ld,left),('right',rd,right)]:
        for r in decisions['exclusions']:
            if r['domain']==domain and r['source_card_id'] in cards:
                item=cards.pop(r['source_card_id'])
                exclusions.append(dict(side=side,source_card_id=item['id'],district_code=item['district'],facility_code=item['facility'],reason=r['reason']))
    allowed=set(OCR_EXPERIMENT_FACILITIES)
    left={k:v for k,v in left.items() if v['facility'] in allowed}
    right={k:v for k,v in right.items() if v['facility'] in allowed}
    manual=[]; decision_audit=[]
    for r in decisions['matches']:
        if (r['left_domain'],r['right_domain'])==(ld,rd): a,b=r['left_card_id'],r['right_card_id']
        elif (r['right_domain'],r['left_domain'])==(ld,rd): a,b=r['right_card_id'],r['left_card_id']
        else: continue
        applied=a in left and b in right
        decision_audit.append(dict(left_card_id=a,right_card_id=b,status='applied' if applied else 'source_card_not_present'))
        if applied: manual.append((a,b))
    pairs,ul,ur,graph=match(left,right,manual)
    pair_rows=[]
    for a,b,method in pairs:
        x,y=left[a],right[b]
        pair_rows.append(dict(district_code=x['district'],facility_code=x['facility'],left_card_id=a,right_card_id=b,
            match_method=method,left_hcc=' | '.join(sorted(x['hccs'])),right_hcc=' | '.join(sorted(y['hccs'])),
            left_birth_date=' | '.join(sorted(x['births'])),right_birth_date=' | '.join(sorted(y['births']))))
    unresolved=[]
    for side,cards in [('left',ul),('right',ur)]:
        for card,x in cards.items():
            candidates=graph[card] if side=='left' else {a for a,bs in graph.items() if card in bs}
            unresolved.append(dict(side=side,district_code=x['district'],facility_code=x['facility'],source_card_id=card,
                status='inconsistent_identifiers_or_birth_date' if x['inconsistent'] else 'ambiguous_candidates' if candidates else 'no_candidate',
                candidate_card_ids=' | '.join(sorted(candidates)),hcc=' | '.join(sorted(x['hccs'])),
                unique_child_id=' | '.join(sorted(x['uids'])),birth_date=' | '.join(sorted(x['births']))))
    summary=[]
    for f in OCR_EXPERIMENT_FACILITIES:
        l=sum(c['facility']==f for c in left.values()); r=sum(c['facility']==f for c in right.values())
        n=sum(x['facility_code']==f for x in pair_rows)
        summary.append(dict(district_code=FACILITY_DISTRICT_CODES[f],facility_code=f,left_dataset=args.left,right_dataset=args.right,
            left_cards=l,right_cards=r,matched_pairs=n,left_unmatched=l-n,right_unmatched=r-n,
            left_match_rate=n/l if l else '',right_match_rate=n/r if r else ''))
    district=[]
    for d in sorted(set(FACILITY_DISTRICT_CODES[f] for f in allowed)):
        rr=[r for r in summary if r['district_code']==d]
        district.append(dict(district_code=d,left_dataset=args.left,right_dataset=args.right,
            **{k:sum(r[k] for r in rr) for k in ['left_cards','right_cards','matched_pairs','left_unmatched','right_unmatched']}))
    output=args.output or ROOT/'OUTPUTS/selected_agreement'/('03_card_matches_'+args.left+'_vs_'+args.right)
    output.mkdir(parents=True,exist_ok=True)
    write(output/'facility_matches.csv',summary,list(summary[0]))
    write(output/'district_matches.csv',district,list(district[0]))
    write(output/'matched_card_pairs.csv',pair_rows,['district_code','facility_code','left_card_id','right_card_id','match_method','left_hcc','right_hcc','left_birth_date','right_birth_date'])
    write(output/'unmatched_cards.csv',unresolved,['side','district_code','facility_code','source_card_id','status','candidate_card_ids','hcc','unique_child_id','birth_date'])
    write(output/'excluded_cards.csv',exclusions,['side','source_card_id','district_code','facility_code','reason'])
    write(output/'manual_match_audit.csv',decision_audit,['left_card_id','right_card_id','status'])
    assert len(pairs)+len(ul)==len(left) and len(pairs)+len(ur)==len(right)
    assert len({a for a,b,m in pairs})==len(pairs)==len({b for a,b,m in pairs})
    totals={k:sum(r[k] for r in summary) for k in ['left_cards','right_cards','matched_pairs','left_unmatched','right_unmatched']}
    (output/'run_manifest.json').write_text(json.dumps(dict(left=args.left,right=args.right,totals=totals,
        OCR_EXPERIMENT_FACILITIES=OCR_EXPERIMENT_FACILITIES,
        method='Manual, reciprocal unique HCC/UID (columns and coded filename evidence), identifier plus DOB, HCC suffix plus DOB. No matching across district/facility. Ambiguous ties remain unresolved.',
        inputs=[dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in lp+rp],
        overrides_sha256=hashlib.sha256(args.overrides.read_bytes()).hexdigest(),
        filename_hints_sha256=hashlib.sha256(args.hints.read_bytes()).hexdigest()),indent=2),encoding='utf-8')
    for row in summary: print(row)
    print('TOTAL',totals)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,default=ROOT/'DATA_ANN')
    p.add_argument('--left',default='Human_1')
    p.add_argument('--right',default='Human_2')
    p.add_argument('--overrides',type=Path,default=Path(__file__).with_name('card_match_overrides.json'))
    p.add_argument('--hints',type=Path,default=Path(__file__).with_name('card_filename_identifiers.csv'))
    p.add_argument('--output',type=Path)
    run(p.parse_args())
