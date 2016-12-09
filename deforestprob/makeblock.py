#!/usr/bin/python

# =============================================================================
#
# makeblock.py
#
# Python function to read raster data in block
#
# Ghislain Vieilledent <ghislain.vieilledent@cirad.fr>
# November 2016
#
# call: makeblock(rasterfile, byrows=False, nrows=128)
#
# ============================================================================

# Libraries
from osgeo import gdal  # GIS libraries
import numpy as np  # For arrays


def makeblock(rasterfile, blk_rows=128):
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
