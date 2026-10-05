from pathlib import Path
import hashlib
import io
import json
import runpy
import uuid
import zipfile
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from validation import validate, read_upload, template
from utils.style import header, footer, about
from basic_analysis import analyze
import plotly.express as px
import plotly.graph_objects as go
from pyproj import Transformer
from boundary import validate_boundary, rings

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='OasisInsight | Projects',page_icon='🌿',layout='wide')
st.session_state.setdefault('route','Product')
st.session_state.setdefault('projects',{})
def set_route(route):
    st.session_state.route=route

def navigate(route):
    st.session_state.route=route
    st.rerun()

def result_workspace(project):
    st.title(project['name'])
    st.caption(f"{project['area']} · {project['start']}–{project['end']} · Basic analysis complete")
    result=project['result']; summary=project['summary']
    a,b,c=st.columns(3)
    a.metric('Observations',len(result)); b.metric('Mean dNDVI',f'{result.dNDVI.mean():.4f}'); c.metric('Confirmed expansion',int((result.Trajectory=='New persistent expansion').sum()))
    tabs=st.tabs(['Overview','Trajectory & Response','Export'])
    with tabs[0]:
        fig=px.scatter(result,x='X',y='Y',color='Trajectory',hover_data=['ID','dNDVI'],color_discrete_sequence=['#898988','#79CB9B','#FFC48A','#547AC0','#A369B0'])
        if project.get('boundary'):
            transform=Transformer.from_crs(4326,project['crs'],always_xy=True)
            for ring in rings(project['boundary']):
                xs,ys=transform.transform(*zip(*[(p[0],p[1]) for p in ring]))
                fig.add_trace(go.Scatter(x=list(xs),y=list(ys),mode='lines',line=dict(color='#898988',width=2),name='Study boundary',showlegend=False,hoverinfo='skip'))
        fig.update_yaxes(scaleanchor='x',scaleratio=1)
        st.plotly_chart(fig,use_container_width=True)
        st.caption('Spatial observations in the supplied CRS: '+project['crs'])
        if project.get('boundary_audit'):
            st.caption(f"Boundary alignment: {project['boundary_audit']['points_inside']:,} observations inside; {project['boundary_audit']['points_outside']:,} outside. Boundary is supplied WGS84 GeoJSON.")
    with tabs[1]:
        st.plotly_chart(px.bar(summary,x='Trajectory',y='Count',color='Response',color_discrete_sequence=['#898988','#79CB9B','#FFC48A','#547AC0','#A369B0']),use_container_width=True)
        st.dataframe(summary,hide_index=True,use_container_width=True)
    with tabs[2]:
        archive=io.BytesIO()
        config={k:v for k,v in project.items() if k not in ['result','summary']}
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('trajectory_vegetation_results.csv',result.to_csv(index=False))
            z.writestr('response_statistics.csv',summary.to_csv(index=False))
            z.writestr('analysis_record.json',json.dumps(config,indent=2,ensure_ascii=False))
            if project.get('boundary'): z.writestr('study_boundary.geojson',json.dumps(project['boundary'],ensure_ascii=False))
        st.download_button('Download analysis results',archive.getvalue(),'oasisinsight_results.zip','application/zip')
    with st.expander('Method and scope'):
        st.write(project['response_method'])
        st.write('Counts describe uploaded observations, not land area. Persistent expansion must remain built through the end of the time window. RF, SHAP and governance are available in the Urumqi case study; this run computes trajectories and endpoint vegetation change.')
    st.caption('Session project · Download results before leaving.')

def project_workspace(project):
    if 'result' in project:
        result_workspace(project)
        return
    st.subheader(project['name'])
    st.caption(f"{project['area']} · {project['start']}–{project['end']} · Prepared project")
    st.info('Input validation and configuration are saved. Analysis engines are not connected in this release; no model results have been generated.')
    for msg in project['audit']['warnings']: st.warning(msg)
    st.dataframe(pd.DataFrame(project['audit']['modules']),hide_index=True,use_container_width=True)
    a,b=st.columns(2)
    a.metric('Input observations',project['audit']['rows'])
    b.metric('Annual observations',project['end']-project['start']+1)
    with st.expander('Configuration and validation record'):
        st.json(project)
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('project_config.json',json.dumps(project,indent=2,ensure_ascii=False))
        z.writestr('validation_fields.csv',pd.DataFrame(project['audit']['checks']).to_csv(index=False))
        z.writestr('README.txt','Prepared input configuration only. No trajectory, model, SHAP or governance results have been computed. Raw uploaded data is not included. Re-upload it to resume in a later session.')
    st.download_button('Export project setup',archive.getvalue(),'oasisinsight_project_setup.zip','application/zip')
    st.caption('Projects and uploaded data are held in this browser session only. Download the setup before leaving. Refresh or server restart can clear the session.')

