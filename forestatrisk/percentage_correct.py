#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Import
from __future__ import division, print_function  # Python 3 compatibility
import numpy as np
from osgeo import gdal
from .miscellaneous import progress_bar


# Make
def make_square(rasterfile, square_size=33):
    """Compute block information.

    This function computes block information from the caracteristics
    of a raster file and an indication on the number of rows to
    consider.

    :param rasterfile: path to a raster file.
    :param square_size: pixel number to define square side size.

    :return: a tuple of length 6 including square number, square number
    on x axis, square number on y axis, square offsets on x axis, square
    offsets on y axis, square sizes on x axis, square sizes on y axis.

    """

    r = gdal.Open(rasterfile)
    # Landscape variables
    ncol = r.RasterXSize
    nrow = r.RasterYSize
    # Number of squares
    nsquare_x = int(np.ceil(ncol / square_size))
    nsquare_y = int(np.ceil(nrow / square_size))
    nsquare = nsquare_x * nsquare_y
    # Upper-left coordinates of each square
    x = np.arange(0, ncol, square_size, dtype=np.int).tolist()
    y = np.arange(0, nrow, square_size, dtype=np.int).tolist()
    # Size (number of col and row) of each square
    nx = [square_size] * nsquare_x
    ny = [square_size] * nsquare_y
    # Modify last values of nx and ny
    if (ncol % square_size) > 0:
        nx[-1] = ncol % square_size
    if (nrow % square_size) > 0:
        ny[-1] = nrow % square_size
    # b = None
    del r
    return (nsquare, nsquare_x, nsquare_y, x, y, nx, ny)


# Percentage correct in a window
def perc_correct_w(wobs, wpred, cat):
    """Compute the percentage of correct pixels in a window.

    This function computes the percentage of correct pixels given one
    matrix of observations and one matrix of predictions.

    :param wobs: nparray of observations.
    :param wpred: nparray of predictions.
    :param cat: categories to consider.

    :return: a tuple with percentage and weight.

    """

    npix = np.isin(wobs, cat).sum()
    perc = 0.0
    for k in cat:
        # Numbers
        nobs = (wobs == k).sum()
        npred = (wpred == k).sum()
        # Proportions
        prop_obs = nobs / npix
        prop_pred = npred / npix
        # Percentage correct
        perc += min(prop_obs, prop_pred)

    return((perc, npix))


# percentage_correct
def percentage_correct(r_obs, r_pred, categories=[0, 1],
                       square_size=50, output_file="npix.txt"):
    """Compute non-deforested and deforested pixels per square.

    This function computes the number of non-deforested and deforested
    pixels in squares of a given size for both a raster of predictions
    and a raster of observations. Results can be used to compute
    correlations.

    :param r_obs: path to raster of observations.
    :param r_pred: path to raster of predictions.
    :param categories: categories to consider.
    :param square_size: size of the square side in number of pixels.
    :param output_file: path to result file.

    :return: a pandas DataFrame, each row being one square.

    """

    # Landscape variables from raster of observations
    obsR = gdal.Open(r_obs)
    gt = obsR.GetGeoTransform()
    ncol_r = obsR.RasterXSize
    nrow_r = obsR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol_r
    Ymin = gt[3] + gt[5] * nrow_r
    Ymax = gt[3]

    # Raster list
    raster_list = [r_obs, r_pred]
    raster_list.sort()  # Sort names

    # Make vrt with gdal.BuildVRT
    # Note: Extent and resolution from forest raster!
    print("Make virtual raster with variables as raster bands")
    param = gdal.BuildVRTOptions(resolution="user",
                                 outputBounds=(Xmin, Ymin, Xmax, Ymax),
                                 xRes=gt[1], yRes=-gt[5],
                                 separate=True)
    gdal.BuildVRT("/vsimem/var.vrt", raster_list, options=param)
    stack = gdal.Open("/vsimem/var.vrt")

    # Make squares
    squareinfo = make_square(r_obs, square_size)
    nsquare = squareinfo[0]
    nsquare_x = squareinfo[1]
    x = squareinfo[3]
    y = squareinfo[4]
    nx = squareinfo[5]
    ny = squareinfo[6]
    print("Divide region in {} squares".format(nsquare))

    # Window resolution
    wres = [25, 50]
    nres = len(wres)

    # 3D-Array to store the number of pixels per square and category
    # for observations and predictions
    ncat = len(categories)
    square_cat = np.empty(shape=(2, nsquare, ncat), dtype=np.int)

    # Arrays to store results by square and wres
    weighted_perc = np.zeros(shape=(nsquare, nres), dtype=np.float)
    sum_of_weights = np.zeros(shape=(nsquare, nres), dtype=np.int)

    # Loop on squares
    print("Loop on squares")
    for s in range(nsquare):
        # Progress bar
        progress_bar(nsquare, s + 1)
        # Position in 1D-arrays
        px = s % nsquare_x
        py = s // nsquare_x
        # Data for one square
        array_stack = stack.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Loop on categories
        for k in range(ncat):
            c = categories[k]
            square_cat[:, s, k] = (array_stack == c).sum(
                axis=2).sum(axis=1)
        # Loop on window resolution
        for r in range(nres):
            wr = wres[r]
            nw = 40 // wr
            for i in range(nw):
                for j in range(nw):
                    wstack = array_stack[:, (wr * i):(wr * (i + 1) - 1),
                                         (wr * j):(wr * (j + 1) - 1)]
                    wobs = wstack[0, :, :]
                    wpred = wstack[1, :, :]
                    (perc, weight) = perc_correct_w(wobs,
                                                    wpred,
                                                    categories)
                    weighted_perc[s, r] += weight * perc
                    sum_of_weights[s, r] += weight

    # Summarize results obtained per wres
    perc_by_res = np.zeros(nres, dtype=np.float)
    for r in range(nres):
        perc_by_res[r] = weighted_perc.sum(axis=1) / sum_of_weights.sum(axis=1)

    # =============================================
    # Results
    # =============================================

    # Export to txt file
    print("Export results to file " + output_file)
    np.savetxt(output_file, perc_by_res, header=['res' + i for i in wres],
               fmt="%s", delimiter=",", comments="")

    # Return the result
    return(perc_by_res)

# End
