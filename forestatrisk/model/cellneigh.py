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
import sys

# Third party imports
import numpy as np
from osgeo import gdal


# cellneigh
def cellneigh(raster=None, region=None, csize=10, rank=1):
    """Compute number of spatial cells and neighbours.

    :param raster: Path to raster file to compute region.
    :param region: List/tuple of region coordinates (east, west, south, north).
    :param csize: Spatial cell size (in km).
    :param rank: Rank of the neighborhood (1 for chess king's move).

    :return: Tuple of length 2 with number of neighbours for each cell
        and adjacent cells.

    """

    # Region
    if raster is not None:
        r = gdal.Open(raster)
        ncol_r = r.RasterXSize
        nrow_r = r.RasterYSize
        gt = r.GetGeoTransform()
        Xmin = gt[0]
        Xmax = gt[0] + gt[1] * ncol_r
        Ymin = gt[3] + gt[5] * nrow_r
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
    print("Compute number of {} x {} km spatial cells".format(csize, csize))
    csize = csize * 1000  # Transform km in m
    ncol = np.int(np.ceil((Xmax - Xmin) / csize))
    nrow = np.int(np.ceil((Ymax - Ymin) / csize))
    ncell = ncol * nrow
    print("... {} cells ({} x {})".format(ncell, nrow, ncol))

    # Adjacent cells and number of neighbors
    print("Identify adjacent cells and compute number of neighbors")
    nneigh = []
    adj = []
    around = np.arange(-rank, rank + 1)
    for i in range(nrow):
        for j in range(ncol):
            bigI = i + around
            Iprim = bigI[(bigI >= 0) & (bigI < nrow)]
            bigJ = j + around
            Jprim = bigJ[(bigJ >= 0) & (bigJ < ncol)]
            # Disregard the center cell
            nneigh.append(len(Iprim) * len(Jprim) - 1)
            for cy in Iprim:
                for cx in Jprim:
                    if not (cy == i and cx == j):
                        adj.append(cy * ncol + cx)
    nneigh = np.array(nneigh)
    adj = np.array(adj)

    return (nneigh, adj)


# cellneigh_ctry
def cellneigh_ctry(raster=None, region=None, vector=None,
                   csize=10, rank=1):
    """Compute number of spatial cells and neighbours inside country's
    borders.

    :param raster: Path to raster file to compute region from.
    :param region: List/tuple of region coordinates (east, west,
        south, north) if raster is not provided.
    :param vector: Path to vector file with country's borders.
    :param csize: Spatial cell size (in km).
    :param rank: Rank of the neighborhood (1 for chess king's move).

    :return: Tuple of length 4 with (i) number of neighbours for each
        cell, (ii) adjacent cells, (iii) total number of cells inside
        country's border, (iv) total number of cells from region.

    """

    # Region
    if raster is not None:
        r = gdal.Open(raster)
        ncol_r = r.RasterXSize
        nrow_r = r.RasterYSize
        gt = r.GetGeoTransform()
        Xmin = gt[0]
        Xmax = gt[0] + gt[1] * ncol_r
        Ymin = gt[3] + gt[5] * nrow_r
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
    print("Compute number of {} x {} km spatial cells".format(csize, csize))
    csize = csize * 1000  # Transform km in m
    ncol = np.int(np.ceil((Xmax - Xmin) / csize))
    nrow = np.int(np.ceil((Ymax - Ymin) / csize))
    Xmax_new = Xmin + ncol * csize
    Ymin_new = Ymax + nrow * (-csize)
    ncell = ncol * nrow
    print("... {} cells ({} x {})".format(ncell, nrow, ncol))

    # Cells within country borders (rasterizing method)
    cb_ds = gdal.OpenEx(vector, gdal.OF_VECTOR)
    rOptions = gdal.RasterizeOptions(xRes=csize, yRes=-csize,
                                     allTouched=True,
                                     outputBounds=[Xmin, Ymin_new,
                                                   Xmax_new, Ymax],
                                     burnValues=1, noData=0)
    outfile = "/vsimem/tmpfile"
    ds = gdal.Rasterize(outfile, cb_ds, options=rOptions)
    mask = ds.ReadAsArray()
    ds = None
    gdal.Unlink(outfile)
    y_in, x_in = np.where(mask == 1)
    cell_in = y_in * ncol + x_in

    # Adjacent cells and number of neighbors
    print("Identify adjacent cells and compute number of neighbors")
    nneigh = []
    adj = []
    adj_sort = []
    around = np.arange(-rank, rank + 1)
    for i in range(nrow):
        for j in range(ncol):
            if mask[i, j] == 1:
                bigI = i + around
                Iprim = bigI[(bigI >= 0) & (bigI < nrow)]
                bigJ = j + around
                Jprim = bigJ[(bigJ >= 0) & (bigJ < ncol)]
                # Loop on potential neighbors
                nneighbors = 0
                for cy in Iprim:
                    for cx in Jprim:
                        if (not (cy == i and cx == j)) and (mask[cy, cx] == 1):
                            adj.append(cy * ncol + cx)
                            nneighbors += 1
                nneigh.append(nneighbors)
    nneigh = np.array(nneigh)
    adj = np.array(adj)
    for i in adj:
        adj_sort.append(np.flatnonzero(cell_in == i)[0])
    adj_sort = np.array(adj_sort)
    return (nneigh, adj_sort, cell_in, ncell)

# End
