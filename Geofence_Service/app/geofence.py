from typing import List
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from .models import Zone, LatLon

EARTH_RADIUS_M = 6371000.0

def _point(lat: float, lon: float) -> Point:
    # For small areas, approximate by treating lat/lon as planar with scaling.
    # Convert degrees to meters via simple equirectangular approximation near Pune.
    # 1 deg lat ~ 111_132 m; 1 deg lon ~ 111_320 * cos(lat)
    lat_m = lat * 111_132.0
    lon_m = lon * 111_320.0 * __import__("math").cos(__import__("math").radians(lat))
    return Point(lon_m, lat_m)

def point_from_latlon(p: LatLon) -> Point:
    return _point(p.lat, p.lon)

def contains(z: Zone, p: LatLon) -> bool:
    pt = point_from_latlon(p)
    if z.type == "circle":
        assert z.center and z.radius_m is not None
        c = point_from_latlon(z.center)
        return pt.distance(c) <= z.radius_m
    elif z.type == "polygon":
        assert z.points
        poly = Polygon([(_point(pp.lat, pp.lon).x, _point(pp.lat, pp.lon).y) for pp in z.points])
        return poly.contains(pt) or poly.touches(pt)  # count boundary as inside
    else:
        return False

def zones_for_point(zones: List[Zone], p: LatLon) -> List[str]:
    return [z.id for z in zones if contains(z, p)]