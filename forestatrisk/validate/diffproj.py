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
from ..misc import progress_bar, makeblock


# r_diffproj
def r_diffproj(inputA, inputB,
               output_file="diffproj.tif",
               blk_rows=128):
    """Compute a raster of differences for comparison.

    This function compute a raster of differences between two rasters
    of future forest cover. Rasters must have the same extent and resolution.

    :param inputA: Path to first raster (predictions).
    :param inputB: Path to second raster of (sd. predictions or observations).
    :param output_file: Name of the output raster file for differences.
    :param blk_rows: If > 0, number of rows for computation by block.

    """

    # Inputs
    ds_A = gdal.Open(inputA)
    band_A = ds_A.GetRasterBand(1)
    ds_B = gdal.Open(inputB)
    band_B = ds_B.GetRasterBand(1)

    # Landscape variables from forest raster
    gt = ds_A.GetGeoTransform()
    ncol = ds_A.RasterXSize
    nrow = ds_A.RasterYSize
    proj = ds_A.GetProjection()

    # Make blocks
    blockinfo = makeblock(inputA, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Raster of predictions
    print("Create a raster file on disk for projections")
    driver = gdal.GetDriverByName("GTiff")
    ds_out = driver.Create(output_file, ncol, nrow, 1,
                           gdal.GDT_Byte,
                           ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"])
    ds_out.SetGeoTransform(gt)
    ds_out.SetProjection(proj)
    band_out = ds_out.GetRasterBand(1)
    band_out.SetNoDataValue(255)

    # Compute differences
    # Message
    print("Compute differences")
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Data for one block of the stack (shape = (nband,nrow,ncol))
        A = band_A.ReadAsArray(x[px], y[py], nx[px], ny[py])
        B = band_B.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Compute differences
        data_diff = A
        data_diff[np.where(np.logical_and(A == 0, B == 0))] = 0
        data_diff[np.where(np.logical_and(A == 1, B == 1))] = 1
        # false negative (no pred. deforestation vs. obs. deforestation)
        data_diff[np.where(np.logical_and(A == 1, B == 0))] = 2
        # false positive (pred. deforestation vs. no obs. deforestation)
        data_diff[np.where(np.logical_and(A == 0, B == 1))] = 3
        data_diff[np.where(np.logical_and(A == 255, B == 255))] = 255
        # Write output data
        band_out.WriteArray(data_diff, x[px], y[py])

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


# mat_diffproj
def mat_diffproj(input_raster,
                 blk_rows=128):
    """Compute a confusion matrix from a raster of differences.

    This function computes a confusion matrix from a raster of
    differences. The raster of differences can be obtained using
    function ``.r_diffproj()``\\ .

    :param input_raster: Raster of differences obtain with
        forestatrisk.r_projdiff.

    :return: A confusion matrix. [[np00, np01], [np10, np11]].

    """

    # Inputs
    ds = gdal.Open(input_raster)
    band = ds.GetRasterBand(1)

    # Make blocks
    blockinfo = makeblock(input_raster, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Confusion matrix
    n00 = n11 = n10 = n01 = 0

    # Compute differences
    # Message
    print("Compute confusion matrix")
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Data for one block of the stack (shape = (nband,nrow,ncol))
        data_diff = band.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Confusion matrix
        n00 += (data_diff == 0).sum()
        n11 += (data_diff == 1).sum()
        n10 += (data_diff == 2).sum()
        n01 += (data_diff == 3).sum()

    # Return confusion matrix
    conf_mat = np.array([[n00, n01], [n10, n11]])
    return conf_mat

# End
