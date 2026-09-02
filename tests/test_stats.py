#!/usr/bin/env python
# -*- coding: utf-8 -*-
from eolab.georastertools.processing import stats, vector

from . import utils4test

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"

from .utils4test import RastertoolsTestsData

__refdir = utils4test.get_refdir("test_stats/")

DEFAULT_STATS = "count min max mean std".split()
EXTRA_STATS = "sum median mad percentile_5 range majority minority unique nodata valid".split()


def test_compute_zonal_default_stats():
    raster = RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
    geojson = RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson"
    stats_to_compute = DEFAULT_STATS
    categorical = False
    bands = [1]

    geometries = vector.filter(vector.reproject(geojson, raster), raster)
    statistics = stats.compute_zonal_stats(geometries, raster, bands=bands,
                                           stats=stats_to_compute, categorical=categorical)

    # statistics is a list of list of dict.
    # First list iterates over geometries
    # Second list iterates over bands.
    assert len(statistics) == len(geometries.index)
    assert len(statistics[0]) == len(bands)

    # round stats to compare with numerical accuracy
    [d.update({key: round(val, 6)})
     for geom_stats in statistics for d in geom_stats for key, val in d.items()]

    # ref is the following
    ref = [[{'count': 321657, 'min': -1.0, 'max': 1.0, 'mean': 0.609034, 'std': 0.273792}],
           [{'count': 45821, 'min': -1.0, 'max': 1.0, 'mean': 0.695903, 'std': 0.208686}],
           [{'count': 12465, 'min': -1.0, 'max': 1.0, 'mean': 0.629209, 'std': 0.292921}],
           [{'count': 87687, 'min': -1.0, 'max': 1.0, 'mean': 0.639204, 'std': 0.237151}],
           [{'count': 13290, 'min': 0.088869, 'max': 1.0, 'mean': 0.700159, 'std': 0.186689}],
           [{'count': 41332, 'min': -0.656766, 'max': 1.0, 'mean': 0.735571, 'std': 0.165584}],
           [{'count': 65786, 'min': -0.927374, 'max': 1.0, 'mean': 0.481607, 'std': 0.243762}],
           [{'count': 93293, 'min': -1.0, 'max': 1.0, 'mean': 0.609265, 'std': 0.25795}],
           [{'count': 50896, 'min': -1.0, 'max': 1.0, 'mean': 0.598643, 'std': 0.255214}],
           [{'count': 64186, 'min': -1.0, 'max': 1.0, 'mean': 0.698426, 'std': 0.210732}],
           [{'count': 83063, 'min': -1.0, 'max': 1.0, 'mean': 0.699223, 'std': 0.213408}],
           [{'count': 4038, 'min': -0.206738, 'max': 1.0, 'mean': 0.734667, 'std': 0.230044}],
           [{'count': 29232, 'min': -0.83908, 'max': 1.0, 'mean': 0.60207, 'std': 0.217282}],
           [{'count': 177106, 'min': -1.0, 'max': 1.0, 'mean': 0.548052, 'std': 0.261178}],
           [{'count': 17772, 'min': 0.038081, 'max': 1.0, 'mean': 0.61795, 'std': 0.269253}],
           [{'count': 169829, 'min': -1.0, 'max': 1.0, 'mean': 0.525915, 'std': 0.258398}],
           [{'count': 28862, 'min': -1.0, 'max': 0.993846, 'mean': 0.597986, 'std': 0.207013}],
           [{'count': 55764, 'min': -1.0, 'max': 1.0, 'mean': 0.560012, 'std': 0.272884}],
           [{'count': 35282, 'min': -1.0, 'max': 1.0, 'mean': 0.570112, 'std': 0.255631}]]

    for geom_stats, ref_stats in zip(statistics, ref):
        for i, band in enumerate(bands):
            assert geom_stats[i] == ref_stats[i]


