"""Input audit only. No imputation, model training or ecological classification."""
import csv
import io
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer

PREDICTORS = ['NTLmean', 'NTLchg', 'PREmean', 'TEMmean', 'AImean', 'DEM', 'Slope']
MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 50000


def read_upload(raw, name):
    if len(raw) > MAX_BYTES:
        raise ValueError('File exceeds the 20 MB prototype limit.')
    if name.lower().endswith('.csv'):
        text = raw.decode('utf-8-sig')
        columns = next(csv.reader(io.StringIO(text)), [])
        if len(columns) != len(set(columns)):
            raise ValueError('Duplicate CSV column names. Rename them before uploading.')
        frame = pd.read_csv(io.StringIO(text), nrows=MAX_ROWS + 1, dtype={'ID': 'string'})
    elif name.lower().endswith('.parquet'):
        import pyarrow.parquet as pq
        file = pq.ParquetFile(io.BytesIO(raw))
        if file.metadata.num_rows > MAX_ROWS:
            raise ValueError('Dataset exceeds the 50,000-row prototype limit.')
        if len(file.schema.names) > 250 or sum(file.metadata.row_group(i).total_byte_size for i in range(file.metadata.num_row_groups)) > 128*1024*1024:
            raise ValueError('Parquet expands beyond the prototype memory/column limit.')
        frame = file.read().to_pandas()
    else:
        raise ValueError('Upload a UTF-8 CSV or Parquet file.')
    if len(frame) > MAX_ROWS or len(frame.columns) > 250:
        raise ValueError('Prototype limit: 50,000 rows and 250 columns.')
    if frame.columns.duplicated().any():
        raise ValueError('Duplicate column names.')
    return frame


def template(start, end):
    columns = ['ID', 'X', 'Y'] + [f'Built_{y}' for y in range(start, end+1)]
    columns += [f'NDVI_{y}' for y in range(start, end+1)] + PREDICTORS
    return pd.DataFrame(columns=columns).to_csv(index=False)


