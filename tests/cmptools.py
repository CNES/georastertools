import json
import xml.etree.ElementTree as ET

import geopandas as gpd
import shapely.wkt
from osgeo import gdal
from osgeo_utils import gdalcompare


def cmp_geojson(golden, new, column_sortby = None, tolerance=1e-9):
    # Load GeoJSON files
    gld_gj = json.load(open(golden))
    new_gj = json.load(open(new))

    # Construct geospatial objects using geopandas and shapely
    gld_gdf = gpd.GeoDataFrame.from_features(gld_gj["features"])
    new_gdf = gpd.GeoDataFrame.from_features(new_gj["features"])

    if column_sortby :
        gld_gdf = gld_gdf.sort_values(by=column_sortby)
        new_gdf = new_gdf.sort_values(by=column_sortby)

    equals = True
    # Compare each geometry using Hausdorff distance
    for gld_geom, new_geom in zip(gld_gdf.geometry, new_gdf.geometry):
        if gld_geom.hausdorff_distance(new_geom) > tolerance:
            equals = False

    return equals


def cmp_shp(golden, new, tolerance=1e-9):
    # Construct geospatial objects using geopandas and shapely
    gld_gdf = gpd.read_file(golden)
    new_gdf = gpd.read_file(new)

    equals = True
    # Compare each geometry using Hausdorff distance
    for geom1, geom2 in zip(gld_gdf.geometry, new_gdf.geometry):
        if geom1.hausdorff_distance(geom2) > tolerance:
            equals = False

    return equals


class Element:
    def __init__(self, e):
        self.name = e.tag
        self.subs = {}
        self.atts = {}
        self.text = e.text
        for child in e:
            self.subs[child.tag] = Element(child)

        for att in e.attrib.keys():
            self.atts[att] = e.attrib[att]

    def equals(self, el, tolerance):
        if self.name != el.name:
            return False

        equality = True

        # Text compare
        t1 = self.text
        t2 = el.text

        if t1 and "POLYGON" in t1:
            p1 = shapely.wkt.loads(t1)
            p2 = shapely.wkt.loads(t2)
            if p1.hausdorff_distance(p2) > tolerance:
                return False
        elif "GeoTransform" in self.name:
            transform1 = [float(x) for x in t1.split(",")]
            transform2 = [float(x) for x in t2.split(",")]
            if transform1 != transform2:
                return False
        else:
            if t2 != t1:
                return False

        # Attributes compare
        for att in self.atts.keys():
            v1 = self.atts[att]
            if att not in el.atts.keys():
                v2 = "[NA]"
                color = "yellow"
            else:
                v2 = el.atts[att]

            if v2 != v1:
                return False

        for subName in self.subs.keys():
            if subName not in el.subs.keys():
                equality = False
            else:
                if not self.subs[subName].equals(el.subs[subName], tolerance):
                    equality = False

        return equality


def cmp_vrt(golden, new, tolerance=1e-9):
    # Open both xml files
    gld_tree = ET.parse(golden)
    gld_root = gld_tree.getroot()
    gld_e = Element(gld_root)

    new_tree = ET.parse(new)
    new_root = new_tree.getroot()
    new_e = Element(new_root)

    return new_e.equals(gld_e, tolerance)


def cmp_tif(golden, new, tolerance=1e-2):
    gld_ds = gdal.Open(golden, gdal.GA_ReadOnly)
    new_ds = gdal.Open(new, gdal.GA_ReadOnly)
    d_count = gdalcompare.compare_db(gld_ds, new_ds, options= ['SKIP_METADATA'])
    p_count = gld_ds.RasterCount * gld_ds.RasterXSize * gld_ds.RasterYSize
    return d_count *100. / p_count < tolerance


def cmp_png(golden, new, tolerance=1e-9):
    with open(golden, 'rb') as gld_f, open(new, 'rb') as new_f:
        gld_content = gld_f.read()
        new_content = new_f.read()
    return gld_content == new_content   


CMP_FUN = {
    ".tif": cmp_tif,
    ".png": cmp_png,
    ".vrt": cmp_vrt,
    ".shp": cmp_shp,
    ".geojson": cmp_geojson,
}
