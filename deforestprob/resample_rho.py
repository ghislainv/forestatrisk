#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Import
import os
import numpy as np
from osgeo import gdal
import matplotlib.pyplot as plt
from miscellaneous import figure_as_image


# Resample_rho
def resample_rho(rho, input_raster, output_file="output/rho.tif",
                 csize_orig=10, csize_new=1,
                 figsize=(11.69, 8.27),
                 dpi=300):
    """Resample rho values with interpolation.

    This function resamples the spatial random effects (rho values)
    obtained from an iCAR model. It performs a bilinear interpolation
    at a finer resolution and smoothens the rho values.

    :param rho: original rho values estimates with the iCAR model.
    :param input_raster: path to input raster defining the region.
    :output_file: path to output raster file with resampled rho values.
    :csize_orig: original size of the spatial cells (in km).
    :csize_new: new size of the spatial cells for bilinear \
    interpolation (in km).
    :param figsize: figure size in inches.
    :param dpi: resolution for output image.

    :return: a Matplotlib figure of the spatial random effects.

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
    ncell_X = np.ceil((Xmax - Xmin) / csize_orig).astype(int)
    ncell_Y = np.ceil((Ymax - Ymin) / csize_orig).astype(int)

    # NumpyArray
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
    rho_min, rho_max = rho_B.ComputeRasterMinMax()
    rho_bound = np.max((-rho_min, rho_max))

    # Build overviews
    print("Build overview")
    rho_R.BuildOverviews("average", [2, 4, 8, 16, 32])

    # Get data from finest overview
    # ov_band = rho_B.GetOverview(0)
    ov_band = rho_B
    ov_arr = ov_band.ReadAsArray()

    # Dereference driver
    rho_B = None
    del rho_R

    # Bilinear interpolation to csize_new*1000 km
    print("Resampling spatial random effects to file " + output_file)
    param = ["gdalwarp", "-overwrite",
             "-tr", str(csize_new * 1000), str(csize_new * 1000),
             "-r bilinear",
             "-ot Float32",
             "-co 'COMPRESS=LZW'", "-co 'PREDICTOR=3'",
             rho_orig_filename, output_file]
    command = " ".join(param)
    os.system(command)

    # Plot
    print("Make figure")
    # Figure name
    fig_name = output_file
    index_dot = output_file.index(".")
    fig_name = fig_name[:index_dot]
    fig_name = fig_name + ".png"
    # Plot raster and save
    fig = plt.figure(figsize=figsize, dpi=dpi)
    plt.subplot(111)
    plt.imshow(ov_arr, cmap="RdYlGn_r", vmin=-rho_bound, vmax=rho_bound)
    plt.colorbar()
    fig_img = figure_as_image(fig, fig_name, dpi=dpi)

    # Return figure
    return(fig_img)

# End
