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
from ..misc import progress_bar, makeblock


# map_validation
def map_validation(pred, obs, blk_rows=128):
    """Compute accuracy indices based on predicted and observed
    forest-cover change (fcc) maps.

    Compute the Overall Accuracy, the Figure of Merit, the
    Specificity, the Sensitivity, the True Skill Statistics and the
    Cohen's Kappa from a confusion matrix built on predictions
    vs. observations.

    :param pred: Raster of predicted fcc.
    :param obs: Raster of observed fcc.
    :param blk_rows: If > 0, number of rows for block (else 256x256).

    :return: A dictionnary of accuracy indices.

    """

    # Load raster and band
    predR = gdal.Open(pred)
    predB = predR.GetRasterBand(1)
    obsR = gdal.Open(obs)
    obsB = obsR.GetRasterBand(1)

    # Make blocks
    blockinfo = makeblock(pred, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Initialize the confusion matrix
    n00 = 0.0
    n10 = 0.0
    n01 = 0.0
    n11 = 0.0

    # Compute the confusion matrix
    print("Compute the confusion matrix")
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Data for one block
        df_pred = predB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        df_pred = 1 - df_pred
        df_obs = obsB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        df_obs = 1 - df_obs
        # Update confusion matrix
        n00 = n00 + np.sum((df_pred == 0) & (df_obs == 0))
        n10 = n10 + np.sum((df_pred == 1) & (df_obs == 0))
        n01 = n01 + np.sum((df_pred == 0) & (df_obs == 1))
        n11 = n11 + np.sum((df_pred == 1) & (df_obs == 1))

    # Dereference driver
    predB = None
    del(predR)
    obsB = None
    del(obsR)

    # Print confusion matrix
    mat = pd.DataFrame({"obs0": pd.Series([n00, n10],
                                          index=["pred0", "pred1"]),
                        "obs1": pd.Series([n01, n11],
                                          index=["pred0", "pred1"])})
    print(mat)

    # Accuracy indices
    print("Compute accuracy indices")
    OA = (n11 + n00) / (n11 + n10 + n00 + n01)
    FOM = n11 / (n11 + n10 + n01)
    Sensitivity = n11 / (n11 + n01)
    Specificity = n00 / (n00 + n10)
    TSS = Sensitivity + Specificity - 1
    N = n11 + n10 + n00 + n01
    Observed_accuracy = (n11 + n00) / N
    Expected_accuracy = (
        (n11 + n10) * ((n11 + n01) / N) + (n00 + n01) * ((n00 + n10) / N)) / N
    Kappa = (Observed_accuracy - Expected_accuracy) / (1 - Expected_accuracy)

    r = {"OA": round(OA, 2), "FOM": round(FOM, 2),
         "Sen": round(Sensitivity, 2),
         "Spe": round(Specificity, 2),
         "TSS": round(TSS, 2), "K": round(Kappa, 2)}

    return r

# End
