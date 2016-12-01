#!/usr/bin/python

# ============================================================================
#
# cellneigh.py
#
# Compute number of spatial cells and neighbours
#
# Ghislain Vieilledent <ghislain.vieilledent@cirad.fr>
# November 2016
#
# call: cellneigh(region, csize, rank=1)
# raster = path to raster file to compute region
# region = list/tuple of region coordinates (east, west, south, north)
# csize = spatial cell size (in km)
# rank = rank of the neighborhood (1 for chess king's move)
#
# ============================================================================

# =============================================
# Libraries
# =============================================

import numpy as np
import sys
from osgeo import gdal


def cellneigh(raster=None, region=None, csize=10, rank=1):

    # Region
    if raster is not None:
        r = gdal.Open(raster)
        ncol = r.RasterXSize
        nrow = r.RasterYSize
        gt = r.GetGeoTransform()
        Xmin = gt[0]
        Xmax = gt[0]+gt[1]*ncol
        Ymin = gt[3]+gt[5]*nrow
        Ymax = gt[3]
    elif region is not None:
        Xmin = region[0]
        Xmax = region[1]
        Ymin = region[2]
        Ymax = region[3]
    else:
        print("raster or region must be specified")
        sys.exit(1)

    # Cell number from region
    csize = csize
    print("Compute number of %d x %d km spatial cells" % (csize, csize))
    csize = csize * 1000  # Transform km in m
    ncell_byrow = np.int(np.ceil((Xmax - Xmin) / csize))
    ncell_bycol = np.int(np.ceil((Ymax - Ymin) / csize))
    ncell = ncell_byrow * ncell_bycol
    print("... %d cells (%d x %d)" % (ncell, ncell_bycol, ncell_byrow))

    # Adjacent cells and number of neighbors
    print("Identify adjacent cells and compute number of neighbors")
    nneigh = []
    adj = []
    around = np.arange(-rank, rank+1)
    for i in range(ncell_bycol):
        for j in range(ncell_byrow):
            I = i + around
            I = I[(I >= 0) & (I < ncell_bycol)]
            J = j + around
            J = J[(J >= 0) & (J < ncell_byrow)]
            # Disregard the center cell
            nneigh.append(len(I) * len(J) - 1)
            for cy in I:
                for cx in J:
                    if not (cy == i and cx == j):
                        adj.append(cy * ncell_byrow + cx)
    nneigh = np.array(nneigh)
    adj = np.array(adj)

    return(nneigh, adj)

# ============================================================================
# End of cellneigh.py
# ============================================================================
