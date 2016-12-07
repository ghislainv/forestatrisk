#!/usr/bin/python

# ============================================================================
#
# predict_hSDM.py
#
# Predict deforestation probability from hSDM model
#
# Ghislain Vieilledent <ghislain.vieilledent@cirad.fr>
# November 2016
#
# ============================================================================

# =============================================
# Libraries
# =============================================

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
import deforestprob as dfp

# =============================================
# Functions
# =============================================


# Function to rescale from 1-1000000 to 1-65535 (UInt16)
def rescale(value):
    return (((value - 1) * 65534 / 999999) + 1)


# Inverse-logit
def invlogit(x):
    Result = 1/(1+np.exp(-x))
    return (Result)


# Predict function for hSDM model
def predict(hSDM_model, new_data, rhos):
    (new_x,) = build_design_matrices([hSDM_model._x_design_info],
                                     new_data)
    new_X = new_x[:, :-1]
    return (invlogit(np.dot(new_X, hSDM_model.betas) + rhos))


# Saving a matplotlib.pyplot figure as a border-less frame-less image
def SaveFigureAsImage(fileName, fig=None, dpi=300, **kwargs):
    ''' Save a Matplotlib figure as an image without borders or frames.
        Args:
            fileName (str): String that ends in .png etc.
            fig (Matplotlib figure instance): figure you want to \
            save as the image
        Keyword Args:
            orig_size (tuple): width, height of the original image \
            used to maintain
            aspect ratio.
    '''
    fig_size = fig.get_size_inches()
    w, h = fig_size[0], fig_size[1]
    fig.patch.set_alpha(0)
    if "orig_size" in kwargs:  # Aspect ratio scaling if required
        w, h = kwargs["orig_size"]
        w2, h2 = fig_size[0], fig_size[1]
        h2 == (w2/w)*h
        fig.set_size_inches([w2, h2])
        fig.set_dpi((w2/w)*fig.get_dpi())
    a = fig.gca()
    a.set_frame_on(False)
    a.set_xticks([])
    a.set_yticks([])
    plt.axis('off')
    plt.xlim(0, h)
    plt.ylim(w, 0)
    fig.savefig(fileName, transparent=True, bbox_inches='tight',
                pad_inches=0, dpi=dpi)

# =============================================
# predict_hSDM
# =============================================


def predict_hSDM(hSDM_model, var_dir="data",
                 input_cell_raster="output/rho.tif",
                 input_forest_raster="data/forest.tif",
                 output_file="output/pred_hSDM.tif"):

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
        band = stack.GetRasterBand(k+1)
        bandND[k] = band.GetNoDataValue()
        if (bandND[k] is None) or (bandND[k] is np.nan):
            print("NoData value is not specified for input raster file %d" % k)
            sys.exit(1)
    bandND = bandND.astype(np.float32)

    # Make blocks
    blockinfo = dfp.makeblock(output_vrt, byrows=True, nrows=128)
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
        npix = nx[px]*ny[py]
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
        data = data.reshape(npix, nband+1)
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
            p = np.rint(1000000*p)
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
    del Pdrv

    # Colormap
    colors = []
    colors.append((0, (0, 0, 0, 0)))
    colors.append((1/65535., (34/255., 139/255., 34/255., 1)))
    colors.append((45000/65535., (1, 165/255., 0, 1)))
    colors.append((55000/65535., (1, 0, 0, 1)))
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
    fig = plt.figure(1)
    plt.subplot(111)
    plt.imshow(ov_arr, cmap=color_map)
    plt.close(fig)
    SaveFigureAsImage(fig_name, fig, dpi=200)

    # Return figure
    return (fig)

# ============================================================================
# End of predict_hSDM.py
# ============================================================================
