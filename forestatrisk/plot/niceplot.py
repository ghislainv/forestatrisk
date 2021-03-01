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

# os.chdir("/home/ghislain/Code/forestatrisk/docsrc/notebooks")
# os.environ["PROJ_LIB"]="/home/ghislain/.pyenv/versions/miniconda3-latest/envs/conda-far/share/proj"

# Third party imports
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from osgeo import gdal, ogr

# Local imports
from scalebar import scale_bar


def _plot_polygon(poly, symbol='k-', **kwargs):
    """Plots a polygon using the given symbol."""
    for i in range(poly.GetGeometryCount()):
        subgeom = poly.GetGeometryRef(i)
        x, y = zip(*subgeom.GetPoints())
        plt.plot(x, y, symbol, **kwargs)


def _plot_line(line, symbol='k-', **kwargs):
    """Plots a line using the given symbol."""
    x, y = zip(*line.GetPoints())
    plt.plot(x, y, symbol, **kwargs)


def _plot_point(point, symbol='ko', **kwargs):
    """Plots a point using the given symbol."""
    x, y = point.GetX(), point.GetY()
    plt.plot(x, y, symbol, **kwargs)


def _plot_layer(filename, symbol, layer_index=0, **kwargs):
    """Plots an OGR layer using the given symbol."""
    ds = ogr.Open(filename)
    for row in ds.GetLayer(layer_index):
        geom = row.geometry()
        geom_type = geom.GetGeometryType()

        # Polygons
        if geom_type == ogr.wkbPolygon:
            _plot_polygon(geom, symbol, **kwargs)

        # Multipolygons
        elif geom_type == ogr.wkbMultiPolygon:
            for i in range(geom.GetGeometryCount()):
                subgeom = geom.GetGeometryRef(i)
                _plot_polygon(subgeom, symbol, **kwargs)

        # Lines
        elif geom_type == ogr.wkbLineString:
            _plot_line(geom, symbol, **kwargs)

        # Multilines
        elif geom_type == ogr.wkbMultiLineString:
            for i in range(geom.GetGeometryCount()):
                subgeom = geom.GetGeometryRef(i)
                _plot_line(subgeom, symbol, **kwargs)

        # Points
        elif geom_type == ogr.wkbPoint:
            _plot_point(geom, symbol, **kwargs)

        # Multipoints
        elif geom_type == ogr.wkbMultiPoint:
            for i in range(geom.GetGeometryCount()):
                subgeom = geom.GetGeometryRef(i)
                _plot_point(subgeom, symbol, **kwargs)


def nice_plot_prob(input_prob_raster,
                   projection=ccrs.Mercator(),
                   maxpixels=500000,
                   borders=None,
                   legend=False,
                   figsize=(11.69, 8.27),
                   dpi=300, **kwargs):
    """Plot map of spatial probability of deforestation.

    This function plots the spatial probability of deforestation.

    :param input_prob_raster: Path to raster of probabilities.
    :param projection: Cartopy projection.
    :param maxpixels: Maximum number of pixels to plot.
    :param borders: Vector file to be plotted.
    :param legend: Add colorbar if True.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :param \\**kwargs: see below.

    :Keyword Arguments: Additional arguments to plot borders.

    :return: A Matplotlib figure of the map of spatial probability of
        deforestation.

    """

    # Load raster and band
    rasterR = gdal.Open(input_prob_raster, gdal.GA_ReadOnly)
    rasterB = rasterR.GetRasterBand(1)
    gt = rasterR.GetGeoTransform()
    ncol = rasterR.RasterXSize
    nrow = rasterR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]
    extent = [Xmin, Xmax, Ymin, Ymax]

    # Total number of pixels
    npixels_orig = ncol * nrow
    # Check number of pixels is inferior to maxpixels
    if (npixels_orig > maxpixels):
        # Remove potential existing external overviews
        if os.path.isfile(input_prob_raster + ".ovr"):
            os.remove(input_prob_raster + ".ovr")
        # Find overview level such that npixels <= maxpixels
        i = 0
        npixels_ov = npixels_orig
        while npixels_ov > maxpixels:
            i += 1
            ov_level = pow(2, i)
            npixels_ov = npixels_orig // np.power(ov_level, 2)
        # Build overview
        print("Build overview")
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
        rasterR.BuildOverviews("nearest", [ov_level])
        # Get data from overview
        ov_band = rasterB.GetOverview(0)
        ov_arr = ov_band.ReadAsArray()
    else:
        # Get original data
        ov_arr = rasterB.ReadAsArray()

    # Dereference driver
    rasterB = None
    del(rasterR)

    # Colormap
    colors = []
    cmax = 255.0  # float for division
    vmax = 65535.0  # float for division
    colors.append((0, (34 / cmax, 139 / cmax, 34 / cmax, 1)))  # green
    colors.append((1 / vmax, (34 / cmax, 139 / cmax, 34 / cmax, 1)))  # green
    colors.append((39322 / vmax, (1, 165 / cmax, 0, 1)))  # orange, p=0.60
    # red, p=0.80
    colors.append((52429 / vmax, (227 / cmax, 26 / cmax, 28 / cmax, 1)))
    colors.append((1, (0, 0, 0, 1)))  # black
    color_map = LinearSegmentedColormap.from_list(name="mycm", colors=colors,
                                                  N=65535, gamma=1.0)
    # transparent, must be associated with vmin
    color_map.set_under(color=(1, 1, 1, 0))

    # Plot
    fig = plt.figure(figsize=figsize, dpi=dpi)
    plt.subplot(111, projection=projection)
    # Raster data
    plt.imshow(ov_arr, cmap=color_map, extent=extent,
               vmin=0.01, vmax=65535)
    if borders is not None:
        _plot_layer(borders, symbol="k-", **kwargs)

    # Legend
    if legend is True:
        t = np.linspace(1, 65535, 5, endpoint=True)
        cbar = plt.colorbar(ticks=t, orientation="vertical",
                            shrink=0.5, aspect=20)
        vl = np.linspace(0, 1, 5, endpoint=True)
        cbar.ax.set_yticklabels(vl)

    # Return figure
    return(fig)


# Plot
fig = nice_plot_prob("output/prob.tif",
                     maxpixels=1e8,
                     borders="data/ctry_PROJ.shp",
                     linewidth=0.2,
                     legend=True,
                     figsize=(5, 4), dpi=800)
ax = fig.gca()
# Scale bar
scale_bar(ax, (0.8, 0.1), 10, metres_per_unit=1000,
          unit_name="km", color="black", linewidth=1, text_kwargs={'size': 7})
# Gridlines from Cartopy
gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=0.3, alpha=0.5,
                  xlocs=[-61.8, -61.6, -61.4, -61.2, -61.0],
                  ylocs=[15.8, 16.0, 16.2, 16.4], draw_labels=True)
gl.top_labels = False
gl.right_labels = False
gl.xlabel_style = {'size': 6}
gl.ylabel_style = {'size': 6}

# Save
fig.savefig("output/prob_joss.png", dpi="figure", bbox_inches="tight")

# End
