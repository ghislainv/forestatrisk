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
from glob import glob
import os
import sys

# Third party imports
import numpy as np
from osgeo import gdal
import pandas as pd
from patsy import build_design_matrices

# Local application imports
from ..misc import invlogit, rescale
from ..misc import progress_bar, makeblock


# predict_binomial_iCAR
def predict_binomial_iCAR(model, new_data, rhos):
    """Function to return the predictions of a model_binomial_iCAR model.

    Function to return the predictions of a model_binomial_iCAR model
    for a new data-set. In this function, rho values for spatial cells
    are directly provided and not obtained from the model.

    :param model: The model_binomial_iCAR model to predict from.
    :param new_data: Pandas DataFrame including explicative variables.
    :param rhos: Spatial random effects for each observation (row) in new_data.
    :return: Predictions (probabilities).

    """

    (new_x,) = build_design_matrices([model._x_design_info],
                                     new_data)
    new_X = new_x[:, :-1]
    return (invlogit(np.dot(new_X, model.betas) + rhos))


# predict
def predict_raster_binomial_iCAR(model, var_dir="data",
                                 input_cell_raster="output/rho.tif",
                                 input_forest_raster="data/forest.tif",
                                 output_file="output/pred_binomial_iCAR.tif",
                                 blk_rows=128):
    """Predict the spatial probability of deforestation from a model.

    This function predicts the spatial probability of deforestation
    from a model_binomial_iCAR model. Computation are done by block and
    can be performed on large geographical areas.

    :param model: The model_binomial_iCAR model to predict from.
    :param var_dir: Directory with rasters (.tif) of explicative variables.
    :param input_cell_raster: Path to raster of rho values for spatial cells.
    :param input_forest_raster: Path to forest raster (1 for forest).
    :param output_file: Name of the raster file to output the probability map.
    :param blk_rows: If > 0, number of rows for computation by block.

    """

    # Mask on forest
    fmaskR = gdal.Open(input_forest_raster)
    fmaskB = fmaskR.GetRasterBand(1)

    # Landscape variables from forest raster
    gt = fmaskR.GetGeoTransform()
    ncol = fmaskR.RasterXSize
    nrow = fmaskR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]

    # Raster list
    var_tif = var_dir + "/*.tif"
    raster_list = glob(var_tif)
    raster_list.sort()  # Sort names
    raster_list.append(input_cell_raster)
    raster_names = []
    for i in range(len(raster_list)):
        fname = os.path.basename(raster_list[i])
        index_dot = fname.index(".")
        raster_names.append(fname[:index_dot])
    raster_names.append("fmask")

    # Make vrt with gdalbuildvrt
    print("Make virtual raster with variables as raster bands")
    param = gdal.BuildVRTOptions(resolution="user",
                                 outputBounds=(Xmin, Ymin, Xmax, Ymax),
                                 xRes=gt[1], yRes=-gt[5],
                                 separate=True)
    gdal.BuildVRT("/vsimem/var.vrt", raster_list, options=param)
    stack = gdal.Open("/vsimem/var.vrt")
    nband = stack.RasterCount
    proj = stack.GetProjection()

    # List of nodata values
    bandND = np.zeros(nband)
    for k in range(nband):
        band = stack.GetRasterBand(k + 1)
        bandND[k] = band.GetNoDataValue()
        if (bandND[k] is None) or (bandND[k] is np.nan):
            print("NoData value is not specified for"
                  " input raster file {}".format(k))
            sys.exit(1)
    bandND = bandND.astype(np.float32)

    # Make blocks
    blockinfo = makeblock("/vsimem/var.vrt", blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Raster of predictions
    print("Create a raster file on disk for projections")
    driver = gdal.GetDriverByName("GTiff")
    Pdrv = driver.Create(output_file, ncol, nrow, 1,
                         gdal.GDT_UInt16,
                         ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"])
    Pdrv.SetGeoTransform(gt)
    Pdrv.SetProjection(proj)
    Pband = Pdrv.GetRasterBand(1)
    Pband.SetNoDataValue(0)

    # Predict by block
    # Message
    print("Predict deforestation probability by block")
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Number of pixels
        npix = nx[px] * ny[py]
        # Data for one block of the stack (shape = (nband,nrow,ncol))
        data = stack.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Replace ND values with -9999
        for i in range(nband):
            data[i][np.nonzero(data[i] == bandND[i])] = -9999
        # Forest mask
        fmaskA = fmaskB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        fmaskA = fmaskA.astype(np.float32)  # From uint to float
        fmaskA[np.nonzero(fmaskA != 1)] = -9999
        fmaskA = fmaskA[np.newaxis, :, :]
        # Concatenate forest mask with stack
        data = np.concatenate((data, fmaskA), axis=0)
        # Transpose and reshape to 2D array
        data = data.transpose(1, 2, 0)
        data = data.reshape(npix, nband + 1)
        # Observations without NA
        w = np.nonzero(~(data == -9999).any(axis=1))
        # Remove observations with NA
        data = data[w]
        # Transform into a pandas DataFrame
        df = pd.DataFrame(data)
        df.columns = raster_names
        # Add fake "cell" column
        df["cell"] = 0
        # Predict with binomial iCAR model
        pred = np.zeros(npix)  # Initialize with nodata value (0)
        if len(w[0]) > 0:
            # Get predictions into an array
            p = predict_binomial_iCAR(model,
                                      new_data=df,
                                      rhos=data[:, -2])
            # Rescale and return to pred
            pred[w] = rescale(p)
        # Assign prediction to raster
        pred = pred.reshape(ny[py], nx[px])
        Pband.WriteArray(pred, x[px], y[py])

    # Compute statistics
    print("Compute statistics")
    Pband.FlushCache()  # Write cache data to disk
    Pband.ComputeStatistics(False)

    # # Build overviews
    # print("Build overviews")
    # Pdrv.BuildOverviews("nearest", [4, 8, 16, 32])

    # Dereference driver
    Pband = None
    del(Pdrv)

# End
