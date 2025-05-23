#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a rastertool named Hillshade which computes the hillshade
of a Digital Elevation Model corresponding to a given solar position (elevation and azimuth).
"""
import logging.config
from typing import List
from pathlib import Path
import numpy as np

import rasterio
from rasterio.windows import Window

from eolab.georastertools import utils
from eolab.georastertools import Rastertool, Windowable
from eolab.georastertools.processing import algo
from eolab.georastertools.processing import RasterProcessing, compute_sliding


_logger = logging.getLogger(__name__)


class Hillshade(Rastertool, Windowable):
    """Raster tool that computes the hillshades of a Digital Elevation / Surface / Height Model
    corresponding to a given solar position.

    The input image is a raster that contains the height of the points as pixel values.

    At a given position p, the Hillshade tool check if the point is in the hillshade generated by
    any other points in the direction of the sun. To achieve this goal, the algorithm computes the
    angle :math:`\\gamma`: :math:`\\tan \\frac{Height}{Distance}`::

                          _____
                        x|     |  ^
                    x    |     |  | Height (from Digital Model)
               x   __    |     |  |
      ____p_______|  |___|     |__v____________
          <-------------->
              Distance

    The point is in the hillshade of another one if :math:`\\gamma < elevation_{sun}`.
    To avoid testing too many points, the "radius" parameter defines the max distance of the pixel
    to test. The radius can be set by the user or automatically computed by the Hillshade tool. In
    this latter case, the radius is :math:`\\frac{\\Delta h}{\\tan{elevation_{sun}}}` where
    :math:`\\Delta h` is :math:`max - min` of the pixel values in the input raster.

    The output image is a mask where pixels corresponding to hillshades equal to 1.
    """

    def __init__(self, elevation: float, azimuth: float, resolution: float, radius: int = None):
        """ Constructor for the Hillshade class.

        Args:
            elevation (float):
                Elevation of the sun (in degrees), 0 is vertical top (zenith).
            azimuth (float):
                Azimuth of the sun (in degrees), measured clockwise from north.
            resolution (float):
                Resolution of a raster pixel (in meters).
            radius (int, optional):
                Maximum distance from the current point (in pixels) to consider
                for evaluating the hillshade. If None, the radius is calculated
                based on the data range.
        """
        super().__init__()
        self.with_windows()

        self._elevation = elevation
        self._azimuth = azimuth
        self._resolution = resolution
        self._radius = radius

    @property
    def elevation(self):
        """Return the elevation of the sun (in degrees)"""
        return self._elevation

    @property
    def azimuth(self):
        """Return the azimuth of the sun (in degrees)"""
        return self._azimuth

    @property
    def resolution(self):
        """Return the resolution of a raster pixel (in meter)"""
        return self._resolution

    @property
    def radius(self):
        """Return the maximum distance from current point (in pixels)
        for evaluating the maximum elevation angle"""
        return self._radius

    def process_file(self, inputfile: str) -> List[str]:
        """
        Compute hillshade for the input file.

        Args:
            inputfile (str):
                Input image file path to process.

        Returns:
            List[str]: A list containing the file path of the generated hillshade image.

        Raises:
            ValueError: If the input file contains more than one band or if the radius exceeds constraints.
        """
        _logger.info(f"Processing file {inputfile}")
        outdir = Path(self.outputdir)
        output_image = outdir.joinpath(f"{utils.get_basename(inputfile)}-hillshade.tif")

        # compute the radius from data range
        # radius represents the max distance of buildings that can create a hillshade
        # considering the sun elevation.
        wmin, wmax = np.inf, -np.inf
        with rasterio.open(inputfile) as src:
            if src.count != 1:
                raise ValueError("Invalid input file, it must contain a single band.")
            for i in range(src.height // self.window_size[0]  + 1):
                for j in range(src.width // self.window_size[1]  + 1):
                    # Oversized window (out of source bounds) is handled by Window
                    win = Window(i*self.window_size[0] , j*self.window_size[1] , self.window_size[0] , self.window_size[1])
                    # Read masked array (masks are the exact inverse of GDAL RFC 15 conforming masks)
                    data = src.read(1, masked=True, window=win)
                    # mask potential NaN not covered by DatasetReader.read
                    np.ma.masked_invalid(data, copy=False)
                    if data.size and not data.mask.all():
                        wmax = np.maximum(wmax, data.max())
                        wmin = np.minimum(wmin, data.min())
        
        if wmin is np.inf:
            # No valid data in input DEM
            raise ValueError(f"No valid data in file: {inputfile}")
        
        delta = int((wmax - wmin) / self.resolution)
        optimal_radius = abs(int(delta / np.tan(np.radians(self.elevation))))

        if self.radius is None or optimal_radius <= self.radius:
            self._radius = optimal_radius
            _logger.info(f"Using optimal radius {self.radius} for hillshade computation")
        else:
            _logger.warning(f"The optimal radius value is {optimal_radius} exceeding {self.radius} threshold. "
                            f"Oversized radius affects computation time and so radius is set to {self.radius}. "
                            "Result may miss some shadow pixels.")

        if self.radius >= min(self.window_size) / 2:
            raise ValueError(f"The radius (option --radius, value={self.radius}) must be strictly "
                             "less than half the size of the window (option --window_size, "
                             f"value={min(self.window_size)})")

        # Configure the processing
        hillshade = RasterProcessing(
            "hillshade",
            algo=algo.hillshade,
            nodata=255,
            dtype=np.uint8,
            in_dtype=np.float32,
            nbits=1,
            compress="lzw",
            per_band_algo=True,
        )
        hillshade.with_arguments({
            "elevation": None,
            "azimuth": None,
            "resolution": None,
            "radius": None
        })
        # set the configuration of the raster processing
        hillshade_conf = {
            "elevation": self.elevation,
            "azimuth": self.azimuth,
            "resolution": self.resolution,
            "radius": self.radius
        }
        hillshade.configure(hillshade_conf)

        # Run the hillshade processing
        compute_sliding(
            inputfile, output_image, hillshade,
            window_size=self.window_size,
            window_overlap=self.radius,
            pad_mode=self.pad_mode)

        return [output_image.as_posix()]
