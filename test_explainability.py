from pathlib import Path
import sys,json
p=Path(__file__).resolve().parent
sys.path.insert(0,str(p))
from streamlit.testing.v1 import AppTest
from utils.data import table
at=AppTest.from_file(str(p/'app.py'),default_timeout=60).run()
results=[]
for label,field in [('NDVIbase','NDVIbase'),('Slope','Slope'),('DEM','DEM'),('Temperature','TEMmean')]:
 next(x for x in at.selectbox if x.label=='Feature Response').set_value(label).run()
 assert not at.exception,at.exception
 d=table('feature_response.csv');d=d[d.feature==field]
 assert len(d)==20 and d[['x_mean','shap_mean','n']].notna().all().all()
 results.append({'selection':label,'source_field':field,'bins':len(d),'status':'passed'})
(p/'explainability_checks.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('Four feature selections passed; each has 20 saved bins.')