def test_compute_zonal_extra_stats():
    raster = RastertoolsTestsData.tests_input_data_dir + "/" + "SENTINEL2A_20180928-105515-685_L2A_T30TYP_D-ndvi.tif"
    geojson = RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_32xxx.geojson"
    stats_to_compute = EXTRA_STATS + ["valid"]
    categorical = False
    bands = [1]

    geometries = vector.reproject(vector.filter(geojson, raster), raster)
    statistics = stats.compute_zonal_stats(geometries, raster, bands=bands,
                                           stats=stats_to_compute, categorical=categorical)

    # statistics is a list of list of dict.
    # First list iterates over geometries
    # Second list iterates over bands.
    assert len(statistics) == len(geometries.index)
    assert len(statistics[0]) == len(bands)

    # round stats to compare with numerical accuracy
    [d.update({key: round(val, 6)})
     for geom_stats in statistics for d in geom_stats for key, val in d.items()]

    # ref is the following
    ref = [[{'sum': 195899.928989, 'median': 0.636118, 'range': 2.0,
             'percentile_5': 0.15373, 'mad': 0.218207, 'majority': -1.0,
             'minority': -0.996727, 'unique': 285995,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 31886.95005, 'median': 0.701654, 'range': 2.0,
             'percentile_5': 0.280309, 'mad': 0.161672, 'majority': 1.0,
             'minority': -0.979167, 'unique': 44398,
             'nodata': 367, 'valid': 0.992054}],
           [{'sum': 7843.094361, 'median': 0.682968, 'range': 2.0,
             'percentile_5': 0.12968, 'mad': 0.146711, 'majority': -1.0,
             'minority': -0.993174, 'unique': 12189,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 56049.860487, 'median': 0.668857, 'range': 2.0,
             'percentile_5': 0.154594, 'mad': 0.148523, 'majority': 1.0,
             'minority': -0.977465, 'unique': 83944,
             'nodata': 245, 'valid': 0.997214}],
           [{'sum': 9305.114276, 'median': 0.713093, 'range': 0.911131,
             'percentile_5': 0.358831, 'mad': 0.143713, 'majority': 0.6,
             'minority': 0.088869, 'unique': 13137,
             'nodata': 244, 'valid': 0.981971}],
           [{'sum': 30402.614902, 'median': 0.753216, 'range': 1.656766,
             'percentile_5': 0.433678, 'mad': 0.124387, 'majority': 1.0,
             'minority': -0.656766, 'unique': 40146,
             'nodata': 85, 'valid': 0.997948}],
           [{'sum': 31683.020613, 'median': 0.471969, 'range': 1.927374,
             'percentile_5': 0.110149, 'mad': 0.168122, 'majority': 0.5,
             'minority': -0.927374, 'unique': 63745,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 56840.183386, 'median': 0.629144, 'range': 2.0,
             'percentile_5': 0.134994, 'mad': 0.188218, 'majority': -1.0,
             'minority': -0.993671, 'unique': 89338,
             'nodata': 85, 'valid': 0.99909}],
           [{'sum': 30468.534019, 'median': 0.619463, 'range': 2.0,
             'percentile_5': 0.15824, 'mad': 0.161906, 'majority': -1.0,
             'minority': -0.991903, 'unique': 49427,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 44829.198908, 'median': 0.704596, 'range': 2.0,
             'percentile_5': 0.307304, 'mad': 0.169161, 'majority': 1.0,
             'minority': -0.969231, 'unique': 61646,
             'nodata': 337, 'valid': 0.994777}],
           [{'sum': 58079.578482, 'median': 0.727142, 'range': 2.0,
             'percentile_5': 0.211673, 'mad': 0.138837, 'majority': 1.0,
             'minority': -0.962406, 'unique': 79181,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 2966.584778, 'median': 0.786099, 'range': 1.206738,
             'percentile_5': 0.241052, 'mad': 0.153867, 'majority': 0.941176,
             'minority': -0.206738, 'unique': 4007,
             'nodata': 62, 'valid': 0.984878}],
           [{'sum': 17599.695646, 'median': 0.586743, 'range': 1.83908,
             'percentile_5': 0.255563, 'mad': 0.168826, 'majority': 1.0,
             'minority': -0.83908, 'unique': 28731,
             'nodata': 290, 'valid': 0.990177}],
           [{'sum': 97063.345854, 'median': 0.548321, 'range': 2.0,
             'percentile_5': 0.121661, 'mad': 0.177506, 'majority': -1.0,
             'minority': -0.996276, 'unique': 165519,
             'nodata': 55, 'valid': 0.99969}],
           [{'sum': 10982.207629, 'median': 0.647735, 'range': 0.961919,
             'percentile_5': 0.135674, 'mad': 0.24678, 'majority': 1.0,
             'minority': 0.038081, 'unique': 17550,
             'nodata': 337, 'valid': 0.98139}],
           [{'sum': 89315.609434, 'median': 0.491085, 'range': 2.0,
             'percentile_5': 0.12513, 'mad': 0.170515, 'majority': -1.0,
             'minority': -0.995074, 'unique': 158615,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 17259.079321, 'median': 0.589402, 'range': 1.993846,
             'percentile_5': 0.324657, 'mad': 0.142261, 'majority': -1.0,
             'minority': -0.974359, 'unique': 28279,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 31228.533127, 'median': 0.564933, 'range': 2.0,
             'percentile_5': 0.111111, 'mad': 0.227924, 'majority': -1.0,
             'minority': -0.962085, 'unique': 54423,
             'nodata': 0, 'valid': 1.0}],
           [{'sum': 20114.676941, 'median': 0.537082, 'range': 2.0,
             'percentile_5': 0.231518, 'mad': 0.16068, 'majority': -1.0,
             'minority': -0.991091, 'unique': 34565,
             'nodata': 259, 'valid': 0.992713}]]

    for geom_stats, ref_stats in zip(statistics, ref):
        for i, band in enumerate(bands):
            assert geom_stats[i] == ref_stats[i]


