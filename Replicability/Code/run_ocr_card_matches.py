"""Run every coded OCR model against Human 1 and Human 2 with match_cards.py."""
import csv
import json
import subprocess
import sys
from pathlib import Path
from match_cards import ROOT, write

def main():
    totals=[]
    for folder in sorted((ROOT/'DATA_ANN_HCC_PSEUDONYMISED/OCR').iterdir()):
        if not folder.is_dir() or folder.name == 'gpt_ocr': continue
        model='OCR_'+folder.name
        for reference in ('Human_1','Human_2'):
            subprocess.run([sys.executable,str(Path(__file__).with_name('match_cards.py')),
                            '--left',model,'--right',reference],check=True)
            output=ROOT/'OUTPUTS/hcc_pseudonymised_agreement'/('03_card_matches_'+model+'_vs_'+reference)
            result=json.loads((output/'run_manifest.json').read_text())
            totals.append(dict(ocr_dataset=model,human_dataset=reference,**result['totals']))
    output=ROOT/'OUTPUTS/hcc_pseudonymised_agreement/03_ocr_card_matches'
    output.mkdir(parents=True,exist_ok=True)
    write(output/'all_comparison_totals.csv',totals,list(totals[0]))

if __name__=='__main__':
    main()
