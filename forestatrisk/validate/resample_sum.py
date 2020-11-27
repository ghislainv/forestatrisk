#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Standard library imports
from __future__ import division, print_function  # Python 3 compatibility

# Third party imports
import numpy as np
from osgeo import gdal

# Local application imports
from ..misc import progress_bar, make_square


# Coarsen
def coarsen_sum(a, c):
    """Resample to coarser resolution using sum

    This is an internal function used by resample_sum.

    :param a: 2D numpy array
    :param c: Coarseness, in number of cells
    """

    if ((a.shape[0] % c == 0) and (
            a.shape[1] % c == 0)):
        temp = a.reshape(a.shape[0] // c, c,
                         a.shape[1] // c, c)
    else:
        shape = np.array(a.shape, dtype=int)
        # New shape
        ns = c * np.ceil(shape / c).astype(int)
        a_ns = np.zeros(ns)
        a_ns[:shape[0], :shape[1]] = a
        temp = a_ns.reshape(ns[0] // c, c,
                            ns[1] // c, c)
    b = np.sum(temp, axis=(1, 3))
    return b


# Resample to coarser resolution with sum
def resample_sum(input_raster, output_raster, val=0,
                 window_size=2):
    """Resample to coarser resolution with counts.

    This function resamples to coarser resolution counting pixel
    number having a given value. Window's size is limited to 1000
    pixels.

    :param input_raster: Path to input raster.
    :param val: Pixel value to consider.
    :param window_size: Size of the window in number of pixels.
    :param output_raster: Path to output raster file.

    """

    # Limit window_size to 1000
    if (window_size > 1000):
        window_size = 1000
        square_size = 1000

    # Compute square size as a function of window_size
    print("Compute square size")
    if window_size <= 1000:
        square_size = int(window_size * (1000 // window_size))

    # Landscape variables from input raster
    ds_in = gdal.Open(input_raster)
    gt_in = ds_in.GetGeoTransform()
    ncol_in = ds_in.RasterXSize
    nrow_in = ds_in.RasterYSize

    # Landscape variables for output raster
    ncol_out = int(np.ceil(ncol_in / window_size))
    nrow_out = int(np.ceil(nrow_in / window_size))
    gt_out_list = list(gt_in)  # Copy the georeference to a list
    gt_out_list[1] = gt_in[1] * window_size
    gt_out_list[5] = gt_in[5] * window_size
    gt_out = tuple(gt_out_list)

    # Raster of result
    print("Create output raster file on disk")
    driver = gdal.GetDriverByName("GTiff")
    ds_out = driver.Create(output_raster, ncol_out, nrow_out, 1,
                           gdal.GDT_UInt32,
                           ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"])
    ds_out.SetGeoTransform(gt_out)
    ds_out.SetProjection(ds_in.GetProjection())  # Copy projection info
    band_out = ds_out.GetRasterBand(1)
    band_out.SetNoDataValue(4294967295)

    # Input data
    band_in = ds_in.GetRasterBand(1)

    # Make square
    squareinfo = make_square(input_raster, square_size)
    nsquare = squareinfo[0]
    nsquare_x = squareinfo[1]
    x = squareinfo[3]
    y = squareinfo[4]
    nx = squareinfo[5]
    ny = squareinfo[6]
    print("Divide region in {} squares".format(nsquare))

    # Loop on squares
    print("Loop on squares")
    for s in range(nsquare):
        # Progress bar
        progress_bar(nsquare, s + 1)
        # Position in 1D-arrays
        px = s % nsquare_x
        py = s // nsquare_x
        # Data for one square
        data_in = band_in.ReadAsArray(x[px], y[py], nx[px], ny[py])
        data_val = (data_in == val).astype(int)
        # Coarsen data
        data_out = coarsen_sum(data_val, window_size)
        band_out.WriteArray(data_out, x[px] // window_size,
                            y[py] // window_size)

    # Compute statistics
    print("Compute statistics")
    band_out.FlushCache()  # Write cache data to disk
    band_out.ComputeStatistics(False)

    # Build overviews
    print("Build overviews")
    ds_out.BuildOverviews("nearest", [4, 8, 16, 32])

    # Dereference driver
    band_out = None
    del(ds_out)

# End


# Begin test
# Raster
# a = np.random.choice([0, 1], 121).reshape(11, 11)
# driver = gdal.GetDriverByName("GTiff")
# ds = driver.Create("test.tif", 11, 11, 1,
#                    gdal.GDT_UInt32,
#                    ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"])
# band = ds.GetRasterBand(1)
# band.WriteArray(a, 0, 0)
# band.FlushCache()
# band.ComputeStatistics(False)
# band = None
# del(ds)

# Call to function
# resample_sum(input_raster="test.tif",
#              output_raster="test_out.tif",
#              val=0,
#              window_size=2)

# input_raster = "test.tif"
# output_raster = "test_out.tif"
# val = 0
# window_size = 2

# Results
# ds = gdal.Open("test_out.tif")
# band = ds.GetRasterBand(1)
# b = band.ReadAsArray()
# band = None
# del(ds)
# End test