def test_compute_zonal_categorical():
    raster = RastertoolsTestsData.tests_input_data_dir + "/" + "OCS_2017_CESBIO_extract.tif"
    geojson = RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_59xxx.geojson"
    stats_to_compute = ['count']
    categorical = True
    bands = [1]

    geometries = vector.reproject(vector.filter(geojson, raster), raster)
    statistics = stats.compute_zonal_stats(geometries, raster, bands=bands,
                                           stats=stats_to_compute, categorical=categorical)

    # statistics is a list of list of dict.
    # First list iterates over geometries
    # Second list iterates over bands.
    assert len(statistics) == len(geometries.index)
    assert len(statistics[0]) == len(bands)

    # round stats to compare with numerical accuracy
    [d.update({key: round(val, 6)}) for geom_stats in statistics
     for d in geom_stats for key, val in d.items()]

    # ref is the following
    ref = [[{11: 13067, 12: 11970, 31: 8991, 32: 4534, 34: 1190, 36: 1181, 41: 27, 42: 18842,
             43: 7634, 46: 270, 51: 485, 211: 3830, 222: 344, 'count': 72365.0}],
           [{11: 2615, 12: 5701, 31: 5381, 32: 863, 34: 308, 36: 93, 41: 9, 42: 9023,
             43: 979, 46: 261, 51: 22, 211: 1023, 221: 1, 222: 99, 'count': 26378.0}],
           [{11: 99595, 12: 158199, 31: 12867, 32: 6722, 34: 5702, 36: 525, 41: 16, 42: 45626,
             43: 6314, 46: 277, 51: 3228, 211: 19841, 221: 4, 222: 877, 'count': 359793.0}],
           [{11: 60113, 12: 106209, 31: 32745, 32: 6081, 34: 870, 36: 792, 41: 10, 42: 51128,
             43: 7364, 46: 2, 51: 5892, 211: 36505, 221: 13, 222: 237, 'count': 307961.0}],
           [{11: 19532, 12: 44701, 31: 333, 32: 1016, 34: 5, 36: 11, 41: 1, 42: 8859,
             43: 1710, 51: 237, 211: 4353, 222: 19, 'count': 80777.0}]]

    for geom_stats, ref_stats in zip(statistics, ref):
        for i, band in enumerate(bands):
            assert geom_stats[i] == ref_stats[i]


