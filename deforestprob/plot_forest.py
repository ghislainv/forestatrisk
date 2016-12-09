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
from matplotlib.colors import LinearSegmentedColormap
from miscellaneous import figure_as_image


# plot_forest
def plot_forest(input_forest_raster, output_file="output/forest.png"):
    """Plot the forest map.

    This function plots the forest map. Green is the remaining forest
    (value 1), red is the deforestation (value 0).

    :param input_forest_raster: path to forest raster.
    :param output_file: name of the plot file.
    :return: a Matplotlib figure of the forest map.

    """

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

    # Colormap
    colors = []
    cmax = 255.
    colors.append((forestND, (0, 0, 0, 0)))  # transparent
    colors.append((0, (1, 0, 0, 1)))  # red
    colors.append((1, (34 / cmax, 139 / cmax, 34 / cmax, 1)))  # forest green

    # Plot raster and save
    fig = plt.figure()
    plt.subplot(111)
    plt.imshow(ov_arr, cmap=color_map)
    plt.close(fig)
    fig_img = figure_as_image(fig, output_file, dpi=200)

    # Return figure
    return(fig_img)

# End
