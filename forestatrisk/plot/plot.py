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
from glob import glob
import os
import sys

# Third party imports
import numpy as np
from osgeo import gdal, ogr
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt


# Plot vector objects
# (https://github.com/cgarrard/osgeopy-code/blob/master/Chapter13/listing13_3.py)
def plot_polygon(poly, symbol='k-', **kwargs):
    """Plots a polygon using the given symbol."""
    for i in range(poly.GetGeometryCount()):
        subgeom = poly.GetGeometryRef(i)
        x, y = zip(*subgeom.GetPoints())
        plt.plot(x, y, symbol, **kwargs)


# Use this function to fill polygons.
def plot_polygon_fill(poly, symbol='w', **kwargs):
    """Plots a polygon using the given symbol."""
    for i in range(poly.GetGeometryCount()):
        x, y = zip(*poly.GetGeometryRef(i).GetPoints())
        plt.fill(x, y, symbol, **kwargs)


def plot_line(line, symbol='k-', **kwargs):
    """Plots a line using the given symbol."""
    x, y = zip(*line.GetPoints())
    plt.plot(x, y, symbol, **kwargs)


def plot_point(point, symbol='ko', **kwargs):
    """Plots a point using the given symbol."""
    x, y = point.GetX(), point.GetY()
    plt.plot(x, y, symbol, **kwargs)


def plot_layer(filename, symbol, layer_index=0, **kwargs):
    """Plots an OGR layer using the given symbol."""
    ds = ogr.Open(filename)
    for row in ds.GetLayer(layer_index):
        geom = row.geometry()
        geom_type = geom.GetGeometryType()

        # Polygons
        if geom_type == ogr.wkbPolygon:
            plot_polygon(geom, symbol, **kwargs)

        # Multipolygons
        elif geom_type == ogr.wkbMultiPolygon:
            for i in range(geom.GetGeometryCount()):
                subgeom = geom.GetGeometryRef(i)
                plot_polygon(subgeom, symbol, **kwargs)

        # Lines
        elif geom_type == ogr.wkbLineString:
            plot_line(geom, symbol, **kwargs)

        # Multilines
        elif geom_type == ogr.wkbMultiLineString:
            for i in range(geom.GetGeometryCount()):
                subgeom = geom.GetGeometryRef(i)
                plot_line(subgeom, symbol, **kwargs)

        # Points
        elif geom_type == ogr.wkbPoint:
            plot_point(geom, symbol, **kwargs)

        # Multipoints
        elif geom_type == ogr.wkbMultiPoint:
            for i in range(geom.GetGeometryCount()):
                subgeom = geom.GetGeometryRef(i)
                plot_point(subgeom, symbol, **kwargs)


# Saving a matplotlib.pyplot figure as a border-less frame-less image
def figure_as_image(fig, output_file):
    """Remove borders and frames of a Matplotlib figure and save.

    :param fig: Matplotlib figure you want to save as the image.
    :param output_file: Path to the output image file.

    :return: Figure without borders and frame.

    """

    fig.tight_layout()
    a = fig.gca()
    a.set_frame_on(False)
    a.set_xticks([])
    a.set_yticks([])
    plt.axis("off")
    fig.savefig(output_file, dpi="figure", bbox_inches="tight")


