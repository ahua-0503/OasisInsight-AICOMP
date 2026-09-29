from pathlib import Path
import sys,json
P=Path(__file__).parent;sys.path.insert(0,str(P))
from streamlit.testing.v1 import AppTest
from utils.data import diagnose,table,TRAJECTORIES
expected={1:[2,3,3],2:[1,3,3],3:[5,4,4]}
for u in expected:
 for response,zone in zip(['Degraded','Stable','Improved'],expected[u]):assert diagnose(u,response)[0]==zone
stats=table('trajectory_stats.csv')
for u in [1,2,3]:
 r=stats[stats.code==u].iloc[0];assert abs(r.decrease_pct+r.stable_pct+r.increase_pct-100)<1e-9
at=AppTest.from_file(str(P/'app.py'),default_timeout=60).run()
assert not at.exception,at.exception
checks=[]
for key in ['Built-up','NDVI','Nighttime Light','DEM']:
 at.selectbox[0].set_value(key).run();assert not at.exception;checks.append('Layer '+key)
for u in [1,2,3]:
 at.selectbox(key='trajectory').set_value(TRAJECTORIES[u]).run();assert not at.exception;checks.append('Trajectory '+str(u))
for u in [1,2,3]:
 for response in ['Degraded','Stable','Improved']:
  at.selectbox(key='governance_trajectory').set_value(TRAJECTORIES[u])
  next(x for x in at.selectbox if x.label=='Vegetation response').set_value(response)
  at.run();assert not at.exception
  assert at.success[0].value==diagnose(u,response)[1];checks.append(f'Rule {u}/{response}')
for model in table('benchmark.csv').Model:
 next(x for x in at.selectbox if x.label=='Benchmark model').set_value(model).run();assert not at.exception;checks.append(model)
for strategy in table('validation.csv').Validation.unique():
 next(x for x in at.selectbox if x.label=='Validation strategy').set_value(strategy).run();assert not at.exception;checks.append(strategy)
(P/'test_results.json').write_text(json.dumps(dict(status='passed',checks=checks),indent=2))
print('App tests passed:',len(checks))
