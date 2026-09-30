from pathlib import Path
import subprocess, sys, json
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'research/synthetic_witness_smoke.xml'
cmd=[sys.executable,str(ROOT/'import/adapters/txt_to_tei.py'),str(ROOT/'import/examples/SYNTH1.txt'),str(out),'SYNTH1','Synthetic ingestion witness']
r=subprocess.run(cmd,capture_output=True,text=True)
report={'adapter_exit':r.returncode,'stderr':r.stderr,'output':str(out.relative_to(ROOT))}
if r.returncode==0:
    try:
        t=etree.parse(str(out)); report['well_formed']=True; report['paragraphs']=len(t.xpath('//*[local-name()="p"]'))
    except Exception as e: report['well_formed']=False; report['error']=str(e)
else: report['well_formed']=False
(ROOT/'research/ingestion_smoke_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report.get('well_formed') else 1)
