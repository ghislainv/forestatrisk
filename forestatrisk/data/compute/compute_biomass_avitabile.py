#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Downloading and processing Avitabile AGB data"""

# =====================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# =====================================================================

from osgeo import gdal


def compute_biomass_avitabile(proj, extent, verbose=False):
    """Compute aboveground biomass.

    Using Avitabile et al. 2016 data.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Used for reprojecting data.

    :param extent: Extent (xmin, ymin, xmax, ymax) of output rasters.

    :param verbose: Logical. Whether to print messages or not. Default
        to ``False``.

    """

    # Callback
    cback = gdal.TermProgress if verbose else 0

    # Creation options
    copts = ["COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"]

    # Resample
    ifile = (
        "/vsicurl/https://forestatrisk.cirad.fr/"
        "tropics/agb/Avitabile_AGB_Map_cog.tif"
    )
    param = gdal.WarpOptions(
        warpOptions=["overwrite"],
        srcSRS="EPSG:4326",
        dstSRS=proj,
        outputBounds=extent,
        targetAlignedPixels=True,
        resampleAlg=gdal.GRA_Bilinear,
        xRes=1000,
        yRes=1000,
        creationOptions=copts,
        callback=cback,
    )
    gdal.Warp("AGB.tif", ifile, options=param)

# End
