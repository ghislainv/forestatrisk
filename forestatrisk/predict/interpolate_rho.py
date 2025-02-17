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
def interpolate_rho(
    rho, input_raster, output_file="output/rho.tif", csize_orig=10, csize_new=1
):
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
    with gdal.Open(input_raster) as ds:
        gt = ds.GetGeoTransform()
        xmin, xres, _, ymax, _, yres = gt
        xmax = xmin + xres * ds.RasterXSize
        ymin = ymax + yres * ds.RasterYSize
        proj = ds.GetProjection()

    # Cell number from region
    csize_orig = csize_orig * 1000  # Transform km in m
    ncell_x = int(np.ceil((xmax - xmin) / csize_orig))
    ncell_y = int(np.ceil((ymax - ymin) / csize_orig))

    # NumpyArray
    rho = np.array(rho)
    rho_arr = rho.reshape(ncell_y, ncell_x)

    # Create .tif file
    dirname = os.path.dirname(output_file)
    rho_orig_filename = os.path.join(dirname, "rho_orig.tif")
    driver = gdal.GetDriverByName("GTiff")
    if os.path.isfile(rho_orig_filename):
        os.remove(rho_orig_filename)
    rho_r = driver.Create(
        rho_orig_filename,
        ncell_x,
        ncell_y,
        1,
        gdal.GDT_Float64
    )
    rho_r.SetProjection(proj)
    gt_new = list(gt)
    gt_new[1] = csize_orig
    gt_new[5] = -csize_orig
    rho_r.SetGeoTransform(gt_new)

    # Write data
    print("Write spatial random effect data to disk")
    rho_b = rho_r.GetRasterBand(1)
    rho_b.WriteArray(rho_arr)
    rho_b.FlushCache()  # Write cache data to disk

    # Compute statistics
    print("Compute statistics")
    rho_b.ComputeStatistics(False)

    # Set nodata value
    rho_b.SetNoDataValue(-9999)

    # Dereference driver
    rho_b = None
    del rho_r

    # Cubicspline interpolation to csize_new*1000 km
    print("Resampling spatial random effects to file " + output_file)
    param = gdal.WarpOptions(
        warpOptions=["overwrite"],
        format="GTiff",
        xRes=csize_new * 1000,
        yRes=csize_new * 1000,
        resampleAlg=gdal.GRA_CubicSpline,
        creationOptions=["COMPRESS=DEFLATE"],
    )
    ds_rho = gdal.Warp(output_file, rho_orig_filename, options=param)
    del ds_rho

# End
