from pathlib import Path
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.data import P,TRAJECTORIES,ZONES,COLORS,table,layers,grid,diagnose
from utils.media import evidence_image

from utils.style import header,finding,footer,about
header()
metadata=layers();stats=table('trajectory_stats.csv');bench=table('benchmark.csv');validation=table('validation.csv');zone_stats=table('zone_stats.csv')
@st.cache_data
def cached_grid(key):return grid(key)
def base(fig,height=340):
 fig.update_layout(template='plotly_white',height=height,font=dict(family='Arial',size=13,color='#263c34'),margin=dict(l=25,r=25,t=20,b=25),paper_bgcolor='white',plot_bgcolor='white')
 return fig
def mapfig(key,selected=None):
 g=cached_grid(key);z=g['z'].copy();m=metadata[key];kind=m['kind']
 if selected is not None:z[z!=selected]=np.nan
 discrete={'trajectory':(['#898988','#FFC48A','#79CB9B','#A369B0','#DBE6F7','#E6E6E6'],['Persistent built-up','New expansion','Non-built','Uncertain','Missing annual','Missing confirmation']), 'governance':(list(COLORS.values()),list(ZONES.values()))}
 opts={};scale=None
 if kind in discrete:
  colors,names=discrete[kind];n=len(colors);scale=[]
  for i,c in enumerate(colors):scale.extend([(i/n,c),((i+1)/n,c)])
  opts=dict(zmin=.5,zmax=n+.5,colorbar=dict(tickvals=list(range(1,n+1)),ticktext=names,len=.7,thickness=10))
 elif kind=='binary':scale=[[0,'#E6E6E6'],[.5,'#E6E6E6'],[.5,'#547AC0'],[1,'#547AC0']];opts=dict(zmin=0,zmax=1,colorbar=dict(tickvals=[0,1],ticktext=['Non-built','Built-up'],thickness=10))
 elif kind=='ndvi':scale=[[0,'#E6E6E6'],[.4,'#DFF2E7'],[1,'#79CB9B']];opts=dict(zmin=-.2,zmax=.6,colorbar=dict(title='NDVI',thickness=10))
 elif kind=='ntl':scale=[[0,'#E6E6E6'],[.5,'#DBE6F7'],[1,'#547AC0']];opts=dict(colorbar=dict(title='NTL',thickness=10))
 else:scale=[[0,'#DFF2E7'],[.5,'#FFC48A'],[1,'#898988']];opts=dict(colorbar=dict(title='Elevation / m',thickness=10))
 isgeo=m['crs']=='EPSG:4326';factor=1 if isgeo else 1000
 fig=go.Figure(go.Heatmap(z=z,x=g['x']/factor,y=g['y']/factor,colorscale=scale,hoverongaps=False,hovertemplate='x: %{x:.3f}<br>y: %{y:.3f}<br>Value: %{z:.3f}<extra></extra>',**opts))
 if kind in discrete or kind=='binary':
  fig.update_traces(showscale=False)
  if kind=='binary':colors,names=['#E6E6E6','#547AC0'],['Non-built','Built-up']
  else:colors,names=discrete[kind]
  for i,(color,name) in enumerate(zip(colors,names),1):
   if selected is not None and i!=selected:continue
   fig.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(color=color,size=9,symbol='square'),name=name))
  fig.update_layout(legend=dict(orientation='h',y=-.26,font=dict(size=11)))
 base(fig,440);fig.update_layout(margin=dict(l=25,r=25,t=20,b=100));fig.update_xaxes(title='Longitude / °E' if isgeo else 'Easting / km',showgrid=False);fig.update_yaxes(title='Latitude / °N' if isgeo else 'Northing / km',showgrid=False,scaleanchor='x',scaleratio=float(1/np.cos(np.deg2rad(np.mean(g['y'])))) if isgeo else 1)
 if selected is not None:
  boundary=json.loads((P/'data/study_boundary_utm.json').read_text(encoding='utf-8'))
  for i,ring in enumerate(boundary['rings']):
   fig.add_trace(go.Scatter(x=ring['x'],y=ring['y'],mode='lines',line=dict(color='#898988',width=1.2),name='Study boundary',showlegend=i==0,hoverinfo='skip'))
  fig.add_trace(go.Heatmap(z=np.where(np.isfinite(g['z']),1,np.nan),x=g['x']/1000,y=g['y']/1000,colorscale=[[0,'#E6E6E6'],[1,'#E6E6E6']],opacity=.35,showscale=False,hoverinfo='skip'))
  fig.data=(fig.data[-1],)+fig.data[:-1]
  fig.update_layout(showlegend=True)
 return fig
