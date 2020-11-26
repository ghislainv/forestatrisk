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
import os

# Third party imports
import numpy as np
from osgeo import gdal


# Interpolate_rho
def interpolate_rho(rho, input_raster, output_file="output/rho.tif",
                    csize_orig=10, csize_new=1):
    """Resample rho values with interpolation.

    This function resamples the spatial random effects (rho values)
    obtained from an iCAR model. It performs a cubicspline interpolation
    at a finer resolution and smoothens the rho values.

    :param rho: Original rho values estimates with the iCAR model.
    :param input_raster: Path to input raster defining the region.
    :param output_file: Path to output raster file with resampled rho values.
    :param csize_orig: Original size of the spatial cells (in km).
    :param csize_new: New size of the spatial cells for cubicspline
        interpolation (in km).

    """

    # Region
    r = gdal.Open(input_raster)
    ncol = r.RasterXSize
    nrow = r.RasterYSize
    gt = r.GetGeoTransform()
    xres = gt[1]
    yres = -gt[5]
    Xmin = gt[0]
    Xmax = gt[0] + xres * ncol
    Ymin = gt[3] - yres * nrow
    Ymax = gt[3]

    # Cell number from region
    csize_orig = csize_orig * 1000  # Transform km in m
    ncell_X = int(np.ceil((Xmax - Xmin) / csize_orig))
    ncell_Y = int(np.ceil((Ymax - Ymin) / csize_orig))

    # NumpyArray
    rho = np.array(rho)
    rho_arr = rho.reshape(ncell_Y, ncell_X)

    # Create .tif file
    dirname = os.path.dirname(output_file)
    rho_orig_filename = os.path.join(dirname, "rho_orig.tif")
    driver = gdal.GetDriverByName("GTiff")
    rho_R = driver.Create(rho_orig_filename, ncell_X, ncell_Y, 1,
                          gdal.GDT_Float64)
    rho_R.SetProjection(r.GetProjection())
    gt = list(gt)
    gt[1] = csize_orig
    gt[5] = -csize_orig
    rho_R.SetGeoTransform(gt)

    # Write data
    print("Write spatial random effect data to disk")
    rho_B = rho_R.GetRasterBand(1)
    rho_B.WriteArray(rho_arr)
    rho_B.FlushCache()
    rho_B.SetNoDataValue(-9999)

    # Compute statistics
    print("Compute statistics")
    rho_B.FlushCache()  # Write cache data to disk
    rho_B.ComputeStatistics(False)

    # Build overviews
    print("Build overview")
    rho_R.BuildOverviews("average", [2, 4, 8, 16, 32])

    # Dereference driver
    rho_B = None
    del rho_R

    # Cubicspline interpolation to csize_new*1000 km
    print("Resampling spatial random effects to file " + output_file)
    param = gdal.WarpOptions(srcNodata=-9999, xRes=csize_new * 1000,
                             yRes=csize_new * 1000,
                             resampleAlg=gdal.GRA_CubicSpline,
                             outputType=gdal.GDT_Float32,
                             creationOptions=["COMPRESS=LZW", "PREDICTOR=3",
                                              "BIGTIFF=YES"])
    gdal.Warp(output_file, rho_orig_filename, options=param)

# End