header(context=None)
nav=['Product','New Analysis','Projects','Urumqi Case Study','About']
for col,label in zip(st.columns(5),nav):
    col.button(label,key='nav_'+label,use_container_width=True,on_click=set_route,args=(label,))
st.divider()
if st.session_state.route in ['Urumqi Demo','Urumqi Case Study']:
    st.caption('URUMQI CASE STUDY · 2016–2023 · Research workflow and precomputed results')
    runpy.run_path(str(ROOT/'demo_workspace.py'))
    st.stop()
if st.session_state.route in ['Home','Product']:
    st.title('Understand urban change. Inform ecological decisions.')
    st.write('OasisInsight · AI-assisted ecological diagnosis for multi-year urban environments')
    st.markdown('**Multi-year data → Trajectories → Spatial AI → Explanation → Diagnosis → Governance**')
    for col,title,body in zip(st.columns(3),['Trajectory-aware Analysis','Trustworthy Spatial AI','Diagnosis to Governance'],['Identify persistent development and vegetation change across a flexible time window.','Explore spatial validation, model benchmarks and interpretable evidence in the Urumqi case.','Explore reproducible governance zoning backed by the Urumqi research workflow.']):
        with col:
            st.subheader(title); st.write(body)
    a,b=st.columns(2)
    if a.button('Start New Analysis',type='primary',use_container_width=True): navigate('New Analysis')
    if b.button('Explore Urumqi Case',use_container_width=True): navigate('Urumqi Case Study')
    st.caption('New analyses: trajectories, endpoint NDVI change and downloadable statistics. Full spatial AI evidence: Urumqi Case Study.')
elif st.session_state.route=='Projects':
    st.title('Projects')
    if not st.session_state.projects:
        st.info('Your projects will appear here. Start a new analysis to create one.')
    for pid,project in st.session_state.projects.items():
        with st.container(border=True):
            st.write(f"**{project['name']}** · {project['area']} · {project['start']}–{project['end']}")
            if st.button('Open project',key=pid):
                st.session_state.current_project=pid
                navigate('Project Workspace')
    st.caption('Projects are available in this session. Export results to keep them.')
elif st.session_state.route=='About':
    st.title('Xinjiang University · Team OasisInsight')
    st.write('Chunhui Li · Chao Guo · Xiaxuan Zhang')
    about()
    st.write('A reusable analytical framework for urban ecological research. Urumqi provides the completed research case.')
    st.caption('SHAP explains predictive associations. Spatial block validation assesses transfer performance without guaranteeing independence.')
elif st.session_state.route=='Project Workspace':
    project_workspace(st.session_state.projects[st.session_state.current_project])
