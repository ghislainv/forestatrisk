#!/usr/bin/python
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
from glob import glob  # To explore files in a folder
import os  # Operating system interfaces
import sys  # To read and write files

# Third party imports
import numpy as np  # For arrays
from osgeo import gdal  # GIS libraries
import pandas as pd  # To export result as a pandas DF

# Local imports
from ..misc import makeblock, progress_bar


# sample()
def sample(nsamp=10000, adapt=True, seed=1234, csize=10,
           var_dir="data",
           input_forest_raster="forest.tif",
           output_file="output/sample.txt",
           blk_rows=0):

    """Sample points and extract raster values.

    This function (i) randomly draws spatial points in deforested and
    forested areas and (ii) extract environmental variable values for
    each spatial point.

    :param nsamp: Number of random spatial points.

    :param adapt: Boolean. Adapt ``nsamp`` to forest area: 1000 for 1 Mha of
        forest, with min=10000 and max=50000. Default to ``True``.

    :param seed: Seed for random number generator.

    :param csize: Spatial cell size in km.

    :param var_dir: Directory with raster data.

    :param input_forest_raster: Name of the forest raster file
       (1=forest, 0=deforested) in the var_dir directory.

    :param output_file: Path to file to save sample points.

    :param blk_rows: If > 0, number of lines per block.

    :return: A Pandas DataFrame, each row being one observation.

    """

    # Set random seed
    np.random.seed(seed)

    # =============================================
    # Sampling pixels
    # =============================================

    print("Sample 2x {} pixels (deforested vs. forest)".format(nsamp))

    # Read defor raster
    forest_raster_file = os.path.join(var_dir, input_forest_raster)
    forestR = gdal.Open(forest_raster_file)
    forestB = forestR.GetRasterBand(1)

    # Make blocks
    blockinfo = makeblock(forest_raster_file, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Number of defor/forest pixels by block
    print("Compute number of deforested and forest pixels per block")
    ndc = 0
    ndc_block = np.zeros(nblock, dtype=np.int)
    nfc = 0
    nfc_block = np.zeros(nblock, dtype=np.int)

    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Read the data
        forest = forestB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Identify pixels (x/y coordinates) which are deforested
        deforpix = np.nonzero(forest == 0)
        ndc_block[b] = len(deforpix[0])  # Number of defor pixels
        ndc += len(deforpix[0])
        # Identify pixels (x/y coordinates) which are forest
        forpix = np.nonzero(forest == 1)
        nfc_block[b] = len(forpix[0])  # Number of forest pixels
        nfc += len(forpix[0])

    # Adapt nsamp to forest area
    if adapt is True:
        gt = forestR.GetGeoTransform()
        pix_area = gt[1] * (-gt[5])
        farea = pix_area * (nfc + ndc) / 10000  # farea in ha
        nsamp_prop = 1000 * farea / 1e6  # 1000 per 1Mha
        if nsamp_prop >= 50000:
            nsamp = 50000
        elif nsamp_prop <= 10000:
            nsamp = 10000
        else:
            nsamp = int(np.rint(nsamp_prop))
    else:
        nsamp = nsamp

    # Proba of drawing a block
    print("Draw blocks at random")
    proba_block_d = ndc_block / ndc
    proba_block_f = nfc_block / nfc
    # Draw block number nsamp times
    block_draw_d = np.random.choice(list(range(nblock)), size=nsamp,
                                    replace=True, p=proba_block_d)
    block_draw_f = np.random.choice(list(range(nblock)), size=nsamp,
                                    replace=True, p=proba_block_f)
    # Number of times the block is drawn
    nblock_draw_d = np.zeros(nblock, dtype=np.int)
    nblock_draw_f = np.zeros(nblock, dtype=np.int)
    for s in range(nsamp):
        nblock_draw_d[block_draw_d[s]] += 1
        nblock_draw_f[block_draw_f[s]] += 1

    # Draw defor/forest pixels in blocks
    print("Draw pixels at random in blocks")
    # Object to store coordinates of selected pixels
    deforselect = np.empty(shape=(0, 2), dtype=np.int)
    forselect = np.empty(shape=(0, 2), dtype=np.int)
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # nbdraw
        nbdraw_d = nblock_draw_d[b]
        nbdraw_f = nblock_draw_f[b]
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Read the data
        forest = forestB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Identify pixels (x/y coordinates) which are deforested
        # !! Values returned in row-major, C-style order (y/x) !!
        deforpix = np.nonzero(forest == 0)
        deforpix = np.transpose((x[px] + deforpix[1],
                                 y[py] + deforpix[0]))
        ndc_block = len(deforpix)
        # Identify pixels (x/y coordinates) which are forested
        forpix = np.nonzero(forest == 1)
        forpix = np.transpose((x[px] + forpix[1],
                               y[py] + forpix[0]))
        nfc_block = len(forpix)
        # Sample deforested pixels
        if nbdraw_d > 0:
            if nbdraw_d < ndc_block:
                i = np.random.choice(ndc_block, size=nbdraw_d,
                                     replace=False)
                deforselect = np.concatenate((deforselect, deforpix[i]),
                                             axis=0)
            else:
                # nbdraw = ndc_block
                deforselect = np.concatenate((deforselect, deforpix),
                                             axis=0)
        # Sample forest pixels
        if nbdraw_f > 0:
            if nbdraw_f < nfc_block:
                i = np.random.choice(nfc_block, size=nbdraw_f,
                                     replace=False)
                forselect = np.concatenate((forselect, forpix[i]),
                                           axis=0)
            else:
                # nbdraw = ndc_block
                forselect = np.concatenate((forselect, forpix),
                                           axis=0)

    # =============================================
    # Compute center of pixel coordinates
    # =============================================

    print("Compute center of pixel coordinates")

    # Landscape variables from forest raster
    gt = forestR.GetGeoTransform()
    ncol_r = forestR.RasterXSize
    nrow_r = forestR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol_r
    Ymin = gt[3] + gt[5] * nrow_r
    Ymax = gt[3]

    # Concatenate selected pixels
    select = np.concatenate((deforselect, forselect), axis=0)

    # Offsets and coordinates #
    xOffset = select[:, 0]
    yOffset = select[:, 1]
    pts_x = (xOffset + 0.5) * gt[1] + gt[0]  # +0.5 for center of pixels
    pts_y = (yOffset + 0.5) * gt[5] + gt[3]  # +0.5 for center of pixels

    # ================================================
    # Compute cell number for spatial autocorrelation
    # ================================================

    # Cell number from region
    print("Compute number of {} x {} km spatial cells".format(csize, csize))
    csize = csize * 1000  # Transform km in m
    ncol = int(np.ceil((Xmax - Xmin) / csize))
    nrow = int(np.ceil((Ymax - Ymin) / csize))
    ncell = ncol * nrow
    print("... {} cells ({} x {})".format(ncell, nrow, ncol))
    # bigI and bigJ are the coordinates of the cells and start at zero
    print("Identify cell number from XY coordinates")
    bigJ = ((pts_x - Xmin) / csize).astype(np.int)
    bigI = ((Ymax - pts_y) / csize).astype(np.int)
    cell = bigI * ncol + bigJ  # Cell number starts at zero

    # =============================================
    # Extract values from rasters
    # =============================================

    # Raster list
    var_tif = var_dir + "/*.tif"
    raster_list = glob(var_tif)
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

    # List of nodata values
    nband = stack.RasterCount
    bandND = np.zeros(nband)
    for k in range(nband):
        band = stack.GetRasterBand(k + 1)
        bandND[k] = band.GetNoDataValue()
        if bandND[k] is None:
            print("NoData value is not specified \
            for input raster file " + raster_list[k])
            sys.exit(1)

    # Numpy array to store values
    nobs = select.shape[0]
    val = np.zeros(shape=(nobs, nband), dtype=np.float32)

    # Extract raster values
    print("Extract raster values for selected pixels")
    for i in range(nobs):
        # Progress bar
        progress_bar(nobs, i + 1)
        # ReadArray for extract
        extract = stack.ReadAsArray(int(xOffset[i]), int(yOffset[i]), 1, 1)
        val[i, :] = extract.reshape(nband,)

    # Close stack
    del stack

    # Replace NA
    # NB: ReadAsArray return float32 type
    bandND = bandND.astype(np.float32)
    for k in range(nband):
        val[val[:, k] == bandND[k], k] = np.nan

    # Add XY coordinates and cell number
    pts_x.shape = (nobs, 1)
    pts_y.shape = (nobs, 1)
    cell.shape = (nobs, 1)
    val = np.concatenate((val, pts_x, pts_y, cell), axis=1)

    # =============================================
    # Export and return value
    # =============================================

    print("Export results to file " + output_file)

    # Write to file by row
    colname = raster_list
    for i in range(len(raster_list)):
        base_name = os.path.basename(raster_list[i])
        index_dot = base_name.index(".")
        colname[i] = base_name[:index_dot]

    varname = ",".join(colname) + ",X,Y,cell"
    np.savetxt(output_file, val, header=varname, fmt="%s",
               delimiter=",", comments="")

    # Convert to pandas DataFrame and return the result
    colname.extend(["X", "Y", "cell"])
    val_DF = pd.DataFrame(val, columns=colname)
    return val_DF

# End
