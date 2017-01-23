#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Import
import numpy as np
from osgeo import gdal
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from miscellaneous import figure_as_image
from miscellaneous import progress_bar, makeblock


# deforest
def deforest(input_raster,
             hectares,
             output_file="output/forest_cover.tif",
             blk_rows=128):

    """Function to map the future forest cover.

    This function computes the future forest cover map based on (i) a
    raster of probability of deforestation (rescaled from 1 to 65535),
    and (ii) a surface (in hectares) to be deforested.

    :param input_raster: raster of probability of deforestation (1 to 65535
    with 0 as nodata value).

    :param hectares: number of hectares to deforest.

    :param output_file: name of the raster file for forest cover map.

    :param blk_rows: if > 0, number of rows for block (else 256x256).

    :return: a dictionary with two items, 1) a Matplotlib figure of
    the forest cover, 2) a tuple of statistics (hectares, frequence,
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
    surface_pixel = -gt[1]*gt[5]
    ndefor = np.around((hectares*10000)/surface_pixel).astype(np.int)

    # Make blocks
    blockinfo = makeblock(input_raster, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in " + str(nblock) + " blocks")

    # Compute the total number of forest pixels
    print("Compute the total number of forest pixels")
    nfc = 0
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b+1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b / nblock_x
        # Data for one block
        data = probB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        forpix = np.nonzero(data != 0)
        nfc += len(forpix[0])

    # Compute the histogram of values
    print("Compute the histogram of values")
    nvalues = 65635
    counts = np.zeros(nvalues, dtype=np.float)
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b+1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b / nblock_x
        # Data for one block
        data = probB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        flat_data = data.flatten()
        flat_data_nonzero = flat_data[flat_data != 0]
        for i in flat_data_nonzero:
            counts[i-1] += 1.0/nfc

    # Identify threshold
    print("Identify threshold")
    quant = ndefor/np.float(nfc)
    cS = 0.0
    cumSum = np.zeros(nvalues, dtype=np.float)
    go_on = True
    for i in np.arange(nvalues-1, -1, -1):
        cS += counts[i]
        cumSum[i] = cS
        if (cS >= quant) & (go_on is True):
            go_on = False
            index = i
            threshold = index+1

    # Minimize error
    print("Minimize error on deforested hectares")
    diff_inf = ndefor-cumSum[index+1]*nfc
    diff_sup = cumSum[index]*nfc-ndefor
    if diff_sup >= diff_inf:
        index = index+1
        threshold = index+1

    # Raster of predictions
    print("Create a raster file on disk for forest cover")
    driver = gdal.GetDriverByName("GTiff")
    forestR = driver.Create(output_file, ncol, nrow, 1,
                            gdal.GDT_Byte,
                            ["COMPRESS=LZW", "PREDICTOR=2"])
    forestR.SetGeoTransform(gt)
    forestR.SetProjection(proj)
    forestB = forestR.GetRasterBand(1)
    forestB.SetNoDataValue(255)

    # Write raster of forest cover
    print("Write raster of forest cover")
    ndc = 0
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b+1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b / nblock_x
        # Data for one block
        prob_data = probB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Number of pixels that are really deforested
        deforpix = np.nonzero(prob_data >= threshold)
        ndc += len(deforpix[0])
        # Forest cover
        for_data = np.ones(shape=prob_data.shape, dtype=np.int8)
        for_data = for_data*255  # nodata
        for_data[prob_data != 0] = 1
        for_data[deforpix] = 0
        forestB.WriteArray(for_data, x[px], y[py])

    # Estimates of error on deforested hectares
    error = (ndc*surface_pixel/10000)-hectares

    # Compute statistics
    print("Compute statistics")
    forestB.FlushCache()  # Write cache data to disk
    forestB.ComputeStatistics(False)

    # Build overviews
    print("Build overview")
    forestR.BuildOverviews("nearest", [8, 16, 32])

    # Get data from finest overview
    ov_band = forestB.GetOverview(0)
    ov_arr = ov_band.ReadAsArray()
    ov_arr[ov_arr == 255] = 2

    # Dereference driver
    forestB = None
    del(forestR)

    # Colormap
    colors = []
    cmax = 255.0  # float for division
    colors.append((1, 0, 0, 1))  # red
    colors.append((34/cmax, 139/cmax, 34/cmax, 1))  # forest green
    colors.append((0, 0, 0, 0))  # transparent
    color_map = ListedColormap(colors)

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

    # Return results
    return {"figure": fig_img, "statistics": (counts, threshold,
                                              error, hectares)}

# End
