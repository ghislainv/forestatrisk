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

# Third party imports
import numpy as np
from osgeo import gdal
import pandas as pd

# Local application imports
from ..misc import progress_bar


# Make
def make_square(rasterfile, square_size=33):
    """Compute block information. **(deprecated)**

    This is an internal function for ``.validation_npix()``\\ .

    This function computes block information from the caracteristics
    of a raster file and an indication on the number of rows to
    consider.

    :param rasterfile: Path to a raster file.
    :param square_size: Pixel number to define square side size.

    :return: A tuple of length 6 including square number, square number
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


# validation_Dha
def validation_npix(r_pred, r_obs, value_f=1, value_d=0,
                    square_size=33, output_file="npix.txt"):
    """Compute non-deforested and deforested pixels per
    square. **(deprecated)**

    This function computes the number of non-deforested and deforested
    pixels in squares of a given size for both a raster of predictions
    and a raster of observations. Results can be used to compute
    correlations.

    :param r_pred: Path to raster of predictions.
    :param r_obs: Path to raster of observations.
    :param value_f: Value of non-deforested pixels in rasters.
    :param value_d: Value of deforested pixels in rasters.
    :param square_size: Size of the square side in number of pixels.
    :param output_file: Path to result file.

    :return: A pandas DataFrame, each row being one square.

    """

    # Load raster and band
    predR = gdal.Open(r_pred)
    predB = predR.GetRasterBand(1)
    obsR = gdal.Open(r_obs)
    obsB = obsR.GetRasterBand(1)

    # Make blocks
    squareinfo = make_square(r_pred, square_size)
    nsquare = squareinfo[0]
    nsquare_x = squareinfo[1]
    x = squareinfo[3]
    y = squareinfo[4]
    nx = squareinfo[5]
    ny = squareinfo[6]
    print("Divide region in {} squares".format(nsquare))

    # Initialize the number of pixels per square
    npix_pred_f = np.zeros(nsquare, dtype=np.int)
    npix_obs_f = np.zeros(nsquare, dtype=np.int)
    npix_pred_d = np.zeros(nsquare, dtype=np.int)
    npix_obs_d = np.zeros(nsquare, dtype=np.int)

    # Compute the number of pixels
    print("Compute the number of pixels per square")
    # Loop on squares
    for s in range(nsquare):
        # Progress bar
        progress_bar(nsquare, s + 1)
        # Position in 1D-arrays
        px = s % nsquare_x
        py = s // nsquare_x
        # Data for one square
        array_pred = predB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        array_obs = obsB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Identify pixels (x/y coordinates) equal to value
        pix_pred_f = np.nonzero(array_pred == value_f)
        pix_obs_f = np.nonzero(array_obs == value_f)
        npix_pred_f[s] = len(pix_pred_f[0])
        npix_obs_f[s] = len(pix_obs_f[0])
        # Identify pixels (x/y coordinates) equal to value
        pix_pred_d = np.nonzero(array_pred == value_d)
        pix_obs_d = np.nonzero(array_obs == value_d)
        npix_pred_d[s] = len(pix_pred_d[0])
        npix_obs_d[s] = len(pix_obs_d[0])

    # =============================================
    # Export and return value
    # =============================================

    print("Export results to file " + output_file)

    # Export to file
    npix_arr = np.column_stack((npix_obs_f, npix_pred_f,
                                npix_obs_d, npix_pred_d))
    varname_str = "obs_f, pred_f, obs_d, pred_d"
    np.savetxt(output_file, npix_arr, header=varname_str,
               fmt="%s", delimiter=",", comments="")

    # Convert to pandas DataFrame and return the result
    varname_list = ["obs_f", "pred_f", "obs_d", "pred_d"]
    npix_DF = pd.DataFrame(npix_arr, columns=varname_list)
    return npix_DF

# End
