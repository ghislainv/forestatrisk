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
from matplotlib.colors import LinearSegmentedColormap
from miscellaneous import figure_as_image
from miscellaneous import progress_bar, makeblock


# deforest
def deforest(input_raster, hectares,
             output_file="output/forest_cover.tif",
             blk_rows=0):
    """Function to map the future forest cover.

    This function computes the future forest cover map based on (i) a
    raster of probability of deforestation (rescaled from 1 to 65535),
    and (ii) a surface (in hectares) to be deforested.

    :param input_raster: raster of probability of deforestation (1 to 65535).
    :param hectares: number of hectares to deforest.
    :param output_file: name of the raster file for forest cover map.
    :param blk_rows: if > 0, number of rows for block (else 256x256).
    :return: a Matplotlib figure of the forest cover.

    """

    # Load raster and band
    probR = gdal.Open(input_raster)
    probB = probR.GetRasterBand(1)
    probND = probB.GetNoDataValue()
    gt = probR.GetGeoTransform()
    proj = probR.GetProjection()
    ncol = probR.RasterXSize
    nrow = probR.RasterYSize
    Xmin = gt[0]
    Xmax = gt[0] + gt[1] * ncol
    Ymin = gt[3] + gt[5] * nrow
    Ymax = gt[3]

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

    # Object to store histogram values
    nvalues = 65635
    counts = np.ones(shape=(nvalues, 2))
    counts[:, 0] = np.array(range(nvalues)) + 1

    # Make blocks
    blockinfo = makeblock(input_raster, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    print("Divide region in " + str(nblock) + " blocks")

    # Computation by block
    # Message
    print("Compute the histogram of values")
    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        progress_bar(nblock, b+1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b / nblock_x
        # Number of pixels
        npix = nx[px] * ny[py]
        # Data for one block of the stack (shape = (nband,nrow,ncol))
        data = probB.ReadAsArray(x[px], y[py], nx[px], ny[py])
        for i in range(nvalues):
            count[i, 1] = sum(data == (i+1))
        # Assign prediction to raster
        Pband.WriteArray(forestB, x[px], y[py])

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
    cmax = 255.0  # float for division
    vmax = 65535.0  # float for division
    colors.append((0, (0, 0, 0, 0)))  # transparent
    colors.append((1/vmax, (34/cmax, 139/cmax, 34/cmax, 1)))  # green
    colors.append((45000/vmax, (1, 165/cmax, 0, 1)))  # red
    colors.append((55000/vmax, (1, 0, 0, 1)))  # orange
    colors.append((1, (0, 0, 0, 1)))  # black
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