# plot.correlation
def correlation(y, data,
                output_file="correlation.pdf",
                plots_per_page=4,
                figsize=(8.27, 11.69),
                dpi=300):
    """
    Correlation between variables and the probability of deforestation.

    This function plots (i) the histogram of the explicative variables
    and (ii) the probability of deforestation by bins of equal number of
    observations for each explicative variable.

    :param y: A 1D array for the response variable (forest=1, defor=0).
    :param data: A pandas DataFrame with column names.
    :param output_file: Path to output file.
    :param plots_per_page: Number of plots (lines) per page.
    :param figsize: Figure size.
    :param dpi: Resolution for output image.

    :return: List of Matplotlib figures.

    """

    # Data
    y = 1 - y  # Transform: defor=1, forest=0
    perc = np.arange(0, 110, 10)
    nperc = len(perc)
    colnames = data.columns.values
    # The PDF document
    pdf_pages = PdfPages(output_file)
    # Generate the pages
    nb_plots = len(colnames)
    nb_plots_per_page = plots_per_page
    #  nb_pages = int(np.ceil(nb_plots / float(nb_plots_per_page)))
    grid_size = (nb_plots_per_page, 2)
    # List of figures to be returned
    figures = []
    # Loop on variables
    for i in range(nb_plots):
        # Create a figure instance (ie. a new page) if needed
        if i % nb_plots_per_page == 0:
            fig = plt.figure(figsize=figsize, dpi=dpi)
        varname = colnames[i]
        theta = np.zeros(nperc - 1)
        se = np.zeros(nperc - 1)
        x = np.zeros(nperc - 1)
        quantiles = np.nanpercentile(data[varname], q=perc)
        # Compute theta and se by bins
        for j in range(nperc - 1):
            inf = quantiles[j]
            sup = quantiles[j + 1]
            x[j] = inf + (sup - inf) / 2
            y_bin = y[(data[varname] > inf) &
                      (data[varname] <= sup)]
            y_bin = np.array(y_bin)  # Transform into np.array to compute sum
            s = float(sum(y_bin == 1))  # success
            n = len(y_bin)  # trials
            if n != 0:
                theta[j] = s / n
            else:
                theta[j] = np.nan
            ph = (s + 1 / 2) / (n + 1)
            se[j] = np.sqrt(ph * (1 - ph) / (n + 1))
        # Plots
        # Histogram
        plt.subplot2grid(grid_size, (i % nb_plots_per_page, 0))
        Arr = np.array(data[varname])
        Arr = Arr[~np.isnan(Arr)]
        plt.hist(Arr, facecolor="#808080", alpha=0.75)
        plt.xlabel(varname, fontsize=16)
        plt.ylabel("Nb. of observations", fontsize=16)
        # Corelation
        plt.subplot2grid(grid_size, (i % nb_plots_per_page, 1))
        plt.plot(x, theta, color="#000000", marker='o', linestyle='--')
        plt.xlabel(varname, fontsize=16)
        plt.ylabel("Defor. probability", fontsize=16)
        # Close the page if needed
        if (i + 1) % nb_plots_per_page == 0 or (i + 1) == nb_plots:
            plt.tight_layout()
            figures.append(fig)
            pdf_pages.savefig(fig)
    # Write the PDF document to the disk
    pdf_pages.close()
    return(figures)


# plot.fcc
def fcc(input_fcc_raster,
        output_file="fcc.png",
        maxpixels=500000,
        borders=None,
        zoom=None,
        col_for=(34, 139, 34, 255),
        col_defor=(227, 26, 28, 255),
        figsize=(11.69, 8.27),
        dpi=300, **kwargs):
    """Plot forest-cover change (fcc) map.

    This function plots the forest-cover change map. Green is the
    remaining forest (value 1 in raster), the color specified is for
    deforestation (value 0 in raster).

    :param input_fcc_raster: Path to fcc raster.
    :param output_file: Name of the plot file.
    :param maxpixels: Maximum number of pixels to plot.
    :param borders: Vector file to be plotted.
    :param zoom: Zoom to region (xmin, xmax, ymin, ymax).
    :param col_for: rgba color for forest. Defaut to forest green.
    :param col_defor: rgba color for deforestation. Default to red.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :param \\**kwargs: see below.

    :Keyword Arguments: Additional arguments to plot borders.

    :return: A Matplotlib figure of the forest map.

    """

    # Load raster and band
    rasterR = gdal.Open(input_fcc_raster, gdal.GA_ReadOnly)
    rasterB = rasterR.GetRasterBand(1)
    rasterND = rasterB.GetNoDataValue()
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
        if os.path.isfile(input_fcc_raster + ".ovr"):
            os.remove(input_fcc_raster + ".ovr")
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

    # Change nodata values
    ov_arr[ov_arr == rasterND] = 2

    # Dereference driver
    rasterB = None
    del(rasterR)

    # Num of forest pixels
    nfor = np.sum(ov_arr == 1)

    # Colormap
    colors = []
    cmax = 255.0  # float for division
    col_defor = tuple(np.array(col_defor) / cmax)
    col_for = tuple(np.array(col_for) / cmax)
    colors.append(col_defor)
    if (nfor > 0):
        colors.append(col_for)
    colors.append((0, 0, 0, 0))  # transparent
    color_map = ListedColormap(colors)

    # Plot raster
    place = 111 if zoom is None else 121
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax1 = plt.subplot(place)
    ax1.set_frame_on(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    plt.imshow(ov_arr, cmap=color_map, extent=extent)
    if borders is not None:
        plot_layer(borders, symbol="k-", **kwargs)
    plt.axis("off")
    if zoom is not None:
        z = Rectangle(
            (zoom[0], zoom[2]),
            zoom[1] - zoom[0],
            zoom[3] - zoom[2],
            fill=False
        )
        ax1.add_patch(z)
        ax2 = plt.subplot(222)
        plt.imshow(ov_arr, cmap=color_map, extent=extent)
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])
        ax2.set_xticks([])
        ax2.set_yticks([])

    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi="figure", bbox_inches="tight")
    return(fig)