def validate(frame, start, end, crs_text, block_km, folds=5):
    errors, warnings, checks = [], [], []
    if not 2 <= end-start+1 <= 50:
        return dict(errors=['Choose 2–50 consecutive annual observations for this prototype.'], warnings=[], checks=[], modules=[], rows=len(frame))
    built = [f'Built_{y}' for y in range(start, end+1)]
    annual = [f'NDVI_{y}' for y in range(start, end+1)]
    required = ['ID', 'X', 'Y'] + built + [annual[0], annual[-1]]
    missing = [c for c in required if c not in frame]
    if missing: errors.append('Missing required columns: ' + ', '.join(missing))
    if frame.empty: errors.append('The uploaded table has no observations.')
    if 'ID' in frame:
        ids = frame.ID.astype('string').str.strip()
        if ids.isna().any() or ids.eq('').any(): errors.append('ID contains blank values.')
        if ids.duplicated().any(): errors.append('ID must be unique; duplicate IDs detected.')
    relevant = list(dict.fromkeys([c for c in required if c != 'ID'] + annual + [f'Built_{end+1}'] + PREDICTORS))
    model_errors = []
    clean = {}
    for c in relevant:
        if c not in frame: continue
        s = pd.to_numeric(frame[c], errors='coerce')
        null = int(frame[c].isna().sum())
        invalid = int((s.isna() & frame[c].notna()).sum())
        sentinel = int(s.eq(-9999).sum())
        infinite = int(np.isinf(s).sum())
        clean[c] = s
        checks.append(dict(Field=c, Missing=null, Non_numeric=invalid, Sentinel=sentinel, Infinite=infinite))
        issues = errors if c in required else model_errors if c in PREDICTORS else warnings
        if null or invalid or sentinel or infinite:
            issues.append(f'{c}: {null} missing, {invalid} non-numeric, {sentinel} sentinel (-9999), {infinite} infinite values. No values were imputed.')
        valid = s.dropna()
        if c.startswith('Built_') and not valid.isin([0,1]).all():
            (errors if c != f'Built_{end+1}' else warnings).append(f'{c}: Built values must be 0 or 1; invalid confirmation values remain unconfirmed.')
        if c.startswith('NDVI_') and not valid.between(-1,1).all(): issues.append(f'{c}: NDVI must be unscaled values in [-1, 1].')
        if c == 'Slope' and not valid.between(0,90).all(): model_errors.append('Slope must be degrees in [0, 90].')
    complete_annual = all(c in clean and np.isfinite(clean[c]).all() and clean[c].between(-1,1).all() for c in annual)
    missing_predictors = [c for c in PREDICTORS if c not in frame]
    if missing_predictors: model_errors.append('Missing model predictors: ' + ', '.join(missing_predictors))
    if model_errors: warnings.append('RF / SHAP input not ready. Basic analysis does not require environmental predictors.')
    if not complete_annual: warnings.append('Incomplete annual NDVI: Sen–MK and event-time cannot be enabled.')
    if f'Built_{end+1}' not in frame:
        warnings.append(f'Built_{end+1} is absent. First-time expansion in {end} cannot be confirmed and must remain unconfirmed.')
    block_counts = []
    try:
        crs = CRS.from_user_input(crs_text)
        if not (crs.is_projected or crs.is_geographic): raise ValueError('Use a projected or geographic CRS.')
        if all(c in clean for c in ['X', 'Y']) and not frame.empty:
            x, y = clean['X'].to_numpy(), clean['Y'].to_numpy()
            if not (np.isfinite(x).all() and np.isfinite(y).all()): raise ValueError('Coordinates must be finite.')
            if crs.is_geographic and not ((abs(x)<=180).all() and (abs(y)<=90).all()):
                raise ValueError('Geographic X/Y must be longitude/latitude in degrees.')
            lon, lat = Transformer.from_crs(crs,4326,always_xy=True).transform(x,y)
            if not (np.isfinite(lon).all() and np.isfinite(lat).all()): raise ValueError('Coordinates cannot be transformed to longitude/latitude.')
            area=crs.area_of_use
            if area and area.west < area.east and not ((np.asarray(lon)>=area.west-.1)&(np.asarray(lon)<=area.east+.1)&(np.asarray(lat)>=area.south-.1)&(np.asarray(lat)<=area.north+.1)).all():
                warnings.append('Some coordinates are outside the CRS area of use; verify the CRS before analysis.')
            if frame[['X','Y']].duplicated().any(): warnings.append('Duplicate coordinate pairs detected; review repeated spatial samples.')
            if crs.is_projected and all(abs(a.unit_conversion_factor-1)<1e-9 for a in crs.axis_info[:2]):
                size=block_km*1000
                groups=pd.DataFrame({'bx':np.floor((x-x.min())/size),'by':np.floor((y-y.min())/size)}).value_counts()
                block_counts=groups.tolist()
            else: warnings.append('Spatial CV requires a suitable local projected CRS in metres; geographic coordinates are not kilometres.')
    except Exception as exc:
        errors.append('CRS / coordinate validation: '+str(exc))
    cv_ok=len(block_counts)>=folds and len(frame)>=2*folds
    if block_counts and not cv_ok: warnings.append(f'Only {len(block_counts)} spatial blocks; insufficient support for {folds} folds.')
    common = not errors
    target_varies = all(c in clean for c in [annual[0], annual[-1]]) and (clean[annual[-1]]-clean[annual[0]]).nunique()>1
    modules=[]
    for name,eligible,reason in [
        ('Trajectory / dNDVI / statistics',common,'Full Built series and valid endpoint NDVI required; uploaded observations are counted, not converted to area.'),
        ('RF / SHAP',common and not model_errors and len(frame)>=10 and target_varies,'Seven valid environmental predictors, at least 10 rows and varying endpoint NDVI difference required; fold-level training eligibility still requires separate checks.'),
        ('Spatial CV',common and not model_errors and cv_ok,'Valid model predictors, at least five occupied metre-based blocks and sufficient observations; fold balancing is not yet run.'),
        ('Sen–MK',common and complete_annual,'Complete annual NDVI required; series length and dependence still need method-specific review.'),
        ('Event-time',False,'Pending onset, control, pre/post-window and matching diagnostics; annual data alone is insufficient.')]:
        modules.append(dict(Module=name, Input_screen='Candidate' if eligible else 'Not ready', Execution='Available' if name=='Trajectory / dNDVI / statistics' and eligible else 'Not connected', Reason=reason))
    return dict(errors=errors,warnings=warnings,model_errors=model_errors,checks=checks,modules=modules,rows=len(frame),annual_observations=end-start+1,spatial_blocks=len(block_counts),block_origin='Input minimum X/Y; screening only, not final fold assignment')
