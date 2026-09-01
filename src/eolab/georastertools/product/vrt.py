#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utilities to handle vrt image format
"""
from typing import Union, List
import xml.etree.ElementTree as ET
from pathlib import Path

from osgeo import gdal
import numpy as np

__author__ = "Olivier Queyrut"
__copyright__ = "Copyright 2019, CNES"
__license__ = "Apache v2.0"


def _file2vrt(xml_element, file: str, bands: List[int]):
    """Adds a simple source to the vrt.

    Args:
        xml_element:
            Parent XML element that will contains the function definition
        file:
            Raster file that contains the bands used as masks
        bands (int):
            Bands of the raster image to use as masks
    """
    fh = gdal.Open(file)
    if fh is not None:
        for band in bands:
            rasterband = fh.GetRasterBand(band)
            if rasterband is not None:
                data_type_name = gdal.GetDataTypeName(rasterband.DataType)
                block_size_x, block_size_y = rasterband.GetBlockSize()

                # add a source
                simplesource = ET.SubElement(xml_element, "SimpleSource")

                sourcefilename = ET.SubElement(simplesource, "SourceFilename")
                sourcefilename.attrib["relativeToVRT"] = '1'
                sourcefilename.text = Path(file).name

                sourceband = ET.SubElement(simplesource, "SourceBand")
                sourceband.text = str(band)

                # set the source properties with metadata from input raster
                sourceprops = ET.SubElement(simplesource, "SourceProperties")
                sourceprops.attrib["RasterXSize"] = str(fh.RasterXSize)
                sourceprops.attrib["RasterYSize"] = str(fh.RasterYSize)
                sourceprops.attrib["DataType"] = data_type_name
                sourceprops.attrib["BlockXSize"] = str(block_size_x)
                sourceprops.attrib["BlockYSize"] = str(block_size_y)

                # set the source shape with the shape of the input raster
                srcrect = ET.SubElement(simplesource, "SrcRect")
                srcrect.attrib["xOff"] = "0"
                srcrect.attrib["yOff"] = "0"
                srcrect.attrib["xSize"] = str(fh.RasterXSize)
                srcrect.attrib["ySize"] = str(fh.RasterYSize)

                # set the dest shape the same way
                dstrect = ET.SubElement(simplesource, "DstRect")
                dstrect.attrib["xOff"] = "0"
                dstrect.attrib["yOff"] = "0"
                dstrect.attrib["xSize"] = str(fh.RasterXSize)
                dstrect.attrib["ySize"] = str(fh.RasterYSize)

    # free gdal resource
    del fh


def _func2vrt(xml_element, funcname: str, funcdef: str = None):
    """Adds a pixel function to the vrt.

    Args:
        xml_element:
            Parent XML element that will contains the function definition
        funcname (str):
            Fully qualified name of the function (e.g. indices.vrt.s2_maja_mask)
        funcdef (str, optional, default=None):
            Function definition (without its signature). If None, the function funcname
            must be available in the scope
    """
    # Name of the pixel function
    pixelfunctiontype = ET.SubElement(xml_element, "PixelFunctionType")
    pixelfunctiontype.text = funcname

    # Language of the pixel function
    pixelfunctionlang = ET.SubElement(xml_element, "PixelFunctionLanguage")
    pixelfunctionlang.text = "Python"

    # Definition of the pixel function
    if funcdef is not None:
        code = f'<PixelFunctionCode><![CDATA[\n\
            import numpy as np\n\
            def {funcname}(in_ar, out_ar, xoff, yoff, xsize, ysize,\
                           raster_xsize, raster_ysize, buf_radius, gt, **kwargs):\
                {funcdef}\n\
            ]]></PixelFunctionCode>'
        pixelfunctioncode = ET.fromstring(code)
        xml_element.append(pixelfunctioncode)


def add_masks_to_vrt(src_vrt: Union[Path, str], maskfile: Union[Path, str], bands: List[int] = [1],
                     funcname: str = None, funcdef: str = None):
    """Adds a mask bands to the vrt.

    Args:
        src_vrt (pathlib.Path or str):
            Vrt input image
        maskfile (pathlib.Path or str):
            Input image that contains the bands to use as masks
        bands ([int]):
            Bands in the the input image to use as masks
        funcname (str, optional, default=None):
            Fully qualified name of the pixel function (e.g. indices.vrt.s2_maja_mask)
            used to compute the mask from the maskfile dataset.
        funcdef (str, optional, default=None):
            Function definition (without its signature). If None, the function funcname
            must be available in the scope
    """
    svrt = src_vrt.as_posix() if isinstance(src_vrt, Path) else src_vrt
    mask = maskfile.as_posix() if isinstance(maskfile, Path) else maskfile

    with open(svrt) as vrtContent:
        tree = ET.parse(vrtContent)
        root = tree.getroot()
        vrtmaskband = ET.SubElement(root, 'MaskBand')
        vrtrasterband = ET.SubElement(vrtmaskband, "VRTRasterBand")
        vrtrasterband.attrib["dataType"] = "Byte"
        vrtrasterband.attrib["subClass"] = "VRTDerivedRasterBand"
        if funcname is not None:
            _func2vrt(vrtrasterband, funcname, funcdef)
        _file2vrt(vrtrasterband, mask, bands)

    tree.write(svrt)


def set_band_descriptions(src_vrt: Union[Path, str], descriptions: List[str]):
    """Set the descriptions of the bands in a VRT image.

    Args:
        src_vrt (pathlib.Path or str):
            VRT input image
        descriptions ([str]):
            Descriptions of the bands
    """
    ds = gdal.Open(src_vrt.as_posix() if isinstance(src_vrt, Path) else src_vrt, gdal.GA_Update)
    for i, desc in enumerate(descriptions, 1):
        rb = ds.GetRasterBand(i)
        # if the band exists at the given position, set the description
        if rb is not None:
            rb.SetDescription(desc)
    # free gdal resource
    del ds