# plot.fcc12345
def fcc12345(input_fcc_raster,
             output_file="fcc12345.png",
             maxpixels=500000,
             borders=None,
             zoom=None,
             col=[(255, 165, 0, 255),
                  (235, 100, 0, 255),
                  (227, 26, 28, 255),
                  (163, 26, 28, 255),
                  (34, 139, 34, 255)],
             figsize=(11.69, 8.27),
             dpi=300, **kwargs):
    """Plot forest-cover change (fcc12345) map.

    This function plots the forest-cover change map with 4
    deforestation time-periods (2000 -> 2005 -> 2010 -> 2015 -> 2020
    for example) plus the remaining forest (5 classes).

    :param input_fcc_raster: Path to fcc12345 raster.
    :param output_file: Name of the plot file.
    :param maxpixels: Maximum number of pixels to plot.
    :param borders: Vector file to be plotted.
    :param zoom: Zoom to region (xmin, xmax, ymin, ymax).
    :param col: List of rgba colors for classes 12345.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :param \\**kwargs: see below.

    :Keyword Arguments: Additional arguments to plot borders.

    :return: A Matplotlib figure of the forest map.

    """

    # Load raster and band
    rasterR = gdal.Open(input_fcc_raster, gdal.GA_ReadOnly)
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
        if os.path.isfile(input_fcc_raster + ".ovr"):
            os.remove(input_fcc_raster + ".ovr")
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
    colors = [(1, 1, 1, 0)]  # transparent white for 0
    cmax = 255.0  # float for division
    for i in range(5):
        col_class = tuple(np.array(col[i]) / cmax)
        colors.append(col_class)
    color_map = ListedColormap(colors)

    # Plot raster
    place = 111 if zoom is None else 121
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax1 = plt.subplot(place)
    ax1.set_frame_on(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    plt.imshow(ov_arr, cmap=color_map, extent=extent)
    if borders is not None:
        plot_layer(borders, symbol="k-", **kwargs)
    plt.axis("off")
    if zoom is not None:
        z = Rectangle(
            (zoom[0], zoom[2]),
            zoom[1] - zoom[0],
            zoom[3] - zoom[2],
            fill=False
        )
        ax1.add_patch(z)
        ax2 = plt.subplot(222)
        plt.imshow(ov_arr, cmap=color_map, extent=extent)
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])
        ax2.set_xticks([])
        ax2.set_yticks([])

    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi="figure", bbox_inches="tight")
    return(fig)


