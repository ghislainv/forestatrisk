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
from miscellaneous import invlogit, rescale, figure_as_image
from miscellaneous import progress_bar, makeblock


# emissions
def emissions(input_stocks="data/AGB.tif",
              input_forest="output/forest_cover_2050.tif",
              coefficient=0.47,
              blk_rows=128):
    """Predict the carbon emissions associated to future deforestation.

    This function predicts the carbon emissions associated to future
    deforestation. Computation are done by block and can be performed
    on large geographical areas.

    :param input_stocks: path to raster of biomass or carbon stocks.
    :param input_forest: path to future forest cover raster (0=deforestation).
    :param coefficient: coefficient to convert stocks in MgC.ha-1.
    :param blk_rows: if > 0, number of rows for computation by block.
    :return: emissions of carbon in MgC.

    """

    # Mask on forest
    fmaskR = gdal.Open(input_forest_raster)
    fmaskB = fmaskR.GetRasterBand(1)