tabs=st.tabs(['Overview','Trajectory Diagnosis','Trustworthy AI','Governance'])
with tabs[0]:
 st.subheader('Urban Expansion in a Dryland Oasis City')
 st.caption('Multi-source observations · Trajectory-aware ecological diagnosis')
 cards=st.columns(3)
 for col,(code,label) in zip(cards,TRAJECTORIES.items()):
  r=stats[stats.code==code].iloc[0];col.metric(label,f'{r.area_km2:,.1f} km²')
 left,right=st.columns([2.5,1])
 with right:
  st.markdown('### Data Layers')
  layer_name=st.selectbox('Data layer',['Built-up','NDVI','Nighttime Light','DEM'])
  layer=dict(zip(['Built-up','NDVI','Nighttime Light','DEM'],['built_2016','ndvi_2023','ntl_mean','dem']))[layer_name]
  st.caption(metadata[layer]['title']+' · '+metadata[layer]['period'])
  st.markdown('Explore the spatial context of urban growth and vegetation change.')
  st.caption('Scroll to zoom · Hover to inspect · Double-click to reset')
 with left:st.plotly_chart(mapfig(layer),use_container_width=True,config=dict(displayModeBar=False,scrollZoom=True))
 finding(f"{stats[stats.code==2].iloc[0].area_km2:,.1f} km² of persistent urban expansion was identified during 2016–2023.")
 st.caption('Display grids are reduced for speed; areas use full-resolution formal statistics. Uncertain and missing trajectories are excluded from the three main categories.')
 if layer=='dem':st.caption('DEM zero-valued cells are masked pending terrain-quality review.')
 about()
with tabs[1]:
 st.subheader('Urban development, ecological response')
 st.caption('Innovation 1 · Trajectory-aware representation')
 with st.columns([1,1.5])[0]:
  chosen=st.selectbox('Urbanization trajectory',list(TRAJECTORIES.values()),key='trajectory')
 u=next(k for k,v in TRAJECTORIES.items() if v==chosen)
 r=stats[stats.code==u].iloc[0]
 left,right=st.columns([1.3,1])
 with left:st.plotly_chart(mapfig('trajectory',u),use_container_width=True,config=dict(displayModeBar=False,scrollZoom=True))
 with right:
  st.markdown('### Vegetation response')
  values=[r.decrease_pct,r.stable_pct,r.increase_pct]
  fig=go.Figure(go.Bar(x=['Degraded','Stable','Improved'],y=values,marker_color=['#FFC48A','#898988','#79CB9B'],text=[f'{v:.1f}%' for v in values],textposition='outside'))
  base(fig);fig.update_yaxes(title='Valid NDVI area / %',range=[0,100]);st.plotly_chart(fig,use_container_width=True,config=dict(displayModeBar=False,scrollZoom=True))
  st.metric('Trajectory area',f'{r.area_km2:,.2f} km²')
  st.caption(f'Response denominator: {int(r.NDVI_valid_pixels):,} valid 10 m pixels; {int(r.NDVI_missing_pixels):,} NDVI-missing pixels excluded. This is an area statistic, not the RF sample distribution.')
 finding({1:f'{r.increase_pct:.1f}% of valid NDVI area in persistent built-up areas showed vegetation improvement.',2:f'{r.decrease_pct:.1f}% of valid NDVI area in new persistent expansion showed vegetation degradation.',3:f'{r.stable_pct:.1f}% of valid NDVI area in the non-built background remained stable.'}[u])
