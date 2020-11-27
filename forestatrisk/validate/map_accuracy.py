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

# Local application imports
from ..misc import progress_bar, makeblock


# Percentage_correct
def map_confmat(r_obs0, r_obs1, r_pred0, r_pred1,
                blk_rows=0):
    """Compute a confusion matrix.

    This function computes a confusion matrix at a given
    resolution. Number of pixels in each category (0, 1) and in each
    spatial cell are given by r_obs\\* and r_pred\\* rasters.

    :param r_obs0: Raster counting the number of 0 for observations.
    :param r_obs1: Raster counting the number of 1 for observations.
    :param r_pred0: Raster counting the number of 0 for predictions.
    :param r_pred1: Raster counting the number of 1 for predictions.
    :param blk_rows: If > 0, number of lines per block.

    :return: A numpy array of shape (2,2).

    """

    # Landscape variables from raster of observations
    obsR = gdal.Open(r_obs0)
    gt = obsR.GetGeoTransform()
    ncol_r = obsR.RasterXSize
    nrow_r = obsR.RasterYSize
    del obsR
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol_r
    Ymin = gt[3] + gt[5] * nrow_r
    Ymax = gt[3]

    # Raster list
    raster_list = [r_obs0, r_obs1, r_pred0, r_pred1]

    # Make vrt with gdal.BuildVRT
    # Note: Extent and resolution from forest raster!
    print("Make virtual raster")
    param = gdal.BuildVRTOptions(resolution="user",
                                 outputBounds=(Xmin, Ymin, Xmax, Ymax),
                                 xRes=gt[1], yRes=-gt[5],
                                 separate=True)
    gdal.BuildVRT("/vsimem/temp.vrt", raster_list, options=param)
    stack = gdal.Open("/vsimem/temp.vrt")

    # Make blocks
    blockinfo = makeblock(r_obs0, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Confusion matrix
    conf_mat = np.zeros((2, 2), dtype=np.int32)

    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Read the data
        data = stack.ReadAsArray(x[px], y[py], nx[px], ny[py]).astype(np.int32)
        # Local confusion matrix
        n00 = np.sum(np.min(data[(0, 2), :, :], axis=0))
        n11 = np.sum(np.min(data[(1, 3), :, :], axis=0))
        n01 = np.sum(np.maximum(0, data[2, :, :] - data[0, :, :]))
        n10 = np.sum(np.maximum(0, data[3, :, :] - data[1, :, :]))
        mat = np.array([n00, n01, n10, n11]).reshape(2, 2)
        conf_mat += mat

    # Close stack
    del stack

    # Return confusion matrix
    return conf_mat


# map_accuracy
def map_accuracy(mat):
    """Compute accuracy indices from a confusion matrix.

    Compute Overall Accuracy, Expected Accuracy, Figure of Merit,
    Specificity, Sensitivity, True Skill Statistics and
    Cohen's Kappa from a confusion matrix.

    :param mat: Confusion matrix. Format: [[n00, n01], [n10, n11]]
        with pred on lines and obs on columns.

    :return: A dictionnary of accuracy indices.

    """

    # Confusion matrix
    n00 = mat[0, 0]
    n01 = mat[0, 1]
    n10 = mat[1, 0]
    n11 = mat[1, 1]

    # Accuracy indices
    N = n11 + n10 + n00 + n01
    OA = (n11 + n00) / N
    FOM = n00 / (n00 + n10 + n01)
    Specificity = n11 / (n11 + n01)
    Sensitivity = n00 / (n00 + n10)
    TSS = Sensitivity + Specificity - 1
    Prob_1and1 = ((n11 + n10) / N) * ((n11 + n01) / N)
    Prob_0and0 = ((n00 + n01) / N) * ((n00 + n10) / N)
    EA = Prob_1and1 + Prob_0and0
    Kappa = (OA - EA) / (1 - EA)

    r = {"OA": OA, "EA": EA,
         "FOM": FOM, "Sen": Sensitivity,
         "Spe": Specificity, "TSS": TSS, "K": Kappa}

    return r

# End