def test_compute_zonal_stats_per_category():
    raster = RastertoolsTestsData.tests_input_data_dir + "/" + "DSM_PHR_Dunkerque.tif"
    geojson = RastertoolsTestsData.tests_input_data_dir + "/" + "COMMUNE_59xxx.geojson"
    catgeojson = RastertoolsTestsData.tests_input_data_dir + "/" + "OSO_2017_classification_dep59.shp"
    catlabels = RastertoolsTestsData.tests_input_data_dir + "/" + "OSO_nomenclature_2017.json"
    stats_to_compute = DEFAULT_STATS
    bands = [1]
    geometries = vector.reproject(vector.filter(geojson, raster), raster)
    categories = vector.reproject(vector.clip(catgeojson, raster), raster)

    # test without category_labels
    statistics = stats.compute_zonal_stats_per_category(geometries, raster, bands=bands,
                                                        stats=stats_to_compute,
                                                        categories=categories,
                                                        category_index="Classe")
    # statistics is a list of list of dict.
    # First list iterates over geometries
    # Second list iterates over bands.
    assert len(statistics) == len(geometries.index)
    assert len(statistics[0]) == len(bands)

    # round stats to compare with numerical accuracy
    [d.update({key: round(val, 6)})
     for geom_stats in statistics for d in geom_stats for key, val in d.items()]

    # ref is the following
    ref = [[{'11min': 40.407368, '11max': 44.083961, '11mean': 42.293813, '11count': 244, '11std': 0.849256,
             '31min': 40.224247, '31max': 68.915146, '31mean': 46.435982, '31count': 12347, '31std': 4.744863,
             '32min': 38.825829, '32max': 46.798634, '32mean': 42.54521, '32count': 6657, '32std': 1.33232,
             '42min': 38.214043, '42max': 59.93272, '42mean': 43.375171, '42count': 2716, '42std': 1.595453,
             '43min': 38.214043, '43max': 45.618088, '43mean': 42.273934, '43count': 875, '43std': 1.241663}],
           [{'11min': 38.475033, '11max': 45.613518, '11mean': 42.386635, '11count': 73437, '11std': 1.090365,
             '12min': 39.241253, '12max': 43.433277, '12mean': 41.991684, '12count': 17339, '12std': 0.313978,
             '31min': 33.781662, '31max': 60.81406, '31mean': 44.562402, '31count': 12743, '31std': 3.051407,
             '32min': 37.670204, '32max': 64.120644, '32mean': 44.396165, '32count': 18284, '32std': 2.749989,
             '42min': 40.806831, '42max': 65.240021, '42mean': 45.256735, '42count': 45240, '42std': 3.348138,
             '43min': 42.136879, '43max': 65.507011, '43mean': 48.296514, '43count': 59113, '43std': 3.671298}]]

    for geom_stats, ref_stats in zip(statistics, ref):
        for i, band in enumerate(bands):
            assert geom_stats[i] == ref_stats[i]

    # test with category_labels
    import json
    with open(catlabels) as f:
        labels = json.load(f)

    statistics = stats.compute_zonal_stats_per_category(geometries, raster, bands=bands,
                                                        stats=stats_to_compute,
                                                        categories=categories,
                                                        category_index="Classe",
                                                        category_labels=labels)

    # statistics is a list of list of dict.
    # First list iterates over geometries
    # Second list iterates over bands.
    assert len(statistics) == len(geometries.index)
    assert len(statistics[0]) == len(bands)

    # round stats to compare with numerical accuracy
    [d.update({key: round(val, 6)})
     for geom_stats in statistics for d in geom_stats for key, val in d.items()]

    # ref is the following
    ref = [[{'cetemin': 40.407368, 'cetemax': 44.083961, 'cetemean': 42.293813, 'cetecount': 244, 'cetestd': 0.849256,
             'feumin': 40.224247, 'feumax': 68.915146, 'feumean': 46.435982, 'feucount': 12347, 'feustd': 4.744863,
             'conmin': 38.825829, 'conmax': 46.798634, 'conmean': 42.54521, 'concount': 6657, 'constd': 1.33232,
             'udimin': 38.214043, 'udimax': 59.93272, 'udimean': 43.375171, 'udicount': 2716, 'udistd': 1.595453,
             'zicmin': 38.214043, 'zicmax': 45.618088, 'zicmean': 42.273934, 'ziccount': 875, 'zicstd': 1.241663}],
           [{'cetemin': 38.475033, 'cetemax': 45.613518, 'cetemean': 42.386635, 'cetecount': 73437, 'cetestd': 1.090365,
             'chivmin': 39.241253, 'chivmax': 43.433277, 'chivmean': 41.991684, 'chivcount': 17339, 'chivstd': 0.313978,
             'feumin': 33.781662, 'feumax': 60.81406, 'feumean': 44.562402, 'feucount': 12743, 'feustd': 3.051407,
             'conmin': 37.670204, 'conmax': 64.120644, 'conmean': 44.396165, 'concount': 18284, 'constd': 2.749989,
             'udimin': 40.806831, 'udimax': 65.240021, 'udimean': 45.256735, 'udicount': 45240, 'udistd': 3.348138,
             'zicmin': 42.136879, 'zicmax': 65.507011, 'zicmean': 48.296514, 'ziccount': 59113, 'zicstd': 3.671298}]]

    for geom_stats, ref_stats in zip(statistics, ref):
        for i, band in enumerate(bands):
            assert geom_stats[i] == ref_stats[i]