# plot.fcc123
def fcc123(input_fcc_raster,
           output_file="fcc123.png",
           maxpixels=500000,
           borders=None,
           zoom=None,
           col=[(255, 165, 0, 255),
                (227, 26, 28, 255),
                (34, 139, 34, 255)],
           figsize=(11.69, 8.27),
           dpi=300, **kwargs):
    """Plot forest-cover change (fcc123) map.

    This function plots the forest-cover change map with 2
    deforestation time-periods (2000 -> 2010 -> 2020 for example) plus
    the remaining forest (3 classes).

    :param input_fcc_raster: Path to fcc123 raster.
    :param output_file: Name of the plot file.
    :param maxpixels: Maximum number of pixels to plot.
    :param borders: Vector file to be plotted.
    :param zoom: Zoom to region (xmin, xmax, ymin, ymax).
    :param col: List of rgba colors for classes 123.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :param \\**kwargs: see below.

    :Keyword Arguments: Additional arguments to plot borders.

    :return: A Matplotlib figure of the forest map.

    """

    # Load raster and band
    rasterR = gdal.Open(input_fcc_raster, gdal.GA_ReadOnly)
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
        if os.path.isfile(input_fcc_raster + ".ovr"):
            os.remove(input_fcc_raster + ".ovr")
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
    colors = [(1, 1, 1, 0)]  # transparent white for 0
    cmax = 255.0  # float for division
    for i in range(3):
        col_class = tuple(np.array(col[i]) / cmax)
        colors.append(col_class)
    color_map = ListedColormap(colors)

    # Plot raster
    place = 111 if zoom is None else 121
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax1 = plt.subplot(place)
    ax1.set_frame_on(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    plt.imshow(ov_arr, cmap=color_map, extent=extent)
    if borders is not None:
        plot_layer(borders, symbol="k-", **kwargs)
    plt.axis("off")
    if zoom is not None:
        z = Rectangle(
            (zoom[0], zoom[2]),
            zoom[1] - zoom[0],
            zoom[3] - zoom[2],
            fill=False
        )
        ax1.add_patch(z)
        ax2 = plt.subplot(222)
        plt.imshow(ov_arr, cmap=color_map, extent=extent)
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])
        ax2.set_xticks([])
        ax2.set_yticks([])

    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi="figure", bbox_inches="tight")
    return(fig)


# plot.forest
def forest(input_forest_raster,
           output_file="forest.png",
           maxpixels=500000,
           borders=None,
           zoom=None,
           figsize=(11.69, 8.27),
           dpi=300, **kwargs):
    """Plot forest map.

    This function plots the forest map in green. Raster values must be
    0 (non-forest) and 1 (forest).

    :param input_forest_raster: Path to forest raster.
    :param output_file: Name of the plot file.
    :param maxpixels: Maximum number of pixels to plot.
    :param borders: Vector file to be plotted.
    :param zoom: Zoom to region (xmin, xmax, ymin, ymax).
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :param \\**kwargs: see below.

    :Keyword Arguments: Additional arguments to plot borders.

    :return: A Matplotlib figure of the forest map.

    """

    # Load raster and band
    rasterR = gdal.Open(input_forest_raster, gdal.GA_ReadOnly)
    rasterB = rasterR.GetRasterBand(1)
    rasterND = rasterB.GetNoDataValue()
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
        if os.path.isfile(input_forest_raster + ".ovr"):
            os.remove(input_forest_raster + ".ovr")
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

    # Change nodata values
    ov_arr[ov_arr == rasterND] = 2

    # Dereference driver
    rasterB = None
    del(rasterR)

    # Colormap
    colors = []
    cmax = 255.0  # float for division
    colors.append((0, 0, 0, 0))  # transparent
    colors.append((34 / cmax, 139 / cmax, 34 / cmax, 1))  # forest green
    color_map = ListedColormap(colors)

    # Plot raster
    place = 111 if zoom is None else 121
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax1 = plt.subplot(place)
    ax1.set_frame_on(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    plt.imshow(ov_arr, cmap=color_map, extent=extent)
    if borders is not None:
        plot_layer(borders, symbol="k-", **kwargs)
    plt.axis("off")
    if zoom is not None:
        z = Rectangle(
            (zoom[0], zoom[2]),
            zoom[1] - zoom[0],
            zoom[3] - zoom[2],
            fill=False
        )
        ax1.add_patch(z)
        ax2 = plt.subplot(222)
        plt.imshow(ov_arr, cmap=color_map, extent=extent)
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])
        ax2.set_xticks([])
        ax2.set_yticks([])

    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi="figure", bbox_inches="tight")
    return(fig)


