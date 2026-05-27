#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Functions to compute statistics on raster images.
"""
import os
from typing import List, Dict
import re
import datetime

import numpy as np
from scipy.stats import median_abs_deviation
import pandas as pd
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import rasterio
from rasterio import features
from tqdm import tqdm

from eolab.georastertools.utils import get_metadata_name
from eolab.georastertools.processing.vector import rasterize, filter_dissolve


def compute_zonal_stats(geoms: gpd.GeoDataFrame, image: str,
                        bands: List[int] = [1],
                        stats: List[str] = ["min", "max", "mean", "std"],
                        categorical: bool = False) -> List[List[Dict[str, float]]]:
    """
    Compute zonal statistics for an input raster image over specified geometries.

    This function calculates statistical summaries (e.g., min, max, mean, standard deviation)
    for each feature in the provided geometries (GeoDataFrame) using the specified raster image.
    If the raster is categorical, the function can compute counts of unique values.

    Args:
        geoms (GeoDataFrame):
            A GeoDataFrame containing geometries (e.g., polygons) for which statistics will be computed.
        image (str):
            Path to the raster image file to process.
        bands (List[int], optional):
            A list of raster band indices to process. Defaults to [1] (the first band).
        stats (List[str], optional):
            A list of statistical metrics to compute. Possible values include:
            - "min": Minimum value within the geometry.
            - "max": Maximum value within the geometry.
            - "mean": Mean (average) value within the geometry.
            - "std": Standard deviation within the geometry.
            - Other metrics may be supported based on the implementation of `_compute_stats`.
            Defaults to ["min", "max", "mean", "std"].
        categorical (bool, optional):
            If True, treats the raster as categorical, computing counts of unique values within each geometry.
            Defaults to False.

    Returns:
        List[List[Dict[str, float]]]:
            A nested list where:
            - The outer list corresponds to each geometry in the GeoDataFrame.
            - The inner list corresponds to each band processed.
            - Each dictionary contains the computed statistics, with stat names as keys and their values as values.

    Example:
        ```
        import geopandas as gpd
        from georastertools import compute_zonal_stats

        geoms = gpd.read_file("polygons.shp")
        stats = compute_zonal_stats(geoms, "input_image.tif", bands=[1, 2], stats=["mean", "std"])
        print(stats)
        ```
    """
    nb_geoms = len(geoms)

    with rasterio.open(image) as src:

        geom_gen = (geoms.iloc[i].geometry for i in range(nb_geoms))
        geom_windows = ((geom, features.geometry_window(src, [geom])) for geom in geom_gen)

        statistics = []
        disable = os.getenv("RASTERTOOLS_NOTQDM", 'False').lower() in ['true', '1']
        for geom, window in tqdm(geom_windows, total=nb_geoms, disable=disable, desc="zonalstats"):
            data = src.read(bands, window=window)
            transform = src.window_transform(window)

            s = _compute_stats((data, transform, [geom], window),
                               src.nodata, stats, categorical)
            statistics.append(s)

    return statistics


def compute_zonal_stats_per_category(geoms: gpd.GeoDataFrame, image: str,
                                     bands: List[int] = [1],
                                     stats: List[str] = ["min", "max", "mean", "std"],
                                     categories: gpd.GeoDataFrame = None,
                                     category_index: str = 'Classe',
                                     category_labels: Dict[str, str] = None):
    """
    Compute zonal statistics for an input raster image, categorized by specified subregions.

    This function calculates statistical metrics for a raster image over a set of geometries
    (e.g., polygons) provided in `geoms`. If a set of categories (subregions within each geometry)
    is provided, statistics are computed separately for each category within each geometry.

    Args:
        geoms (GeoDataFrame):
            A GeoDataFrame containing the input geometries (e.g., polygons) to compute
            statistics over.
        image (str):
            The file path to the input raster image.
        bands (List[int], optional):
            A list of raster band indices to process. Defaults to [1] (the first band).
        stats (List[str], optional):
            A list of statistical metrics to compute. Supported values include:
            - "min": Minimum value within the geometry.
            - "max": Maximum value within the geometry.
            - "mean": Mean value within the geometry.
            - "std": Standard deviation within the geometry.
            Defaults to ["min", "max", "mean", "std"].
        categories (GeoDataFrame, optional):
            A GeoDataFrame containing category geometries that define subregions of the
            input geometries. Defaults to None.
        category_index (str, optional):
            The column in the `categories` GeoDataFrame that identifies category labels
            for each geometry. Defaults to 'Classe'.
        category_labels (Dict[str, str], optional):
            A dictionary mapping category values (from `category_index`) to human-readable
            labels. If provided, these labels replace category values in the output.
            Defaults to None.

    Returns:
        List[List[Dict[str, float]]]:
            A nested list of dictionaries containing the computed statistics:
            - Outer list corresponds to each input geometry in `geoms`.
            - Inner list corresponds to each raster band being processed.
            - Each dictionary maps statistic names (e.g., "mean", "max") to their respective values.

    Raises:
        IOError:
            If any input geometry is not of type Polygon or MultiPolygon.

    Notes:
        - For each geometry in `geoms`, the function subdivides it into subregions based
          on the geometries in `categories` (if provided). Statistics are then computed
          for each subregion separately.
        - The function assumes that the raster image is georeferenced and aligned with
          the coordinate system of the input geometries.

    Example:
        ```
        import geopandas as gpd
        from georastertools import compute_zonal_stats_per_category

        geoms = gpd.read_file("regions.shp")
        categories = gpd.read_file("landcover.shp")
        image_path = "satellite_image.tif"

        stats = compute_zonal_stats_per_category(
            geoms=geoms,
            image=image_path,
            categories=categories,
            category_index="Land_Type",
            category_labels={1: "Forest", 2: "Urban", 3: "Water"}
        )

        for geometry_stats in stats:
            print(geometry_stats)
        ```
    """
    def _get_list_of_polygons(geom):
        """Get the list of polygons from the geometry"""
        polygons = None
        if geom.geom_type == 'MultiPolygon':
            polygons = list(geom.geoms)
        elif geom.geom_type == 'Polygon':
            polygons = list([geom])
        else:
            raise IOError('Shape is not a polygon.')
        return polygons

    statistics = []
    # Process geometries one by one
    nb_geoms = len(geoms)
    nb_bands = len(bands)

    with rasterio.open(image) as src:
        # each input geometry is split following the categorical geometries.
        # geom_by_class contains the list of categorical geometries (one list of categorical
        # geometries per input geometry)
        geom_gen = (geoms.iloc[[i]] for i in range(nb_geoms))
        geom_by_class = [filter_dissolve(roi, categories, id=category_index)
                         for roi in geom_gen]

        # Compute the number of categorical geometries for each input geometry
        nb_class_roi = [geom_by_class.shape[0] for geom_by_class in geom_by_class]

        # compute stats prefix
        index_list_roi = [str(el)
                          for geom_by_class in geom_by_class
                          for el in geom_by_class[category_index]]

        # change index_list_roi names if a dict is given
        if category_labels:
            index_list_roi = [category_labels[el] if el in category_labels else el
                              for el in index_list_roi]

        # Generator to creates windows associated with each category
        # geom_window_gen is a generator whose elements are list of geometries per class and per roi
        geom_windows = [(_get_list_of_polygons(geom),
                         features.geometry_window(src, _get_list_of_polygons(geom)))
                        for geom_by_class in geom_by_class
                        for geom in geom_by_class.geometry]

        substats = []
        disable = os.getenv("RASTERTOOLS_NOTQDM", 'False').lower() in ['true', '1']
        for geom_window, stats_prefix in tqdm(zip(geom_windows, index_list_roi),
                                              disable=disable, desc="zonalstats"):
            """Read input raster and compute stats"""
            geom, window = geom_window

            data = src.read(bands, window=window)
            transform = src.window_transform(window)

            s = _compute_stats((data, transform, geom, window),
                               src.nodata, stats, False, stats_prefix)
            substats.append(s)

        offset = 0
        # re-order output so that all stats of catagorical geometries that correspond
        # to the same input geometry are concatenated in the same list
        for i in range(nb_geoms):
            results_roi = [{}] * nb_bands
            [results_roi[u].update(substats[v + offset][u])
             for u in range(nb_bands)
             for v in range(nb_class_roi[i])]
            offset = offset + nb_class_roi[i]
            statistics.append(results_roi)

    return statistics


def extract_zonal_outliers(geoms: gpd.GeoDataFrame, image: str, outliers_image: str,
                           prefix: List[str] = None, bands: List[int] = [1], sigma: float = 2):
    """Extract the outliers of an input image and store the results in a new image where
    all outliers are written with their real values and other pixels are stored with the
    mean value. The outliers are computed for each geometry. The stats mean and std of the
    geometries shall have been computed by the function compute_zonal_stats.

    Args:
        geoms (GeoDataFrame):
            Geometries that contain as metadata the statistics (at least the mean and std)
        image (str):
            Filename of the input image to process
        outliers_image (str):
            Filename of the ioutput image
        prefix ([str]):
            Add a prefix to the stats keys. Must have the same size as bands
        bands ([int], optional, default=[1]):
            List of bands to process in the input image
        sigma (float, optional, default=2):
            Distance (in sigma) to the mean value to consider a point as an outlier
    """
    for i, band in enumerate(bands):
        mean_attr = get_metadata_name(band, prefix[i], "mean")
        std_attr = get_metadata_name(band, prefix[i], "std")
        geoms = geoms[~np.isnan(geoms[mean_attr])]
        geoms = geoms[~np.isnan(geoms[std_attr])]

        with rasterio.open(image) as dataset:
            profile = dataset.profile
            data = dataset.read(band, masked=True)

            with rasterio.open(outliers_image, "w", **profile) as output:
                # rasterisation du mean et du std
                mean = rasterize(geoms, image, burn=mean_attr, burn_type=rasterio.float32,
                                 nodata=dataset.nodata)  # , output=image[:-4] + "-mean.tif")
                std = rasterize(geoms, image, burn=std_attr, burn_type=rasterio.float32,
                                nodata=dataset.nodata)  # , output=image[:-4] + "-std.tif")

                outliers = np.logical_and(mean > -1,
                                          np.logical_or(data <= mean - float(sigma) * std,
                                                        data >= mean + float(sigma) * std))

                mean[outliers] = data[outliers]
                output.write_band(band, mean)


def plot_stats(chartfile: str, stats_per_date: Dict[datetime.datetime, gpd.GeoDataFrame],
               stats: List[str] = ["min", "max", "mean", "std"],
               index_name: str = 'ID', display: bool = False):
    """
    Plot temporal statistics for geometries across multiple dates.

    This function visualizes the evolution of specified statistics (e.g., "min", "mean")
    over time for different zones defined in the input GeoDataFrames. The output is
    saved as a chart file, and optionally displayed.

    Args:
        chartfile (str):
            Path to the file where the generated chart will be saved.
        stats_per_date (Dict[datetime.datetime, gpd.GeoDataFrame]):
            A dictionary mapping each date to a GeoDataFrame containing the statistics
            for that date. Each GeoDataFrame should include the specified `index_name`
            column and relevant statistics columns.
        stats (List[str], optional):
            A list of statistics to plot (e.g., "min", "max", "mean", "std"). Defaults
            to ["min", "max", "mean", "std"].
        index_name (str, optional):
            Name of the column in the GeoDataFrames that uniquely identifies the zones
            (e.g., region IDs). Defaults to 'ID'.
        display (bool, optional):
            If `True`, the generated plot is displayed after saving. Defaults to `False`.

    Raises:
        ValueError:
            If the specified `index_name` is not present in the combined GeoDataFrame.

    Notes:
        - The `stats_per_date` dictionary must be ordered or sortable by date to ensure
          proper time-series plotting.
        - Each GeoDataFrame in `stats_per_date` should have columns named in the format
          `<prefix>.<stat>` (e.g., "temperature.mean").

    Example:
        ```
        import geopandas as gpd
        import datetime
        from plot_tools import plot_stats

        # Example input
        stats_per_date = {
            datetime.datetime(2023, 1, 1): gpd.GeoDataFrame({...}),
            datetime.datetime(2023, 2, 1): gpd.GeoDataFrame({...}),
        }

        plot_stats(
            chartfile="output_chart.png",
            stats_per_date=stats_per_date,
            stats=["mean", "std"],
            index_name="RegionID",
            display=True
        )
        ```

    Output:
        - Saves a time-series plot of the specified statistics as `chartfile`.
        - Optionally displays the plot if `display=True`.
    """

    # convert dates to datenumber format
    sorted_dates = sorted(stats_per_date.keys())
    x = np.array([matplotlib.dates.date2num(date) for date in sorted_dates])

    all_stats = pd.concat([stats_per_date[date] for date in sorted_dates], ignore_index=True)
    if index_name not in all_stats.columns:
        raise ValueError(f"Index '{index_name}' is not present in the geometries. "
                         "Please provide a valid value for -gi option.")
    zones = all_stats[index_name].unique()

    # extract the prefixes present in the stats
    prefix_pattern = re.compile("(.+)\\.name")
    prefixes = []
    for col in all_stats.columns:
        m = prefix_pattern.match(col)
        if m:
            prefixes.append(m.group(1))

    fignum = 1
    lines = []
    for i, prefix in enumerate(prefixes):
        for stat in stats:
            plt.subplot(len(prefixes), len(stats), fignum)
            stat_name = get_metadata_name(-1, prefix, stat)

            for zone in zones:
                y = np.array(all_stats.loc[all_stats[index_name] == zone][stat_name])
                line, = plt.plot_date(x, y, '-')
                lines.append(line)

            plt.title(stat_name)
            fignum = fignum + 1

    plt.xlabel('date')
    plt.ylabel('values')

    plt.figlegend(lines, zones, loc='lower center', ncol=2, fancybox=True, shadow=True)
    plt.savefig(chartfile, bbox_inches='tight')
    if display:
        plt.show()


def _compute_stats(pack, nodata, stats: List[str] = None,
                   categorical: bool = False, prefix_stats: str = ""):
    """Compute the statistics.

    Args:
        pack:
            A quadruplet containing an array of data (1 per band), the geo transform, the geometry
            where to compute stats, and the window corresponding to the geometry
        nodata:
            The value that corresponds to nodata
        stats:
            The list of stats to compute
        categorical:
            Whether to consider the input raster as categorical
        prefix_stats:
            A prefix to name the stats

    Returns:
        A list of statistics (one item per band). Statistics are provided as a dict that associates
        the stats names and the stats values.
    """
    datas, transform, geom, window = pack

    # prepare the mask to apply to input dataset: any pixel outside the geom shall be masked
    all_geoms = [(g, 1) for g in geom]
    mask = features.rasterize(shapes=all_geoms,
                              fill=0, out_shape=rasterio.windows.shape(window),
                              transform=transform,
                              dtype=rasterio.uint8).astype(bool)

    # list of stats computed, one item per band
    all_stats = []
    # for every bands
    for data in datas:
        # create the dataset on which stats will be computed
        if nodata and np.isnan(nodata):
            dataset = np.ma.MaskedArray(data, mask=(np.isnan(data) | ~mask))
        else:
            dataset = np.ma.MaskedArray(data, mask=((data == nodata) | ~mask))

        count = dataset.count()
        if count == 0:
            # nothing here, fill with None and move on
            feature_stats = dict([(stat, None) for stat in stats])
        else:
            # generate the statistics
            feature_stats = _gen_stats(dataset, stats, categorical, prefix_stats)
            # generate the categorical statistics
            feature_stats.update(_gen_stats_cat(dataset, stats, categorical, prefix_stats))

        # generate the counting stats
        if "count" in stats:
            feature_stats[f'{prefix_stats}count'] = count
        if 'valid' in stats or 'nodata' in stats:
            all_count = np.count_nonzero(mask)
            if 'nodata' in stats:
                feature_stats[f'{prefix_stats}nodata'] = all_count - count
            if 'valid' in stats:
                valid = 1.0 * count / (all_count + 1e-5)
                feature_stats[f'{prefix_stats}valid'] = valid

        # append the generated stats to the structure that contains the stats for all bands
        all_stats.append(feature_stats)
    return all_stats


def _gen_stats(dataset, stats: List[str] = None,
               categorical: bool = False, prefix_stats: str = ""):
    """Generates the statistics

    Args:
        dataset:
            The dataset (numpy MaskedArray) from which stats are computed
        stats:
            The stats to compute
        categorical:
            Whether to consider the input raster as categorical
        prefix_stats:
            A prefix to name the stats

    Returns:
        The list of statistics for the input dataset as a dict that associates the
        stats names and the stats values.

    """
    feature_stats = dict()

    # compute stats
    # we force dtype to float64 to avoid precision errors
    functions = {
        'min': {'function': np.ma.min, 'options': {}},
        'max': {'function': np.ma.max, 'options': {}},
        'mean': {'function': np.ma.mean, 'options': {"dtype": np.float64}},
        'sum': {'function': np.ma.sum, 'options': {"dtype": np.float64}},
        'std': {'function': np.ma.std, 'options': {"dtype": np.float64}},
        'median': {'function': np.ma.median, 'options': {}},
    }

    for key, key_content in functions.items():
        if key in stats:
            function = key_content["function"]
            feature_stats[f'{prefix_stats}{key}'] = float(function(dataset, **key_content["options"]))

    if 'range' in stats:
        min_key = f'{prefix_stats}min'
        rmin = feature_stats[min_key] if min_key in feature_stats.keys() else float(dataset.min())
        max_key = f'{prefix_stats}max'
        rmax = feature_stats[max_key] if max_key in feature_stats.keys() else float(dataset.max())
        feature_stats[f'{prefix_stats}range'] = rmax - rmin

    # compute percentiles on the compressed dataset (i.e. the numpy array without the masked values)
    # because np.ma has no percentile computation capabilities
    dataset_com = dataset.compressed()
    for pctile in [s for s in stats if s.startswith('percentile_')]:
        q = np.float64(pctile.replace("percentile_", ''))
        feature_stats[f'{prefix_stats}{pctile}'] = np.percentile(dataset_com, q)
    if 'mad' in stats:
        feature_stats[f'{prefix_stats}mad'] = median_abs_deviation(dataset_com.flatten())

    return feature_stats


def _gen_stats_cat(dataset, stats: List[str] = None,
                   categorical: bool = False, prefix_stats: str = ""):
    """Generates the statistics

    Args:
        dataset:
            The dataset (numpy MaskedArray) from which stats are computed
        stats:
            The stats to compute
        categorical:
            Whether to consider the input raster as categorical
        prefix_stats:
            A prefix to name the stats

    Returns:
        The list of statistics for the input dataset as a dict that associates the
        stats names and the stats values.

    """

    # if categorical stats is requested, extract all unique values from the dataset
    if categorical or 'majority' in stats or 'minority' in stats or 'unique' in stats:
        keys, counts = np.unique(dataset.compressed(), return_counts=True)
        # pixel_count is a dict that associates a unique value with the number
        # of occurrences in the dataset
        pixel_count = dict(zip([k.item() for k in keys],
                               [c.item() for c in counts]))

    # initialize the feature_stats dict
    feature_stats = dict(pixel_count) if categorical else {}

    def _key_assoc_val(d, func, exclude=None):
        """return the key associated with the value returned by func
        """
        vs = list(d.values())
        ks = list(d.keys())
        key = ks[vs.index(func(vs))]
        return key

    if 'majority' in stats:
        feature_stats[f'{prefix_stats}majority'] = float(_key_assoc_val(pixel_count, max))
    if 'minority' in stats:
        feature_stats[f'{prefix_stats}minority'] = float(_key_assoc_val(pixel_count, min))
    if 'unique' in stats:
        feature_stats[f'{prefix_stats}unique'] = len(list(pixel_count.keys()))

    return feature_stats
