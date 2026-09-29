from pathlib import Path
import json
import numpy as np
import pandas as pd
P=Path(__file__).resolve().parents[1]
TRAJECTORIES={1:'Persistent built-up',2:'New persistent expansion',3:'Non-built background'}
ZONES={1:'Expansion Risk Control',2:'Built-up Greening Enhancement',3:'Urban Vegetation Maintenance',4:'Ecological Conservation',5:'Ecological Restoration Priority'}
COLORS={1:'#FFC48A',2:'#A369B0',3:'#547AC0',4:'#79CB9B',5:'#898988'}
PRIORITIES={1:'Review areas where new construction overlaps vegetation degradation. Limit additional vegetation loss and conduct field assessment.',2:'Investigate causes of greening decline in existing built-up areas and prioritize maintenance of existing green spaces.',3:'Maintain existing urban vegetation and monitor subsequent changes.',4:'Conserve stable or improving non-built ecological areas and continue monitoring.',5:'Investigate degradation drivers and restoration feasibility. This category does not automatically identify desert margins.'}
def table(name):return pd.read_csv(P/'data'/name)
def layers():return json.loads((P/'data/layers.json').read_text())
def grid(key):
 with np.load(P/'data'/f'{key}.npz') as f:return {k:f[k].copy() for k in f.files}
def diagnose(trajectory,response):
 rules=json.loads((P/'data/rules.json').read_text())
 matches=[r for r in rules if r['trajectory']==trajectory and r['response']==response]
 if len(matches)!=1:raise ValueError('No formal governance rule for this selection')
 zone=matches[0]['zone']
 return zone,ZONES[zone],PRIORITIES[zone]