with tabs[2]:
 st.subheader('Performance with Explicit Generalization Limits')
 st.caption('Innovation 2 · Spatially trustworthy AI')
 perf,explain,robust=st.tabs(['Model Performance','Explainability','Robustness'])
 with perf:
  rf=bench[bench.Model=='Random Forest'].iloc[0];ridge=bench[bench.Model=='Ridge'].iloc[0]
  random_r2=validation[(validation.Scope=='All area')&(validation.Validation=='Random 5-fold')].iloc[0].R2
  cards=st.columns(3)
  cards[0].metric('RF Spatial OOF R²',f'{rf.OOF_R2:.3f}')
  cards[1].metric('RF vs Ridge ΔR²',f'{rf.OOF_R2-ridge.OOF_R2:+.3f}')
  cards[2].metric('Random CV − Spatial 20 km ΔR²',f'{random_r2-rf.OOF_R2:.3f}')
  left,right=st.columns(2)
  with left:
   st.markdown('### Model benchmark')
   model=st.selectbox('Benchmark model',bench.Model.tolist(),index=bench.Model.tolist().index('Random Forest'))
   row=bench[bench.Model==model].iloc[0]
   c=st.columns(3)
   for col,label,val in zip(c,['OOF R²','RMSE','MAE'],[row.OOF_R2,row.OOF_RMSE,row.OOF_MAE]):col.metric(label,f'{val:.4f}')
   fig=go.Figure(go.Bar(x=bench.Model,y=bench.OOF_R2,marker_color=['#547AC0' if x==model else '#DBE6F7' for x in bench.Model]));base(fig,260);fig.update_yaxes(title='Pooled OOF R²');st.plotly_chart(fig,use_container_width=True,config=dict(displayModeBar=False,scrollZoom=True))
   st.caption('Same 12,596 samples and 20-km spatial folds; fixed configurations. RF is retained among these four tested models, not claimed to be universally best.')
   rf=bench[bench.Model=='Random Forest'].iloc[0];ridge=bench[bench.Model=='Ridge'].iloc[0]
   st.info(f'RF vs Ridge: RMSE {(1-rf.OOF_RMSE/ridge.OOF_RMSE)*100:.1f}% lower · MAE {(1-rf.OOF_MAE/ridge.OOF_MAE)*100:.1f}% lower')
  with right:
   st.markdown('### Spatial generalization')
   strategy=st.selectbox('Validation strategy',validation.Validation.unique().tolist(),index=2)
   selected=validation[(validation.Scope=='All area')&(validation.Validation==strategy)].iloc[0];st.metric('All-area OOF R²',f'{selected.R2:.4f}')
   fig=go.Figure()
   for (scope,d),color in zip(validation.groupby('Scope',sort=False),['#547AC0','#898988','#FFC48A','#79CB9B']):
    fig.add_trace(go.Scatter(x=d.Validation,y=d.R2,name=scope,mode='lines+markers',marker=dict(size=[11 if x==strategy else 5 for x in d.Validation]),line=dict(color=color)))
   base(fig,315);fig.update_layout(legend=dict(orientation='h',y=-.35));fig.update_yaxes(title='Pooled OOF R²',zeroline=True);st.plotly_chart(fig,use_container_width=True,config=dict(displayModeBar=False,scrollZoom=True))
   st.caption('20 km is the main scale; 10/40 km are sensitivity analyses. No buffer: block separation does not guarantee spatial independence. Negative R² is retained.')
 with explain:
  st.caption('These are global predictive associations, not causal explanations or point-specific drivers.')
  imp=table('permutation.csv').sort_values('mean')
  shap=table('shap.csv').sort_values('mean_abs_SHAP')
  left,right=st.columns(2)
  with left:
   st.markdown('### Global Importance')
   st.caption('Permutation importance · predictive performance sensitivity')
   fig=go.Figure(go.Bar(x=imp['mean'],y=imp.feature,orientation='h',marker_color='#547AC0'));base(fig,300);fig.update_xaxes(title='Permutation importance')
   st.plotly_chart(fig,use_container_width=True,config=dict(displayModeBar=False))
  with right:
   st.markdown('### SHAP Summary')
   st.caption('Global mean absolute SHAP · contribution magnitude')
   fig=go.Figure(go.Bar(x=shap.mean_abs_SHAP,y=shap.feature,orientation='h',marker_color='#A369B0'));base(fig,300);fig.update_xaxes(title='Mean |SHAP value|')
   st.plotly_chart(fig,use_container_width=True,config=dict(displayModeBar=False))
  finding('Top predictive drivers by permutation importance: '+', '.join(imp.sort_values('mean',ascending=False).feature.head(3))+'.')
  with st.columns([1,2])[0]:
   feature=st.selectbox('Feature Response',['NDVIbase','Slope','DEM','Temperature'])
  field={'Temperature':'TEMmean'}.get(feature,feature)
  response_data=table('feature_response.csv')
  d=response_data[response_data.feature==field].sort_values('x_mean')
  fig=go.Figure(go.Scatter(x=d.x_mean,y=d.shap_mean,mode='lines+markers',line=dict(color='#547AC0'),customdata=d.n,hovertemplate='Feature: %{x:.4f}<br>Mean SHAP: %{y:.5f}<br>Bin samples: %{customdata}<extra></extra>'))
  base(fig,260);fig.update_xaxes(title=feature);fig.update_yaxes(title='Mean SHAP value',zeroline=True)
  st.plotly_chart(fig,use_container_width=True,config=dict(displayModeBar=False))
  st.caption('Binned means from the saved formal SHAP analysis; each point summarizes observations within a feature bin. This is not a causal response curve.')
  with st.expander('View detailed feature statistics'):
   st.dataframe(imp,use_container_width=True,hide_index=True)
   st.dataframe(shap,use_container_width=True,hide_index=True)
  with st.expander('View original SHAP summary figure'):
   evidence_image(P/'assets/shap.png')
 with robust:
  evidence=st.selectbox('Evidence',['Residual diagnostics','Sen–MK verification','Matched event-time comparison'])
  file={'Residual diagnostics':'residual.png','Sen–MK verification':'sen_mk.png','Matched event-time comparison':'event_time.png'}[evidence]
  evidence_image(P/'assets'/file)
  st.caption('Reused formal analyses. Matched event-time contrasts are supportive observational evidence, not identified causal effects.')
