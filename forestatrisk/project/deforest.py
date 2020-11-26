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


# deforest
def deforest(input_raster,
             hectares,
             output_file="output/fcc.tif",
             blk_rows=128):
    """Function to map the future forest-cover change.

    This function computes the future forest cover map based on (i) a
    raster of probability of deforestation (rescaled from 1 to 65535),
    and (ii) a surface (in hectares) to be deforested.

    :param input_raster: Raster of probability of deforestation (1 to 65535
        with 0 as nodata value).
    :param hectares: Number of hectares to deforest.
    :param output_file: Name of the raster file for forest cover map.
    :param blk_rows: If > 0, number of rows for block (else 256x256).
    :param figsize: Figure size in inches.
    :param dpi: Resolution for output image.

    :return: A tuple of statistics (hectares, frequence,
        threshold, error).

    """

    # Load raster and band
    probR = gdal.Open(input_raster)
    probB = probR.GetRasterBand(1)
    gt = probR.GetGeoTransform()
    proj = probR.GetProjection()
    ncol = probR.RasterXSize
    nrow = probR.RasterYSize

    # Number of pixels to deforest
    surface_pixel = -gt[1] * gt[5]
    ndefor = np.around((hectares * 10000) / surface_pixel).astype(np.int)

    # Make blocks
    blockinfo = makeblock(input_raster, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in {} blocks".format(nblock))

    # Compute the total number of forest pixels
    print("Compute the total number of forest pixels")
    nfp = 0
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Data for one block
        data = probB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        forpix = np.nonzero(data != 0)
        nfp += len(forpix[0])

    # Compute the histogram of values
    nvalues = 65635
    counts = probB.GetHistogram(0.5, 65535.5, nvalues, 0, 0)

    # If deforestation < forest
    if (ndefor < nfp):

        # Identify threshold
        print("Identify threshold")
        quant = ndefor / (nfp * 1.0)
        cS = 0.0
        cumSum = np.zeros(nvalues, dtype=np.float)
        go_on = True
        for i in np.arange(nvalues - 1, -1, -1):
            cS += counts[i] / (nfp * 1.0)
            cumSum[i] = cS
            if (cS >= quant) & (go_on is True):
                go_on = False
                index = i
                threshold = index + 1

        # Minimize error
        print("Minimize error on deforested hectares")
        diff_inf = ndefor - cumSum[index + 1] * nfp
        diff_sup = cumSum[index] * nfp - ndefor
        if diff_sup >= diff_inf:
            index = index + 1
            threshold = index + 1

    # If deforestation > forest (everything is deforested)
    else:
        index = 0
        threshold = 1

    # Raster of predictions
    print("Create a raster file on disk for forest-cover change")
    driver = gdal.GetDriverByName("GTiff")
    fccR = driver.Create(output_file, ncol, nrow, 1,
                         gdal.GDT_Byte,
                         ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"])
    fccR.SetGeoTransform(gt)
    fccR.SetProjection(proj)
    fccB = fccR.GetRasterBand(1)
    fccB.SetNoDataValue(255)

    # Write raster of future fcc
    print("Write raster of future forest-cover change")
    ndc = 0
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Data for one block
        prob_data = probB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Number of pixels that are really deforested
        deforpix = np.nonzero(prob_data >= threshold)
        ndc += len(deforpix[0])
        # Forest-cover change
        for_data = np.ones(shape=prob_data.shape, dtype=np.int8)
        for_data = for_data * 255  # nodata
        for_data[prob_data != 0] = 1
        for_data[deforpix] = 0
        fccB.WriteArray(for_data, x[px], y[py])

    # Compute statistics
    print("Compute statistics")
    fccB.FlushCache()  # Write cache data to disk
    fccB.ComputeStatistics(False)

    # Dereference driver
    fccB = None
    del(fccR)

    # Estimates of error on deforested hectares
    error = (ndc * surface_pixel / 10000.0) - hectares

    # Return results
    stats = (counts, threshold, error, hectares)
    return stats

# End