# plot.prob
def prob(input_prob_raster,
         output_file="prob.png",
         maxpixels=500000,
         borders=None,
         legend=False,
         figsize=(11.69, 8.27),
         dpi=300, **kwargs):
    """Plot map of spatial probability of deforestation.

    This function plots the spatial probability of deforestation.

    :param input_prob_raster: Path to raster of probabilities.
    :param output_file: Name of the plot file.
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
    colors.append((52429 / vmax, (227 / cmax, 26 / cmax, 28 / cmax, 1)))  # red, p=0.80
    colors.append((1, (0, 0, 0, 1)))  # black
    color_map = LinearSegmentedColormap.from_list(name="mycm", colors=colors,
                                                  N=65535, gamma=1.0)
    color_map.set_under(color=(1, 1, 1, 0))  # transparent, must be associated with vmin

    # Plot raster
    fig = plt.figure(figsize=figsize, dpi=dpi)
    plt.subplot(111)
    plt.imshow(ov_arr, cmap=color_map, extent=extent,
               vmin=0.01, vmax=65535)
    if borders is not None:
        plot_layer(borders, symbol="k-", **kwargs)

    # Legend
    if legend is True:
        t = np.linspace(1, 65535, 5, endpoint=True)
        cbar = plt.colorbar(ticks=t, orientation="vertical",
                            shrink=0.5, aspect=20)
        vl = np.linspace(0, 1, 5, endpoint=True)
        cbar.ax.set_yticklabels(vl)

    # Save image
    figure_as_image(fig, output_file)

    # Return figure
    return(fig)


# plot.obs
def obs(sample,
        name_forest_var,
        input_fcc_raster,
        output_file="obs.png",
        zoom=None,
        s=20,
        figsize=(11.69, 8.27),
        dpi=300):
    """Plot the sample points over the forest map.

    This function plots the sample points over the forest map. Green
    is the remaining forest (value 1), red is the deforestation (value
    0).

    :param sample: Pandas DataFrame with observation coordinates (X, Y).
    :param name_forest_var: Name of the forest variable in sample DataFrame.
    :param input_fcc_raster: Path to forest-cover change raster.
    :param output_file: Name of the plot file.
    :param zoom: Zoom to region (xmin, xmax, ymin, ymax).
    :param s: Marker size for sample points.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.

    :return: A Matplotlib figure of the sample points.

    """

    # Load raster and band
    rasterR = gdal.Open(input_fcc_raster, gdal.GA_ReadOnly)
    rasterB = rasterR.GetRasterBand(1)
    rasterND = rasterB.GetNoDataValue()
    gt = rasterR.GetGeoTransform()
    ncol = rasterR.RasterXSize
    nrow = rasterR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]
    extent = [Xmin, Xmax, Ymin, Ymax]

    # Overviews
    if rasterB.GetOverviewCount() == 0:
        # Build overviews
        print("Build overview")
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
        rasterR.BuildOverviews("nearest", [4, 8, 16, 32])

    # Get data from finest overview
    ov_band = rasterB.GetOverview(0)
    ov_arr = ov_band.ReadAsArray()
    ov_arr[ov_arr == rasterND] = 2

    # Dereference driver
    rasterB = None
    del(rasterR)

    # Colormap
    colors = []
    cmax = 255.0  # float for division
    colors.append((227 / cmax, 26 / cmax, 28 / cmax, 1))  # red
    colors.append((34 / cmax, 139 / cmax, 34 / cmax, 1))  # forest green
    colors.append((0, 0, 0, 0))  # transparent
    color_map = ListedColormap(colors)

    # Plot raster
    fig = plt.figure(figsize=figsize, dpi=dpi)
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
    plt.scatter(x_defor, y_defor,
                color="darkred", s=s)
    plt.scatter(x_for, y_for,
                color="darkgreen", s=s)
    if zoom is not None:
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])

    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi=dpi, bbox_inches="tight")
    return(fig)


# plot.differences
def differences(input_raster,
                output_file="differences.png",
                borders=None,
                zoom=None,
                figsize=(11.69, 8.27),
                dpi=300, **kwargs):
    """Plot a map to compare outputs.

    This function plots a map of differences between two rasters of
    predictions.

    :param input_raster: Path to raster of diffeences.
    :param output_file: Name of the plot file.
    :param borders: Vector file to be plotted.
    :param zoom: Zoom to region (xmin, xmax, ymin, ymax).
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :param \\**kwargs: see below.

    :Keyword Arguments: Additional arguments to plot borders.

    :return: A Matplotlib figure of the forest map.

    """

    # Load raster and band
    rasterR = gdal.Open(input_raster, gdal.GA_ReadOnly)
    rasterB = rasterR.GetRasterBand(1)
    rasterND = rasterB.GetNoDataValue()
    gt = rasterR.GetGeoTransform()
    ncol = rasterR.RasterXSize
    nrow = rasterR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]
    extent = [Xmin, Xmax, Ymin, Ymax]

    # Overviews
    if (rasterB.GetOverviewCount() == 0):
        # Build overviews
        print("Build overview")
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
        rasterR.BuildOverviews("nearest", [4, 8, 16, 32])

    # Get data from finest overview
    ov_band = rasterB.GetOverview(0)
    ov_arr = ov_band.ReadAsArray()
    ov_arr[ov_arr == rasterND] = 4

    # Dereference driver
    rasterB = None
    del(rasterR)

    # Colormap
    colors = []
    cmax = 255.0  # float for division
    # 00: true positive (red)
    colors.append((227 / cmax, 26 / cmax, 28 / cmax, 1))
    # 11: true negative (forest green)
    colors.append((34 / cmax, 139 / cmax, 34 / cmax, 1))
    # 10: false negative (light blue)
    colors.append((65 / cmax, 105 / cmax, 225 / cmax, 1))
    # 01: false positive (navy blue)
    colors.append((176 / cmax, 216 / cmax, 230 / cmax, 1))
    colors.append((0, 0, 0, 0))  # transparent
    color_map = ListedColormap(colors)

    # Plot raster
    place = 111 if zoom is None else 121
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax1 = plt.subplot(place)
    ax1.set_frame_on(False)
    ax1.set_xticks([])
    ax1.set_yticks([])
    plt.imshow(ov_arr, cmap=color_map, extent=extent)
    if borders is not None:
        plot_layer(borders, symbol="k-", **kwargs)
    plt.axis("off")
    if zoom is not None:
        z = Rectangle(
            (zoom[0], zoom[2]),
            zoom[1] - zoom[0],
            zoom[3] - zoom[2],
            fill=False
        )
        ax1.add_patch(z)
        ax2 = plt.subplot(222)
        plt.imshow(ov_arr, cmap=color_map, extent=extent)
        plt.xlim(zoom[0], zoom[1])
        plt.ylim(zoom[2], zoom[3])
        ax2.set_xticks([])
        ax2.set_yticks([])

    # Save and return figure
    fig.tight_layout()
    fig.savefig(output_file, dpi="figure", bbox_inches="tight")
    return(fig)


# plot.var
def var(var_dir,
        output_file="var.pdf",
        gridsize=(3, 3),
        figsize=(11.69, 8.27),
        dpi=300):
    """Plot variable maps.

    This function plots variable maps.

    :param var_dir: Path to variable directory.
    :param output_file: Name of the plot file.
    :param grid_size: Grid size per page.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :return: List of Matplotlib figures.

    """

    # Raster list
    var_tif = var_dir + "/*.tif"
    raster_list = glob(var_tif)
    raster_list.sort()
    nrast = len(raster_list)

    # The PDF document
    pdf_pages = PdfPages(output_file)
    # Generate the pages
    ny = gridsize[0]
    nx = gridsize[1]
    nplot_per_page = ny * nx
    # List of figures to be returned
    figures = []

    # Loop on raster files
    for i in range(nrast):

        # Create a figure instance (ie. a new page) if needed
        if i % nplot_per_page == 0:
            fig = plt.figure(figsize=figsize, dpi=dpi)

        # Open raster and get band
        r = gdal.Open(raster_list[i], gdal.GA_ReadOnly)
        b = r.GetRasterBand(1)
        ND = b.GetNoDataValue()
        if ND is None:
            print("NoData value is not specified \
            for input raster file " + raster_list[i])
            sys.exit(1)

        # Raster name
        base_name = os.path.basename(raster_list[i])
        index_dot = base_name.index(".")
        raster_name = base_name[:index_dot]

        # Raster info
        gt = r.GetGeoTransform()
        ncol = r.RasterXSize
        nrow = r.RasterYSize
        Xmin = gt[0]
        Xmax = gt[0] + gt[1] * ncol
        Ymin = gt[3] + gt[5] * nrow
        Ymax = gt[3]
        extent = [Xmin, Xmax, Ymin, Ymax]

        # Overviews
        if b.GetOverviewCount() == 0:
            # Build overviews
            print("Build overview")
            gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
            r.BuildOverviews("nearest", [4, 8, 16, 32])
        # Get data from finest overview
        ov_band = b.GetOverview(0)
        ov_arr = ov_band.ReadAsArray()
        mov_arr = np.ma.array(ov_arr, mask=(ov_arr == ND))
        # Plot raster
        ax = plt.subplot2grid(gridsize,
                              ((i % nplot_per_page) // nx, i % nx))
        ax.set_frame_on(False)
        ax.set_xticks([])
        ax.set_yticks([])
        plt.imshow(mov_arr, extent=extent)
        plt.title(raster_name)
        plt.axis("off")

        # Close the page if needed
        if (i + 1) % nplot_per_page == 0 or (i + 1) == nrast:
            plt.tight_layout()
            figures.append(fig)
            pdf_pages.savefig(fig)

    # Write the PDF document to the disk
    pdf_pages.close()
    return(figures)


# plot.rho
def rho(input_rho_raster,
        output_file="rho.png",
        borders=None,
        figsize=(11.69, 8.27),
        dpi=300, **kwargs):
    """Plot map of spatial random effects (rho).

    This function plots the spatial random effects.

    :param input_rho_raster: Path to raster of random effects.
    :param output_file: Name of the plot file.
    :param borders: Vector file to be plotted.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.
    :param \\**kwargs: see below.

    :Keyword Arguments: Additional arguments to plot borders.

    :return: A Matplotlib figure of the map of spatial random effects.

    """

    # Load raster and band
    rasterR = gdal.Open(input_rho_raster, gdal.GA_ReadOnly)
    rasterB = rasterR.GetRasterBand(1)
    gt = rasterR.GetGeoTransform()
    ncol = rasterR.RasterXSize
    nrow = rasterR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]
    extent = [Xmin, Xmax, Ymin, Ymax]

    # Overviews
    if rasterB.GetOverviewCount() == 0:
        # Build overviews
        print("Build overview")
        gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
        rasterR.BuildOverviews("average", [2, 4, 8, 16, 32])

    # Get data
    # ov_band = rasterB.GetOverview(0)
    ov_band = rasterB
    ov_arr = ov_band.ReadAsArray()
    ov_arr[ov_arr == -9999] = np.nan

    # Compute 99% quantiles
    rho_min, rho_max = np.nanpercentile(ov_arr, [0.5, 99.5])
    rho_bound = np.max((-rho_min, rho_max))

    # Dereference driver
    rasterB = None
    del(rasterR)

    # Plot raster and save
    fig = plt.figure(figsize=figsize, dpi=dpi)
    plt.subplot(111)
    plt.imshow(ov_arr, cmap="RdYlGn_r", extent=extent,
               vmin=-rho_bound, vmax=rho_bound)
    if borders is not None:
        plot_layer(borders, symbol="k-", **kwargs)
    plt.colorbar()
    figure_as_image(fig, output_file)

    # Return figure
    return(fig)


# freq_prob
def freq_prob(stats,
              output_file="freq_prob.png",
              figsize=None,
              dpi=300):
    """Plot distribution of probability values.

    This function plots the distribution of the probability values.

    :param stats: Tuple of statistics (counts, threshold, error,
        hectares) returned by deforestprob.deforest().
    :param output_file: Name of the plot file.
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.

    :return: A Matplotlib figure of the distribution of the
        probability values.

    """

    # Get data from stats
    frequences = stats[0]
    threshold = stats[1]

    # Plot figure and save
    fig = plt.figure(figsize=figsize, dpi=dpi)
    plt.subplot(111)
    plt.plot(frequences, "bo")
    plt.title("Frequencies of deforestation probabilities")
    plt.axvline(x=threshold, color='k', linestyle='--')

    # Save and return figure
    fig.savefig(output_file)
    return(fig)

# End
