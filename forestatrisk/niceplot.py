#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

from __future__ import division, print_function  # Python 3 compatibility
import numpy as np
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from osgeo import gdal
from matplotlib.colors import ListedColormap, LinearSegmentedColormap


# color_map
def color_map(plot_type="prob"):
    if (plot_type == "prob"):
        # Colormap
        colors = []
        cmax = 255.0  # float for division
        vmax = 65535.0  # float for division
        colors.append((0, (0, 0, 0, 0)))  # transparent
        colors.append((1 / vmax, (34 / cmax, 139 / cmax, 34 / cmax, 1)))
        colors.append((45000 / vmax, (1, 165 / cmax, 0, 1)))  # orange
        colors.append((55000 / vmax, (1, 0, 0, 1)))  # red
        colors.append((1, (0, 0, 0, 1)))  # black
        color_map = LinearSegmentedColormap.from_list(name="mycm",
                                                      colors=colors,
                                                      N=65535, gamma=1.0)
    elif (plot_type == "fcc"):
        # Colormap
        colors = []
        cmax = 255.0  # float for division
        col_defor = (227, 26, 28, 255)
        col_defor = tuple(np.array(col_defor) / cmax)
        colors.append(col_defor)  # default is red
        colors.append((51 / cmax, 160 / cmax, 44 / cmax, 1))  # forest green
        colors.append((0, 0, 0, 0))  # transparent
        color_map = ListedColormap(colors)
    elif (plot_type == "forest"):
        # Colormap
        colors = []
        cmax = 255.0  # float for division
        colors.append((51 / cmax, 160 / cmax, 44 / cmax, 1))  # forest green
        colors.append((0, 0, 0, 0))  # transparent
        color_map = ListedColormap(colors)
    return(color_map)


# raster2array
def raster2array(input_prob_raster, n_overview=0):

    # Load raster and band
    rasterR = gdal.Open(input_prob_raster)
    rasterB = rasterR.GetRasterBand(1)

    # Get data from finest overview
    ov_band = rasterB.GetOverview(n_overview)
    ov_arr = ov_band.ReadAsArray()

    # Dereference driver
    rasterB = None
    del(rasterR)

    # Return figure
    return(ov_arr)


# create new figure, axes instances.
fig = plt.figure()
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
# setup mercator map projection.
m = Basemap(llcrnrlon=-20., llcrnrlat=-40., urcrnrlon=60., urcrnrlat=40.,
            resolution="l", projection="merc",
            lat_ts=20.)
# Draw deforestation probability
m.imshow(raster2array("prob.tif", n_overview=0),
         cmap=color_map(plot_type="prob"), origin="upper")
# Draw country
m.drawcoastlines()
m.drawcountries()
# draw parallels
m.drawparallels(np.arange(-40, 40, 20), labels=[1, 1, 0, 1])
# draw meridians
m.drawmeridians(np.arange(-20, 60, 20), labels=[1, 1, 0, 1])
ax.set_title("Test")
plt.show()

# End
