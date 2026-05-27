#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Algorithms on raster data
"""
import math

import numpy
import numpy as np
import numpy.ma as ma
from scipy import ndimage, signal


def normalized_difference(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Normalized Difference Vegetation Index
    The coefficient ranges from -1 to 1 in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        NDVI = \\frac{NIR - RED}{NIR + RED}

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed TNDVI.
    """
    np.seterr(divide='ignore')
    return (bands[1] - bands[0]) / (bands[1] + bands[0])


def tndvi(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Transformed Normalized Difference Vegetation Index
    The coefficient is positive in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        TNDVI = \\sqrt{NDVI + 0.5}

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed TNDVI.

    References:
        `Deering D.W., Rouse J.W., Haas R.H., and Schell J.A., 1975. Measuring forage production
        of grazing units from Landsat MSS data. Pages 1169-1178 In: Cook J.J. (Ed.), Proceedings
        of the Tenth International Symposium on Remote Sensing of Environment (Ann Arbor, 1975),
        Vol. 2, Ann Arbor, Michigan, USA. <https://www.scirp.org/reference/referencespapers?referenceid=1046714>`_
    """
    np.seterr(invalid='ignore')
    ratio = normalized_difference(bands) + 0.5
    ratio[ratio < 0] = 0
    return np.sqrt(ratio)


def rvi(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Ratio Vegetation Index
    The coefficient is positive in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        PVI = \\frac{NIR}{RED}

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed RVI.

    References:
        `Jordan C.F., 1969. Derivation of leaf area index from quality of light on the forest
        floor. Ecology 50:663-666 <https://esajournals.onlinelibrary.wiley.com/doi/10.2307/1936256>`_
    """
    np.seterr(divide='ignore')
    return bands[1] / bands[0]


def pvi(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Perpendicular Vegetation Index
    The coefficient ranges from -1 to 1 in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        PVI = 0.74 (NIR - 0.90893 RED - 7.46216)

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed PVI.

    References:
        `Richardson A.J., Wiegand C.L., 1977. Distinguishing vegetation from soil background
        information. Photogramm Eng Rem S 43-1541-1552 <https://www.asprs.org/wp-content/uploads/pers/1977journal/dec/1977_dec_1541-1552.pdf>`_
    """
    return (bands[1] - 0.90893 * bands[0] - 7.46216) * 0.74


def savi(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Soil Adjusted Vegetation Index
    The coefficient ranges from -1 to 1 in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        SAVI = \\frac{(NIR - RED) (1 + 0.5)}{NIR + RED + 0.5}

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed SAVI.

    References:
        `Huete A.R., 1988. A soil-adjusted vegetation index (SAVI). Remote Sens Environ 25:295-309 <https://www.sciencedirect.com/science/article/abs/pii/003442578890106X>`_
    """
    np.seterr(divide='ignore')
    return (1. + 0.5) * (bands[1] - bands[0]) / (bands[1] + bands[0] + 0.5)


def tsavi(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Transformed Soil Adjusted Vegetation Index
    The coefficient ranges from -1 to 1 in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        TSAVI = \\frac{0.7 (NIR - 0.7 RED - 0.9)}{0.7 NIR + RED + 0.08 (1 + 0.7^2)}

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed TSAVI.

    References:
        `Baret F., Guyot G., Major D., 1989. TSAVI: a vegetation index which minimizes soil
        brightness effects on LAI or APAR estimation. 12th Canadian Symposium on Remote
        Sensing and IGARSS 1990, Vancouver, Canada, 07/10-14. <https://www.researchgate.net/publication/3679422_TSAVI_A_vegetation_index_which_minimizes_soil_brightness_effects_on_LAI_and_APAR_estimation>`_
    """
    np.seterr(divide='ignore')
    denominator = 0.7 * bands[1] + bands[0] + 0.08 * (1 + 0.7 * 0.7)
    numerator = 0.7 * (bands[1] - 0.7 * bands[0] - 0.9)
    return numerator / denominator


def _wdvi(bands : numpy.ndarray) -> numpy.ndarray :
    """
    Compute the Weighted Difference Vegetation Index of the input data.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        WDVI = NIR - 0.4 RED

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed WDVI.
    """
    return bands[1] - 0.4 * bands[0]


def msavi(bands : numpy.ndarray) -> numpy.ndarray :
    """
    Compute the Modified Soil Adjusted Vegetation Index of the input data.
    The coefficient ranges from -1 to 1 in each pixel.

    grdtbrbr The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        MSAVI = \\frac{(NIR - RED) (1 + L)} {NIR + RED + L} \\\\

    With : :math:`L = 1 - 2 * 0.4 * NDVI * WDVI`

    Parameters
    ----------
    input_data : np.ndarray
        A 3D numpy array of shape (number of bands, number of lines, number of columns) where number of bands > 1.

    Returns
    -------
    np.ndarray
        A 2D numpy array of shape (number of lines, number of columns) containing the computed MSAVI values.

    References
    -------
        `Qi J., Chehbouni A., Huete A.R., Kerr Y.H., 1994. Modified Soil Adjusted Vegetation
        Index (MSAVI). Remote Sens Environ 48:119-126 <https://www.researchgate.net/publication/223906415_A_Modified_Soil_Adjusted_Vegetation_Index>`_

        `Qi J., Kerr Y., Chehbouni A., 1994. External factor consideration in vegetation index
        development. Proc. of Physical Measurements and Signatures in Remote Sensing,
        ISPRS, 723-730. <https://www.academia.edu/20596726/External_factor_consideration_in_vegetation_index_development>`_
    """
    np.seterr(divide='ignore')
    ndvi = normalized_difference(bands)
    wdvi = _wdvi(bands)
    dl = 1 - 2 * 0.4 * ndvi * wdvi
    denominator = bands[1] + bands[0] + dl
    return (1 + dl) * (bands[1] - bands[0]) / denominator


def msavi2(bands : numpy.ndarray) -> numpy.ndarray :
    """
    Compute the Modified Soil Adjusted Vegetation Index of the input data.
    The coefficient ranges from -1 to 1 in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        MSAVI2 = (2 * NIR + 1)^2 - 8 (NIR - RED)

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed MSAVI.
    """
    np.seterr(divide='ignore', invalid='ignore')
    dsqrt = (2. * bands[1] + 1) ** 2 - 8 * (bands[1] - bands[0])
    return (2. * bands[1] + 1) - np.sqrt(dsqrt)


def ipvi(bands : numpy.ndarray) -> numpy.ndarray :
    """
    Compute the Infrared Percentage Vegetation Index of the input data.
    The coefficient ranges from 0 to 1 in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red).

    .. math::
        IPVI = \\frac{NIR}{NIR + RED}

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of size (number of lines, number of columns) containing the computed IPVI.

    References:
        `Crippen, R. E. 1990. Calculating the Vegetation Index Faster, Remote Sensing of
        Environment, vol 34., pp. 71-73. <https://www.sciencedirect.com/science/article/abs/pii/003442579090085Z>`_
    """
    np.seterr(divide='ignore')
    return bands[1] / (bands[1] + bands[0])


def evi(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Enhanced vegetation index of the input data.
    The coefficient ranges from -1 to 1 in each pixel.

    The function considers the bands of the input data in the following order :
    Red, NIR (Near Infra-Red), Blue.

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 2.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed EVI.

    .. math::
        EVI = \\frac{G (NIR - RED)} {NIR + C1 * RED - C2 * BLUE + L}

    With :
        - $L$ : Canopy background adjustment term, it reduces the influence of soil brightness.
        - $C1$, $C2$ : Coefficients that correct the influence of aerosol.
        - $G$ : A gain factor. The greater is G, the more the EVI is sensitive to vegetation changes.
    """
    np.seterr(divide='ignore') #Ignore divisions by zero
    return 2.5 * (bands[1] - bands[0]) / ((bands[1] + 6.0 * bands[0] - 7.5 * bands[2]) + 1.0)


def redness_index(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Redness Index of the input data.

    .. math::
        RI = \\frac{RED^2} {GREEN^3}

    The function considers the bands of the input data in the following order :
    Red, Green.

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of size (number of lines, number of columns) containing the computed Redness Index.
    """
    np.seterr(divide='ignore')
    return bands[0] ** 2 / bands[1] ** 3


def brightness_index(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Brightness Index of the input data.

    The function considers the first 2 bands of the input data to be Red and Green.

    .. math::
        BI = \\sqrt{ \\frac{RED^2 + GREEN^2} {2} }

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 1.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed Brightness Index.
    """
    np.seterr(invalid='ignore')
    bi = (bands[0] ** 2 + bands[1] ** 2) / 2
    return np.sqrt(bi)


def brightness_index2(bands : np.ndarray) -> numpy.ndarray :
    """
    Compute the Brightness Index of the input data.

    The function considers the first 3 bands of the input data to be Red, Green, Blue.

    .. math::
        BI = \\sqrt{ \\frac{RED^2 + BLUE^2 + GREEN^2} {2} }

    Args:
        input_data (np.ndarray) : Numpy array of 3 dimensions (number of bands, number of lines, number of columns)
                    with number of bands > 2.

    Returns:
        Numpy array of the size (number of lines, number of columns) containing the computed Brightness Index.
    """
    np.seterr(invalid='ignore')
    bi2 = (bands[0] ** 2 + bands[1] ** 2 + bands[2] ** 2) / 3
    return np.sqrt(bi2)


def speed(data0 : np.ndarray, data1 : np.ndarray, interval : float) -> numpy.ndarray :
    """
    Compute the speed of the input data based on the difference between two time points.

    Args:
        data0 (numpy.ndarray): Numpy array containing the band value(s) at the first date.
                               Shape must be (number_of_lines, number_of_columns).

        data1 (numpy.ndarray): Numpy array containing the band value(s) at the second date.
                               Shape must match `data0`.

        interval (float): Time interval (in the same units as the timestamps of the input data)
                          between the first and second dates.

    Returns:
        numpy.ndarray: Numpy array of shape (number_of_lines, number_of_columns)
                       containing the computed speed of the sequence. The values represent
                       the change in band values per unit time.

    Raises:
        ValueError: If `data0` and `data1` do not have the same shape, or if `interval` is zero.
    """
    return (data1 - data0) / interval


def interpolated_timeseries(dates : numpy.ma.masked_array, series : numpy.ma.masked_array, output_dates : numpy.array, nodata) -> numpy.ndarray:
    """
    Interpolate a timeseries of data. Dates and series must be sorted in ascending order.

    Args:
        dates (numpy.ma.masked_array): A masked array of timestamps (dates) corresponding to
                                        the input series. Should be in ascending order.

        series (numpy.ma.masked_array): A list of 3D masked arrays, each with shape
                                         (bands, height, width), containing the raster data
                                         for each timestamp in `dates`.

        output_dates (numpy.array): A 1D array of timestamps for which to generate the interpolated
                                     rasters.

        nodata (float): Value to use for pixels where input data is NaN or missing.

    Returns:
        numpy.ndarray: A 4D numpy array of shape (time, bands, height, width), containing
                       the interpolated raster data for each output date. If there are no valid
                       data points for a specific pixel, the corresponding pixel will be filled with `nodata`.

    Raises:
        ValueError: If `series` is empty, or if `dates` and `series` dimensions do not match.
    """
    #Create stack, an array of dimension time x band x height x width from a list of band x height x width arrays
    stack = ma.stack(series)
    stack_shape = stack.shape
    # flatten the stacked data: shape is pixel x time
    pixel_series = stack.transpose((1, 2, 3, 0)).reshape(
        stack_shape[1] * stack_shape[2] * stack_shape[3], -1)

    output = []
    for serie in pixel_series:
        compressed = serie.compressed()
        if serie.count() > 1:
            output.append(np.interp(
                output_dates,
                ma.masked_array(dates, serie.mask).compressed(),
                compressed,
                compressed[0],
                compressed[-1]))
        else:
            default_val = serie.sum() if serie.count() > 0 else nodata
            output.append([default_val] * len(output_dates))

    output = np.array(output)
    return output.transpose(1, 0).reshape(
        -1, stack_shape[1], stack_shape[2], stack_shape[3])


def _local_sum(data : np.ndarray, kernel_width: int) -> numpy.ndarray :
    """
    Computes the local sums of the input data using a sliding window defined by the kernel size.
    Each element in the output is the sum of the pixels within the specified kernel size window.

    Args:
        input_data (np.ndarray): A 3D numpy array of shape (1, number_of_lines, number_of_columns)
                                 containing the Digital Elevation Model (DEM).
                                 The function only accepts arrays with one band.

        kernel_size (int): The size of the sliding window used to compute the local sum.

    If kernel_size = 1 : The output array equals to the input
    Otherwise : Sums the pixels belonging to a sliding window of size radius * radius (with radius = (kernel_width + 1) // 2)
                The top-left pixel of the window is the current pixel

    Returns:
        Numpy array of the size of input_data containing the computed local sums. Computed data have a size minored by the kernel_size
        and are centered in the output shape.

    Raises:
        ValueError: If `input_data` does not have 3 dimensions or if the first dimension is not of size 1.
    """
    if kernel_width == 1:
        output = data.copy()
    else:
        # special case: size = 1 ==> returns data
        if np.issubdtype(data.dtype, np.floating):
            ii_dtype = np.float64
        elif np.issubdtype(data.dtype, np.int32):
            ii_dtype = np.int64
        else:
            ii_dtype = data.dtype

        # create the integral image
        line_cumsum = np.nancumsum(data, axis=data.ndim - 1, dtype=ii_dtype)
        ii = np.nancumsum(line_cumsum, axis=data.ndim - 2)

        # if input data is a masked array, ii is a masked array
        if hasattr(ii, 'mask'):
            # get the data of the masked array
            ii = ii.data

        # compute local sum at each pixel from integral image
        output = np.zeros(data.shape, dtype=ii.dtype)
        posd = (kernel_width + 1) // 2
        posf = kernel_width - posd
        if data.ndim == 3:
            output[:, posd:-posf, posd:-posf] = ii[:, :-kernel_width, :-kernel_width] \
                + ii[:, kernel_width:, kernel_width:] \
                - ii[:, :-kernel_width, kernel_width:] \
                - ii[:, kernel_width:, :-kernel_width]
        else:
            output[posd:-posf, posd:-posf] = ii[:-kernel_width, :-kernel_width] \
                + ii[kernel_width:, kernel_width:] \
                - ii[:-kernel_width, kernel_width:] \
                - ii[kernel_width:, :-kernel_width]

    return output.astype(data.dtype)


def median(input_data : np.ndarray, kernel_size : int) -> numpy.ndarray :
    """
    Applies a Median Filter to the input data using `scipy.ndimage.median_filter <https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.median_filter.html>`_.
    The filter computes the median of the values contained within a sliding window determined by the kernel size.

    Args:
        input_data (np.ndarray): A 3D numpy array of shape (1, number_of_lines, number_of_columns)
                                 containing the Digital Elevation Model (DEM). The function only accepts arrays with one band.

        kernel_size (int): The size of the sliding window (kernel) used to compute the median.

    Returns:
        np.ndarray: A numpy array of the same shape as `input_data`, containing the filtered data with the median values computed in the specified kernel.

    Raises:
        ValueError: If `input_data` does not have 3 dimensions or if the first dimension is not of size 1,
                    or if `kernel_size` is not a positive odd integer.
    """
    if len(input_data.shape) != 3:
        raise ValueError("adaptive_gaussian only accepts 3 dims numpy arrays")

    #kernel_size = kwargs.get('kernel_size', 8)
    output = ndimage.median_filter(input_data, size=(1, kernel_size, kernel_size))
    return output


def local_sum(input_data : np.ndarray, kernel_size : int = 8) -> numpy.ndarray :
    """
    Computes the local sums of the input data using a sliding window defined by the kernel size.
    Each element in the output is the sum of the pixels within the specified kernel size window.

    Args:
        input_data (np.ndarray): A 3D numpy array of shape (1, number_of_lines, number_of_columns)
                                 containing the Digital Elevation Model (DEM).
                                 The function only accepts arrays with one band.

        kernel_size (int): The size of the sliding window used to compute the local sum.

    Returns:
        np.ndarray: A numpy array of the same size as `input_data` containing the computed local sums.

    Raises:
        ValueError: If `input_data` does not have 3 dimensions or if the first dimension is not of size 1.
    """

    #kernel_size = kwargs.get('kernel_size', 8)
    # compute local sum of band pixels
    output = _local_sum(input_data, kernel_size)
    return output


def local_mean(input_data : np.ndarray, kernel_size : int = 8) -> numpy.ndarray :
    """
    Computes the local means of the input data using a sliding window defined by the kernel size.
    Each element in the output is the mean of the pixels within the specified kernel size window.

    Args:
        input_data (np.ndarray): A 3D numpy array of shape (1, number_of_lines, number_of_columns)
                                 containing the Digital Elevation Model (DEM).
                                 The function only accepts arrays with one band.

        kernel_size (int): The size of the sliding window used to compute the local mean.

    Returns:
        np.ndarray: A numpy array of the same size as `input_data` containing the computed local means.

    Raises:
        ValueError: If `input_data` does not have 3 dimensions or if the first dimension is not of size 1.
    """
    #kernel_size = kwargs.get('kernel_size', 8)
    # compute local sum of band pixels
    output = _local_sum(input_data, kernel_size)
    # compute local sum of band mask: number of valid pixels
    # in the kernel
    if ma.is_masked(input_data):
        valid = _local_sum(1 - input_data.mask, kernel_size)
    else:
        valid = kernel_size ** 2
    # compute mean for the band
    return np.divide(output, valid, out=np.zeros_like(output), where=valid != 0)


def adaptive_gaussian(input_data : np.ndarray, kernel_size : int = 8, sigma : int = 1) -> numpy.ndarray :
    """
    Applies an Adaptive Gaussian Filter to the input data that smoothes the input while preserving edges.

    Args:
        input_data (np.ndarray): A 3D numpy array of shape (1, number_of_lines, number_of_columns)
                                 containing the Digital Elevation Model (DEM).
                                 The function only accepts arrays with one band.

        kernel_size (int): The size of the kernel used for the adaptive filtering. Default is 8.

        sigma (int): The standard deviation of the Gaussian distribution, which controls the level of smoothing.
                     Default is 1.

    Returns:
        np.ndarray: A numpy array of the same shape as `input_data`, containing the filtered data.

    Raises:
        ValueError: If `input_data` does not have 3 dimensions or if the first dimension is not of size 1.
    """
    if len(input_data.shape) != 3:
        raise ValueError("adaptive_gaussian only accepts 3 dims numpy arrays")
    if input_data.shape[0] != 1:
        raise ValueError("adaptive_gaussian only accepts numpy arrays with first dim of size 1")

    dtype = input_data.dtype

    w_1 = (input_data[0, :, :-2] - input_data[0, :, 2:]) ** 2
    w_2 = (input_data[0, :-2, :] - input_data[0, 2:, :]) ** 2
    w = np.exp(-(w_1[1:-1, :] + w_2[:, 1:-1]) / (2 * sigma ** 2))
    w_sum = signal.convolve2d(w, np.ones((3, 3), dtype=dtype), boundary='symm', mode='same')
    w_sum += np.finfo(dtype).eps
    out = input_data
    for i in range(kernel_size):
        prod = w * out[0, 1:-1, 1:-1]
        conv = signal.convolve2d(prod, np.ones((3, 3), dtype=dtype), boundary='symm', mode='same')
        out[0, 1:-1, 1:-1] = conv / w_sum
    return out


def svf(input_data : np.ndarray, radius : int = 8, directions : int = 12, resolution : float = 0.5, altitude = None) -> np.ndarray:
    """
    Computes the Sky View Factor (SVF), which represents the fraction of the visible sky from each point in a Digital Elevation Model (DEM).

    More information about the Sky View Factor can be found `here <https://www.researchgate.net/publication/257315893_Application_of_sky-view_factor_for_the_visualization_of_historic_landscape_features_in_lidar-derived_relief_models>`_.

    Args:
        input_data (np.ndarray): A 3D numpy array of shape (1, number_of_lines, number_of_columns) containing the Digital Elevation Model (DEM).
                                  The function only accepts arrays with one band (the first dimension must be 1).

        radius (int): The maximum distance (in pixels) around each point to evaluate the horizontal elevation angle. Default is 8.

        direction (int): The number of discrete directions to compute the vertical angle. Default is 12.

        resolution (float): The spatial resolution of the input data in meters. Default is 0.5.

        altitude (Optional[np.ndarray]): A reference altitude to use for computing the SVF. If not specified, SVF is computed using the elevation of each point.

    Returns:
        np.ndarray: A numpy array of the same size as `input_data`, containing the Sky View Factor for each point,
                    where values range from 0 (no visible sky) to 1 (full sky visibility).

    Raises:
        ValueError: If `input_data` does not have 3 dimensions or if the first dimension is not of size 1.

    """
    if len(input_data.shape) != 3:
        raise ValueError("svf only accepts 3 dims numpy arrays")
    if input_data.shape[0] != 1:
        raise ValueError("svf only accepts numpy arrays with first dim of size 1")

    nb_directions = directions

    # initialize output
    shape = input_data.shape
    out = np.zeros(shape, dtype=np.float32)

    # prevent nodata problem
    # change the NaN in the input array to 0
    input_band = np.nan_to_num(input_data[0], copy=False, nan=0)

    # compute directions
    axes = [_bresenham_line(360 * i / nb_directions, radius)
            for i in range(nb_directions)]

    # get altitude of current point to consider for computing elevation angle
    if altitude is None:
        view = input_band[radius: shape[1] - radius, radius: shape[2] - radius]
    else:
        view = altitude

    # iterate over axes to identify the largest elevation in the radius
    for axe in axes:
        ratios = np.zeros((shape[1] - 2 * radius, shape[2] - 2 * radius), dtype=np.float32)
        for x_tr, y_tr, r in axe:
            new_ratios = input_band[radius + x_tr: shape[1] - radius + x_tr,
                                    radius + y_tr: shape[2] - radius + y_tr] - view
            # tangente de l'angle
            new_ratios /= (r * resolution)
            ratios = np.maximum(ratios, new_ratios)

        # SVF = (cosinus de l'angle avec la relation : cos² = sqrt(1 / (1+tan²))
        ratios = 1 / np.sqrt(ratios**2 + 1)  # = np.sin(np.arctan(ratios / self.pixel_size))
        out[0, radius: shape[1] - radius, radius: shape[2] - radius] += ratios

    out /= nb_directions
    return out


def _bresenham_line(theta : int, radius : int) -> tuple :
    """
    Implementation of the `Bresenham's line algorithm <https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm>`_

    This function generates points along a line from the origin (0, 0) based on the given angle (theta)
    and length (radius).

    Args:
        theta (int): The angle of the line in degrees (0 degrees points to the right, 90 degrees points up).
        radius (int): The length of the line in units. If radius is less than or equal to zero, an empty list will be returned.

    Returns:
        list: A list of tuples representing the coordinates of the line points in the format
              (x, y, r), where (x, y) are the coordinates of the point and r is the distance
              from the origin to that point. The origin point (0, 0) is not included.
    """
    x, y = 0, 0
    dx = math.cos(math.radians(theta))
    dy = math.sin(math.radians(theta))
    sx = -1 if dx < 0 else 1
    sy = -1 if dy < 0 else 1
    pts = list()
    r = 0
    if abs(dx) > abs(dy):
        delta = abs(math.tan(math.radians(theta)))
        err = 0
        while r < radius:
            x += sx
            err += delta
            if err > 0.5:
                y += sy
                err -= 1.0
            r = math.sqrt(x ** 2 + y ** 2)
            pts.append((x, y, r))
    else:
        delta = abs(math.tan(math.radians(90 - theta)))
        err = 0
        while r < radius:
            y += sy
            err += delta
            if err > 0.5:
                x += sx
                err -= 1.0
            r = math.sqrt(x ** 2 + y ** 2)
            pts.append((x, y, r))

    return pts


def hillshade(input_data : np.ndarray, elevation : float = 0.0, azimuth : float = 0.0, radius : int = 8, resolution : float = 0.5) -> numpy.ndarray :
    """
    Computes a mask of cast shadows in a Digital Elevation Model (DEM).

    This function calculates the shadows based on the specified elevation and azimuth angles,
    and returns a mask indicating where shadows are cast.

    Args:
        input_data (np.ndarray): A 3D numpy array of shape (1, number_of_lines, number_of_columns) containing the Digital Elevation Model (DEM).
                                  The function only accepts arrays with one band.

        elevation (float): The angle (in degrees) between the horizon and the line of sight from an observer to the satellite.

        azimuth (float): The angle (in degrees) between true north and the projection of the satellite's position onto the horizontal plane,
                         measured in a clockwise direction.

        radius (int): The radius around each pixel to consider when calculating shadows.

        resolution (float): The spatial resolution of the input data, used for scaling calculations.

    Returns:
        np.ndarray: A boolean numpy array of the same size as `input_data`, indicating the mask of cast shadows,
                    where True represents shadowed areas and False represents illuminated areas.

    Raises:
        ValueError: If the input_data does not have 3 dimensions or if the first dimension is not of size 1.
    """
    if len(input_data.shape) != 3:
        raise ValueError("hillshade only accepts 3 dims numpy arrays")
    if input_data.shape[0] != 1:
        raise ValueError("hillshade only accepts numpy arrays with first dim of size 1")

    # initialize output
    shape = input_data.shape
    out = np.zeros(shape, dtype=bool)

    # prevent nodata problem
    input_band = np.nan_to_num(input_data[0], copy=False, nan=0)

    # compute direction
    axe = _bresenham_line(180 - azimuth, radius)

    # identify the largest elevation in the radius
    view = input_band[radius: shape[1] - radius, radius: shape[2] - radius]
    ratios = np.zeros((shape[1] - 2 * radius, shape[2] - 2 * radius), dtype=np.float32)
    for x_tr, y_tr, r in axe:
        new_ratios = input_band[radius + x_tr: shape[1] - radius + x_tr,
                                radius + y_tr: shape[2] - radius + y_tr] - view
        # tangente de l'angle
        new_ratios /= (r * resolution)
        ratios = np.maximum(ratios, new_ratios)

    angles = np.arctan(ratios)
    out[0, radius: shape[1] - radius, radius: shape[2] - radius] = angles > np.radians(elevation, dtype=np.float32)

    return out