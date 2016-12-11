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
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle


# plot_forest
def plot_obs(sample,
             name_forest_var,
             input_forest_raster,
             output_file="output/obs.png",
             zoom=None,
             dpi=200):
    """Plot the sample points over the forest map.

    This function plots the sample points over the forest map. Green
    is the remaining forest (value 1), red is the deforestation (value
    0).

    :param sample: pandas DataFrame with observation coordinates (X, Y).
    :param name_forest_var: name of the forest variable in sample DataFrame.
    :param input_forest_raster: path to forest raster.
    :param output_file: name of the plot file.
    :param dpi: resolution for output image.
    :param zoom: zoom to region (xmin, xmax, ymin, ymax).
    :return: a Matplotlib figure of the sample points.

    """

    # Load raster and band
    forestR = gdal.Open(input_forest_raster)
    forestB = forestR.GetRasterBand(1)
    forestND = forestB.GetNoDataValue()
    gt = forestR.GetGeoTransform()
    ncol = forestR.RasterXSize
    nrow = forestR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]
    extent = [Xmin, Xmax, Ymin, Ymax]

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
    fig = plt.figure(dpi=dpi)
    ax1 = plt.subplot(111)
    # No frame
    ax1.set_frame_on(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    plt.axis("off")
    # Raster
    plt.imshow(ov_arr, cmap=color_map, extent=extent)
    # Points
    f = name_forest_var
    x_defor = sample[sample[f] == 0]["X"]
    y_defor = sample[sample[f] == 0]["Y"]
    x_for = sample[sample[f] == 1]["X"]
    y_for = sample[sample[f] == 1]["Y"]
    plt.scatter(x_defor, y_defor, color="darkred")
    plt.scatter(x_for, y_for, color="darkgreen")
    if zoom is not None:
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])
    plt.close(fig)
    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi=dpi, bbox_inches="tight")
    return(fig)

# End
