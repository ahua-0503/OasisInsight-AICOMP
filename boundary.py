"""Validate an optional WGS84 GeoJSON boundary against every input point."""
import json
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.ops import unary_union

def validate_boundary(raw, frame, crs):
    if len(raw)>2*1024*1024:
        raise ValueError('Boundary exceeds 2 MB limit.')
    geo=json.loads(raw.decode('utf-8-sig'))
    if geo.get('type')!='FeatureCollection' or not geo.get('features'):
        raise ValueError('Boundary must be a nonempty GeoJSON FeatureCollection.')
    declared=geo.get('crs')
    if declared and declared.get('properties',{}).get('name') not in ['EPSG:4326','urn:ogc:def:crs:OGC:1.3:CRS84','urn:ogc:def:crs:EPSG::4326']:
        raise ValueError('Boundary must use WGS84 longitude/latitude (EPSG:4326).')
    polygons=[shape(f['geometry']) for f in geo['features']]
    if any(p.geom_type not in ['Polygon','MultiPolygon'] or p.is_empty or not p.is_valid for p in polygons):
        raise ValueError('Boundary must contain valid nonempty polygons.')
    union=unary_union(polygons)
    left,bottom,right,top=union.bounds
    if not (-180<=left<=right<=180 and -90<=bottom<=top<=90):
        raise ValueError('Boundary coordinates are outside longitude/latitude bounds.')
    lon,lat=Transformer.from_crs(crs,4326,always_xy=True).transform(frame.X.to_numpy(),frame.Y.to_numpy())
    if not np.isfinite(lon).all() or not np.isfinite(lat).all():
        raise ValueError('Point coordinates cannot be transformed to WGS84.')
    inside=sum(union.covers(Point(x,y)) for x,y in zip(lon,lat))
    return geo,dict(crs='EPSG:4326',points_inside=int(inside),points_outside=len(frame)-int(inside),bounds=list(union.bounds),source_verification='Supplied boundary; administrative source and year not independently verified.')

def rings(geo):
    for feature in geo['features']:
        g=feature['geometry']
        polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
        for polygon in polygons:
            yield from polygon
