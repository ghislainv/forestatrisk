#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Import
import os
import sys
import numpy as np
from osgeo import gdal
import matplotlib.pyplot as plt


# Invlogit
def invlogit(x):
    """Compute the inverse-logit of a numpy array.

    We differenciate the positive and negative values to avoid
    under/overflow with the use of exp().

    :param x: numpy array.

    :return: return the inverse-logit of the array.

    """

    r = x
    r[x > 0] = 1. / (1. + np.exp(-x[x > 0]))
    r[x <= 0] = np.exp(x[x <= 0]) / (1 + np.exp(x[x <= 0]))
    return (r)


# Function to make a directory
def make_dir(directory):
    """ Make new directory

    :param directory: path to be created.

    :return: this function does not return any value.

    """

    if not os.path.exists(directory):
        os.mkdir(directory)

    return None


# Makeblock
def makeblock(rasterfile, blk_rows=128):
    """Compute block information.

    This function computes block information from the caracteristics
    of a raster file and an indication on the number of rows to
    consider.

    :param rasterfile: path to a raster file.
    :param blk_rows: if > 0, number of rows for block. If <=0, the
    block size will be 256 x 256.

    :return: a tuple of length 6 including block number, block number
    on x axis, block number on y axis, block offsets on x axis, block
    offsets on y axis, block sizes on x axis, block sizes on y axis.

    """

    r = gdal.Open(rasterfile)
    # b = r.GetRasterBand(1)
    # Landscape variables
    ncol = r.RasterXSize
    nrow = r.RasterYSize
    # Block size
    # block_xsize, block_ysize = b.GetBlockSize()
    # Adapt number of blocks
    if blk_rows > 0:
        block_xsize = ncol
        block_ysize = blk_rows
    else:
        block_xsize = 256
        block_ysize = 256
    # Number of blocks
    nblock_x = np.int(np.ceil(ncol / np.float(block_xsize)))
    nblock_y = np.int(np.ceil(nrow / np.float(block_ysize)))
    nblock = nblock_x * nblock_y
    # Upper-left coordinates of each block
    x = np.arange(0, ncol, block_xsize)
    y = np.arange(0, nrow, block_ysize)
    # Size (number of col and row) of each block
    nx = np.array([block_xsize] * nblock_x)
    ny = np.array([block_ysize] * nblock_y)
    # Modify last values of nx and ny
    if (ncol % block_xsize) > 0:
        nx[-1] = ncol % block_xsize
    if (nrow % block_ysize) > 0:
        ny[-1] = nrow % block_ysize
    # b = None
    del r
    return (nblock, nblock_x, nblock_y, x, y, nx, ny)


# Progress_bar
def progress_bar(niter, i):
    """ Draw progress_bar

    :param niter: total number of iterations.
    :param i: current number of iteration (starts at 1).

    :return: this function does not return any value.

    """

    step = 1 if niter <= 100 else niter / 100
    if i == 1:
        sys.stdout.write("0%")
        sys.stdout.flush()
    elif i % step == 0:
        sys.stdout.write("\r%d%%" % ((100 * i) / niter))
        sys.stdout.flush()
    if (i == niter):
        sys.stdout.write("\r100%\n")
        sys.stdout.flush()
    return None


# Rescale
def rescale(value):
    """Rescale probability values to 1-65534.

    This function rescales probability values (float in [0, 1]) to
    integer values in [1, 65534]. Raster data can then be of type
    UInt16 with 0 as nodata value.

    :param value: float value in [0, 1].

    :return: integer value in [1, 65534].

    """

    return (((value - 1) * 65534 / 999999) + 1)

# End
