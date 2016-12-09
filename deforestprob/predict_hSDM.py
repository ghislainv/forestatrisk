#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# ==============================================================================

# Import
from osgeo import gdal
from tqdm import tqdm
from glob import glob
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from patsy import build_design_matrices
import numpy as np
import os
import sys
import makeblock
from miscellaneous import invlogit, rescale, figure_as_image


# predict
def predict(hSDM_model, new_data, rhos):
    """Function to return the predictions of a hSDM_binomial_iCAR model.

    Function to return the predictions of a hSDM_binomial_iCAR model
    for a new data-set. In this function, rho values for spatial cells
    are directly provided and not obtained from the model.

    :param hSDM_model: hSDM_binomial_iCAR to predict from.
    :param new_data: pandas DataFrame including explicative variables.
    :param rhos: spatial random effects for each observation (row) in new_data.
    :return: prediction (a probability).

    """

    (new_x,) = build_design_matrices([hSDM_model._x_design_info],
                                     new_data)
    new_X = new_x[:, :-1]
    return (invlogit(np.dot(new_X, hSDM_model.betas) + rhos))


# predict_hSDM
def predict_hSDM(hSDM_model, var_dir="data",
                 input_cell_raster="output/rho.tif",
                 input_forest_raster="data/forest.tif",
                 output_file="output/pred_hSDM.tif",
                 blk_rows=128):
    """Predict the spatial probability of deforestation from a hSDM model.

    This function predicts the spatial probability of deforestation
    from a hSDM_binomial_iCAR model. Computation are done by block and
    can be performed on large geographical areas.

    :param hSDM_model: hSDM_binomial_iCAR to predict from.
    :param var_dir: directory with rasters (.tif) of explicative variables.
    :param input_cell_raster: path to raster of rho values for spatial cells.
    :param input_forest_raster: path to forest raster (1 for forest).
    :param output_file: name of the raster file to output the probability map.
    :param blk_rows: if > 0, number of rows for computation by block.
    :return: a figure object for the probability map that can be plotted.

    """

    # Mask on forest
    fmaskR = gdal.Open(input_forest_raster)
    fmaskB = fmaskR.GetRasterBand(1)

    # Raster list
    var_tif = var_dir + "/*.tif"
    raster_list = glob(var_tif)
    raster_list.sort()
    raster_list.append(input_cell_raster)
    raster_names = []
    for i in range(len(raster_list)):
        fname = os.path.basename(raster_list[i])
        index_dot = fname.index(".")
        raster_names.append(fname[:index_dot])
    raster_names.append("fmask")

    # Make vrt with gdalbuildvrt
    print("Make virtual raster with variables as raster bands")
    inputvar = " ".join(raster_list)
    output_vrt = var_dir + "/var.vrt"
    os.system("gdalbuildvrt -separate -o " + output_vrt + " " + inputvar)

    # Load vrt file
    stack = gdal.Open(output_vrt)
    ncol = stack.RasterXSize
    nrow = stack.RasterYSize
    nband = stack.RasterCount
    gt = stack.GetGeoTransform()
    proj = stack.GetProjection()

    # List of nodata values
    bandND = np.zeros(nband)
    for k in range(nband):
        band = stack.GetRasterBand(k + 1)
        bandND[k] = band.GetNoDataValue()
        if (bandND[k] is None) or (bandND[k] is np.nan):
            print("NoData value is not specified for input raster file %d" % k)
            sys.exit(1)
    bandND = bandND.astype(np.float32)

    # Make blocks
    blockinfo = makeblock(output_vrt, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in " + str(nblock) + " blocks")

    # Rasters of predictions
    print("Create a raster file on disk for projections")
    driver = gdal.GetDriverByName("GTiff")
    Pdrv = driver.Create(output_file, ncol, nrow, 1,
                         gdal.GDT_UInt16,
                         ["COMPRESS=LZW", "PREDICTOR=2"])
    Pdrv.SetGeoTransform(gt)
    Pdrv.SetProjection(proj)
    Pband = Pdrv.GetRasterBand(1)
    Pband.SetNoDataValue(0)

    # Predict by block
    # Message
    print("Predict deforestation probability by block")
    # Loop on blocks of data
    for b in tqdm(range(nblock)):
        # Position in 1D-arrays
        px = b % nblock_x
        py = b / nblock_x
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
        # Predict with hSDM model
        pred = np.zeros(npix)  # Initialize with nodata value (0)
        if len(w[0]) > 0:
            # Get predictions into an array
            p = predict(hSDM_model,
                        new_data=df,
                        rhos=data[:, -2])
            # Avoid nodata value (0) for low proba
            p[p < 1e-06] = 1e-06
            # np.rint: round to nearest integer
            p = np.rint(1000000 * p)
            # Rescale and return to pred
            pred[w] = rescale(p)
        # Assign prediction to raster
        pred = pred.reshape(ny[py], nx[px])
        Pband.WriteArray(pred, x[px], y[py])

    # Compute statistics
    print("Compute statistics")
    Pband.FlushCache()  # Write cache data to disk
    Pband.ComputeStatistics(False)

    # Build overviews
    print("Build overview")
    Pdrv.BuildOverviews("average", [8, 16, 32])

    # Get data from finest overview
    ov_band = Pband.GetOverview(0)
    ov_arr = ov_band.ReadAsArray()

    # Dereference driver
    Pband = None
    del(Pdrv)

    # Colormap
    colors = []
    colors.append((0, (0, 0, 0, 0)))
    colors.append((1 / 65535., (34 / 255., 139 / 255., 34 / 255., 1)))
    colors.append((45000 / 65535., (1, 165 / 255., 0, 1)))
    colors.append((55000 / 65535., (1, 0, 0, 1)))
    colors.append((1, (0, 0, 0, 1)))
    color_map = LinearSegmentedColormap.from_list(name="mycm", colors=colors,
                                                  N=65535, gamma=1.0)

    # Plot
    print("Plot map")
    # Figure name
    fig_name = output_file
    index_dot = output_file.index(".")
    fig_name = fig_name[:index_dot]
    fig_name = fig_name + ".png"
    # Plot raster and save
    fig = plt.figure()
    plt.subplot(111)
    plt.imshow(ov_arr, cmap=color_map)
    plt.close(fig)
    fig_img = figure_as_image(fig, fig_name, dpi=200)

    # Return figure
    return(fig_img)

# End
