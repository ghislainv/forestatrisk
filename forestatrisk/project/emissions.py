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

# Third party imports
import numpy as np
from osgeo import gdal

# Local application imports
from ..misc import progress_bar, makeblock


# emissions
def emissions(input_stocks="data/emissions/AGB.tif",
              input_forest="output/forest_cover_2050.tif",
              coefficient=0.47,
              blk_rows=128):
    """Predict the carbon emissions associated to future deforestation.

    This function predicts the carbon emissions associated to future
    deforestation. Computation are done by block and can be performed
    on large geographical areas.

    :param input_stocks: Path to raster of biomass or carbon stocks (in Mg/ha).
    :param input_forest: Path to forest-cover change raster (0=deforestation).
    :param coefficient: Coefficient to convert stocks in MgC/ha (can be 1).
    :param blk_rows: If > 0, number of rows for computation by block.
    :return: Emissions of carbon in MgC.

    """

    # Landscape variables from forest raster
    forestR = gdal.Open(input_forest)
    gt = forestR.GetGeoTransform()
    ncol = forestR.RasterXSize
    nrow = forestR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]

    # Make vrt
    print("Make virtual raster")
    raster_list = [input_forest, input_stocks]
    param = gdal.BuildVRTOptions(resolution="user",
                                 outputBounds=(Xmin, Ymin, Xmax, Ymax),
                                 xRes=gt[1], yRes=-gt[5],
                                 separate=True)
    gdal.BuildVRT("/vsimem/var.vrt", raster_list, options=param)
    stack = gdal.Open("/vsimem/var.vrt")

    # NoData value for stocks
    # stocksB = stack.GetRasterBand(2)
    # stocksND = stocksB.GetNoDataValue()

    # Make blocks
    blockinfo = makeblock("/vsimem/var.vrt", blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Computation by block
    # Total sum
    sum_Stocks = 0
    # Message
    print("Compute carbon emissions by block")
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Data for one block of the stack (shape = (nband,nrow,ncol))
        data = stack.ReadAsArray(x[px], y[py], nx[px], ny[py])
        data_Stocks = data[1]
        # data_Stocks[data_Stocks == StocksND] = 0
        # Previous line doesn't work because StocksND
        # differs from NoData value in ReadAsArray
        data_Stocks[data_Stocks < 0] = 0
        data_Forest = data[0]
        # Sum of emitted stocks
        sum_Stocks = sum_Stocks + np.sum(data_Stocks[data_Forest == 0])
    # Pixel area (in ha)
    Area = gt[1] * (-gt[5]) / 10000
    # Carbon emissions in Mg
    Carbon = sum_Stocks * coefficient * Area
    Carbon = np.int(np.rint(Carbon))

    # Return carbon emissions
    return(Carbon)

# End