with tabs[3]:
 st.subheader('From ecological evidence to management priorities')
 st.caption('Innovation 3 · Multi-evidence diagnosis and governance zoning')
 left,right=st.columns([1.5,1])
 with left:
  st.plotly_chart(mapfig('governance'),use_container_width=True,config=dict(displayModeBar=False,scrollZoom=True))
  st.caption('Excluded and missing-data areas are blank. Zoomed map uses display resampling; exact zone areas are shown below.')
 with right:
  st.markdown('### Diagnosis Report')
  st.caption('SELECTED CONDITION')
  chosen_g=st.selectbox('Trajectory',list(TRAJECTORIES.values()),key='governance_trajectory')
  gu=next(k for k,v in TRAJECTORIES.items() if v==chosen_g)
  response=st.selectbox('Vegetation response',['Degraded','Stable','Improved'])
  zone,name,priority=diagnose(gu,response)
  st.markdown('**Ecological diagnosis**');st.write(f'{response} vegetation in {TRAJECTORIES[gu].lower()} areas.')
  st.markdown('**Governance Priority**');st.success(name)
  st.markdown('**Recommended Actions**')
  for action in priority.split('. '):
   if action.strip():st.markdown('- '+action.rstrip('.')+'.')
  st.caption('Rule-based screening recommendation for field review. The selected scenario is not a location-specific diagnosis or a validated management outcome.')
  zr=zone_stats[zone_stats.Zone_ID==zone].iloc[0]
  st.metric('Total area assigned to this governance zone',f'{zr.Area_km2:,.2f} km²',delta=None)
  st.caption(f'{zr.Percentage_valid_area:.2f}% of valid assigned area; not the area of the selected scenario alone.')
 with st.expander('Formal map and exact area statistics'):
  evidence_image(P/'assets/governance_formal.png')
  st.dataframe(zone_stats[['Governance_zone_EN','Area_km2','Percentage_valid_area']],use_container_width=True,hide_index=True)
 st.download_button('Download governance statistics',zone_stats.to_csv(index=False).encode('utf-8-sig'),'governance_statistics.csv','text/csv')
footer()