else:
    st.title('New Analysis')
    st.caption('01 Study setup → 02 Upload & validate → 03 Configure → 04 Review & run')
    st.subheader('01 · Study Setup')
    a,b=st.columns(2)
    name=a.text_input('Project name',key='project_name',max_chars=100)
    area=b.text_input('Study area name',key='study_area',max_chars=100)
    a,b,c=st.columns(3)
    start=int(a.number_input('Start year',min_value=1900,max_value=2100,value=2018,step=1))
    end=int(b.number_input('End year',min_value=1900,max_value=2100,value=2024,step=1))
    c.metric('Annual observations',max(0,end-start+1))
    crs=st.text_input('Coordinate reference system',placeholder='e.g. EPSG:4326 or a suitable local projected CRS')
    st.caption('X = longitude/easting; Y = latitude/northing. Specify the actual data CRS. Spatial blocks need projected coordinates in metres.')
    description=st.text_area('Project description (optional)',max_chars=1000)
    valid_period=2<=end-start+1<=50
    if not valid_period: st.error('Select 2–50 consecutive annual observations. This is a prototype input limit, not a statistical sufficiency claim.')
    st.divider()
    st.subheader('02 · Upload & Validate')
    upload_panel=st.container(border=True)
    with upload_panel:
        st.write('Upload your study dataset')
        upload=st.file_uploader('Standardized analysis data',type=['csv','parquet'])
        boundary_upload=st.file_uploader('Study boundary (optional WGS84 GeoJSON)',type=['geojson','json'])
        validation_panel=st.container()
    st.caption('UTF-8 CSV / Parquet · up to 20 MB, 50,000 rows and 250 columns. Use Built = 0/1, NDVI in [-1, 1], and Slope in degrees. No automatic imputation.')
    if valid_period:
        st.download_button('Download input template',template(start,end),'input_template.csv','text/csv')
        st.caption(f'Optional Built_{end+1} confirms terminal-year expansion only. Intermediate NDVI years may be omitted, but trend modules will be unavailable.')
    with st.expander('Input semantics'):
        st.write('One row is one spatial observation, with a unique ID. Full Built series and endpoint NDVI are required. NTLmean, NTLchg, PREmean, TEMmean, AImean, DEM and Slope are optional for basic analysis and required only for model input screening. Confirm units and period consistency before analysis.')
        st.write('Point samples alone do not establish pixel areas or polygon boundaries. New projects will not inherit the Urumqi area totals or maps.')
    st.divider()
    st.subheader('03 · Analysis Configuration')
    a,b=st.columns(2)
    block=float(a.number_input('Spatial block size / km',min_value=0.1,max_value=1000.0,value=20.0,step=5.0))
    b.metric('Planned spatial folds',5)
    st.caption('20 km is a starting suggestion, not a universal optimum. Block separation without a buffer does not guarantee spatial independence.')
    mode=st.selectbox('Vegetation response thresholds',['Auto','Custom'])
    cutpoints=None
    threshold_error=''
    if mode=='Custom':
        thresholds=st.text_input('Four ordered internal cutpoints for G1–G5',placeholder='Enter four comma-separated numbers appropriate for your study')
        st.caption('Four internal cutpoints define five bins. Their ecological interpretation and the degraded/stable/improved grouping must be justified for the study; Urumqi thresholds are not global defaults.')
        try:
            cutpoints=[float(v.strip()) for v in thresholds.split(',')]
            if len(cutpoints)!=4 or not all(-2<v<2 for v in cutpoints) or any(x>=y for x,y in zip(cutpoints,cutpoints[1:])): raise ValueError()
        except ValueError: threshold_error='Enter four strictly increasing finite cutpoints inside (-2, 2).'
        if threshold_error: st.warning(threshold_error)
    else: st.caption('Auto: classify endpoint NDVI change as decrease, no change or increase using its sign. This is descriptive change, not a significance test.')
    st.text_input('Analysis scope',value='Trajectory + dNDVI + statistics',disabled=True)
    with st.expander('Advanced Options'):
        st.caption('These analysis modules will become selectable when their engines are integrated.')
        st.checkbox('Benchmark comparison',disabled=True)
        st.checkbox('SHAP interpretation',disabled=True)
        st.checkbox('Residual diagnostics',disabled=True)
    audit=None
    boundary_geo=None
    boundary_audit=None
    raw=None
    with validation_panel:
        if upload is None:
            st.info('Choose a CSV or Parquet file to check fields, years and coordinates.')
        elif not valid_period:
            st.warning('Correct the study period before validation.')
        else:
            try:
                raw=upload.getvalue()
                frame=read_upload(raw,upload.name)
                audit=validate(frame,start,end,crs,block)
                if boundary_upload is not None and not audit['errors']:
                    try:
                        boundary_geo,boundary_audit=validate_boundary(boundary_upload.getvalue(),frame,crs)
                        st.caption(f"Boundary alignment: {boundary_audit['points_inside']:,} observations inside, {boundary_audit['points_outside']:,} outside.")
                        if boundary_audit['points_outside']: audit['errors'].append('Some observations lie outside the supplied boundary. Verify the boundary and point CRS before running.')
                    except Exception as exc: audit['errors'].append('Boundary validation: '+str(exc))
                st.write(f'File: {upload.name}')
                a,b,c=st.columns(3)
                a.metric('Rows',len(frame))
                b.metric('Fields',len(frame.columns))
                missing_count=int(frame.isna().sum().sum())
                c.metric('Missing cells',f'{missing_count / max(1,frame.size):.2%}')
                st.caption('Missing cells counts blank/NaN cells across the uploaded table; sentinel and invalid values are checked separately.')
                st.subheader('Data Validation Summary')
                summary=[]
                for label,cols in [
                    ('ID / coordinates',['ID','X','Y']),
                    ('Built-up series',[f'Built_{y}' for y in range(start,end+1)]),
                    ('Endpoint NDVI',[f'NDVI_{start}',f'NDVI_{end}']),
                    ('Annual NDVI',[f'NDVI_{y}' for y in range(start,end+1)]),
                    ('Predictors',['NTLmean','NTLchg','PREmean','TEMmean','AImean','DEM','Slope'])]:
                    absent=[v for v in cols if v not in frame]
                    summary.append({'Input':label,'Field coverage':'Complete' if not absent else 'Missing: '+', '.join(absent)})
                st.dataframe(pd.DataFrame(summary),hide_index=True,use_container_width=True)
                st.caption('Field coverage indicates column presence only. Value and CRS checks are reported below.')
                for prefix in ['Built','NDVI']:
                    years=sorted(int(str(col).split('_')[1]) for col in frame.columns if str(col).startswith(prefix+'_') and str(col).split('_')[1].isdigit())
                    st.caption(f'{prefix} years detected: '+(', '.join(map(str,years)) or 'None'))
                for msg in audit['errors']: st.error(msg)
                for msg in audit['warnings']: st.warning(msg)
                if not audit['errors']: st.success('Required fields, values and coordinate checks passed. Review warnings before saving.')
                with st.expander('Data preview and field checks'):
                    st.dataframe(frame.head(20),use_container_width=True,hide_index=True)
                    st.dataframe(pd.DataFrame(audit['checks']),hide_index=True,use_container_width=True)
                with st.expander('Analysis eligibility'):
                    st.dataframe(pd.DataFrame(audit['modules']),hide_index=True,use_container_width=True)
            except Exception as exc:
                audit=None
                st.error(f'Cannot validate file: {exc}')
    st.divider()
    st.subheader('04 · Review & Run')
    st.dataframe(pd.DataFrame([{'Setting':'Project','Value':name or 'Not entered'},{'Setting':'Study area','Value':area or 'Not entered'},{'Setting':'Period','Value':f'{start}–{end}'},{'Setting':'CRS','Value':crs or 'Not entered'},{'Setting':'Input','Value':upload.name if upload else 'No file'},{'Setting':'Threshold method','Value':mode},{'Setting':'Analysis','Value':'Trajectory + dNDVI + statistics'}]),hide_index=True,use_container_width=True)
    st.caption('This run produces trajectory and vegetation-change results. Spatial AI and governance evidence can be explored in the Urumqi case.')

    reviewed=st.checkbox('I have reviewed the input units, CRS, validation warnings and study-specific thresholds.')
    ready=bool(name.strip() and area.strip() and audit is not None and not audit['errors'] and not threshold_error and reviewed)
    if st.button('Run Analysis',type='primary',disabled=not ready):
        with st.status('Preparing project',expanded=True) as status:
            st.write('Input checks completed.')
            pid=uuid.uuid4().hex
            project=dict(id=pid,name=name.strip(),area=area.strip(),start=start,end=end,crs=crs,description=description,created_at=datetime.now(timezone.utc).isoformat(),status='prepared',input_sha256=hashlib.sha256(raw).hexdigest(),config=dict(threshold_method=mode,cutpoints=cutpoints,spatial_block_km=block,folds=5,model='Random Forest',governance_rules='Study-specific mapping pending; no zones computed'),audit=audit)
            st.write('Identifying trajectories and computing endpoint NDVI change...')
            result,summary,method=analyze(frame,start,end,cutpoints)
            project.update(result=result,summary=summary,response_method=method,status='complete_basic')
            if boundary_geo is not None:
                project.update(boundary=boundary_geo,boundary_audit=boundary_audit,boundary_sha256=hashlib.sha256(boundary_upload.getvalue()).hexdigest())
            project['config']['model']='Not run; basic analysis'
            st.session_state.projects[pid]=project
            st.session_state.current_project=pid
            st.write('Trajectory and vegetation statistics completed. Building project workspace.')
            status.update(label='Basic analysis complete',state='complete',expanded=False)
        navigate('Project Workspace')
st.caption("OasisInsight · Xinjiang University")
