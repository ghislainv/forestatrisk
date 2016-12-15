#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Import
from osgeo import gdal
from glob import glob
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import os
import sys
import numpy as np


# plot_var
def plot_var(var_dir,
             output_file="output/var.png",
             dpi=200):
    """Plot the map of variables.

    This function plots the map of variables.

    :param var_dir: path to variable directory.
    :param output_file: name of the plot file.
    :param dpi: resolution for output image.
    :return: Matplotlib figures of the variables.

    """

    # Raster list
    var_tif = var_dir + "/*.tif"
    raster_list = glob(var_tif)
    raster_list.sort()

    # Make vrt with gdalbuildvrt
    print("Make virtual raster with variables as raster bands")
    inputvar = " ".join(raster_list)
    outputfile = var_dir + "/var.vrt"
    os.system("gdalbuildvrt -separate -o " + outputfile + " " + inputvar)

    # Load vrt file
    stack = gdal.Open(var_dir + "/var.vrt")
    gt = stack.GetGeoTransform()
    ncol = stack.RasterXSize
    nrow = stack.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]
    extent = [Xmin, Xmax, Ymin, Ymax]

    # List of nodata values
    nband = stack.RasterCount
    bandND = np.zeros(nband)
    for k in range(nband):
        band = stack.GetRasterBand(k + 1)
        if band is None:
            print("NoData value is not specified \
            for input raster file %d" % k)
            sys.exit(1)
        bandND[k] = band.GetNoDataValue()

    # Load raster and band
    forestR = gdal.Open(input_forest_raster)
    forestB = forestR.GetRasterBand(1)
    forestND = forestB.GetNoDataValue()


    # Overviews
    if forestB.GetOverviewCount() == 0:
        # Build overviews
        print("Build overview")
        forestR.BuildOverviews("nearest", [8, 16, 32])
    # Get data from finest overview
    ov_band = forestB.GetOverview(0)
    ov_arr = ov_band.ReadAsArray()
    ov_arr[ov_arr == forestND] = 2

    # Colormap
    colors = []
    cmax = 255.0  # float for division
    colors.append((1, 0, 0, 1))  # red
    colors.append((34/cmax, 139/cmax, 34/cmax, 1))  # forest green
    colors.append((0, 0, 0, 0))  # transparent
    color_map = ListedColormap(colors)

    # Plot raster and save
    place = 111 if zoom is None else 121
    fig = plt.figure(dpi=dpi)
    ax1 = plt.subplot(place)
    ax1.set_frame_on(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    plt.imshow(ov_arr, cmap=color_map, extent=extent)
    plt.axis("off")
    if zoom is not None:
        z = Rectangle(
            (zoom[0], zoom[2]),
            zoom[1]-zoom[0],
            zoom[3]-zoom[2],
            fill=False
        )
        ax1.add_patch(z)
        ax2 = plt.subplot(222)
        plt.imshow(ov_arr, cmap=color_map, extent=extent)
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])
        ax2.set_xticks([])
        ax2.set_yticks([])
    plt.close(fig)
    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi=dpi, bbox_inches="tight")
    return(fig)

# End
