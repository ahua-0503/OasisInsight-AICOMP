"""Reproducible basic analysis; no trained model or area estimates."""
import numpy as np
import pandas as pd

def analyze(frame,start,end,cutpoints=None):
    endpoints=frame[[f'NDVI_{start}',f'NDVI_{end}']].apply(pd.to_numeric,errors='coerce')
    if not np.isfinite(endpoints.to_numpy()).all() or not endpoints.ge(-1).all().all() or not endpoints.le(1).all().all():
        raise ValueError('Endpoint NDVI must be finite, unscaled values in [-1, 1]; missing values cannot be classified.')
    confirmation=pd.to_numeric(frame[f'Built_{end+1}'],errors='coerce') if f'Built_{end+1}' in frame else pd.Series(np.nan,index=frame.index)
    b=frame[[f'Built_{y}' for y in range(start,end+1)]].to_numpy(dtype=float)
    if not np.isin(b,[0,1]).all(): raise ValueError('Built sequence must contain only 0/1.')
    labels=[]; onsets=[]
    for i,row in enumerate(b):
        onset=None
        if (row==1).all(): label='Persistent built-up'
        elif (row==0).all(): label='Non-built background'
        elif row[0]==0:
            first=int(np.flatnonzero(row)[0])
            if (row[first:]==1).all():
                onset=start+first
                if first<len(row)-1: label='New persistent expansion'
                elif confirmation.iloc[i]==1: label='New persistent expansion'
                else: label='Unconfirmed terminal expansion'
            else: label='Intermittent / uncertain'
        else: label='Intermittent / uncertain'
        labels.append(label); onsets.append(onset)
    result=frame[['ID','X','Y']].copy()
    result['Trajectory']=labels
    result['Expansion_onset']=pd.array(onsets,dtype='Int64')
    result['NDVIbase']=pd.to_numeric(frame[f'NDVI_{start}'])
    result['dNDVI']=pd.to_numeric(frame[f'NDVI_{end}'])-result.NDVIbase
    if cutpoints is None:
        result['Response']=np.select([result.dNDVI<0,result.dNDVI>0],['Decrease','Increase'],default='No change')
        method='Auto: endpoint change sign; zero means exactly unchanged. No ecological significance threshold is inferred.'
    else:
        c=np.asarray(cutpoints,dtype=float)
        if len(c)!=4 or not np.isfinite(c).all() or not (np.diff(c)>0).all(): raise ValueError('Four increasing finite cutpoints required.')
        result['Response']=['G'+str(v+1) for v in np.searchsorted(c,result.dNDVI,side='right')]
        method='Custom five bins: left-inclusive intervals; exact cutpoint enters the higher bin. Ecological labels are not inferred.'
    summary=result.groupby(['Trajectory','Response'],observed=True).size().rename('Count').reset_index()
    summary['Within_trajectory_pct']=summary.Count/summary.groupby('Trajectory').Count.transform('sum')*100
    return result,summary,method
