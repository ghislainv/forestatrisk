#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Computations on WDPA data"""

# =====================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# =====================================================================

from osgeo import gdal


def compute_wdpa(iso, proj, extent, where=None, verbose=False):
    """Compute presence of protected areas.

    :param iso: Country iso code.

    :param where: SQL statement to filter features. Default to
        ``"status=\"Designated\" OR status=\"Inscribed\" OR
        status=\"Established\" OR (status=\"Proposed\" AND
        CAST(SUBSTR(date,7,4) AS INTEGER) < 2010)"``

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Used for reprojecting data.

    :param extent: Extent (xmin, ymin, xmax, ymax) of output rasters.

    :param verbose: Logical. Whether to print messages or not. Default
        to ``False``.

    """

    # Callback
    cb = gdal.TermProgress if verbose else 0

    # Defaut value for where
    if where is None:
        where_statement = (
            'status="Designated" OR '
            'status="Inscribed" OR '
            'status="Established" OR '
            '(status="Proposed" AND '
            "CAST(SUBSTR(date,7,4) AS INTEGER) < 2010)"
        )
    else:
        where_statement = where

    # Reproject and filter
    param = gdal.VectorTranslateOptions(
        accessMode="overwrite",
        skipFailures=True,
        format="ESRI Shapefile",
        where=where_statement,
        srcSRS="EPSG:4326",
        dstSRS=proj,
        layerCreationOptions=["ENCODING=UTF-8"],
        callback=cb,
    )
    gdal.VectorTranslate("pa_PROJ.shp", "pa_" + iso + ".shp", options=param)

    # Rasterize
    gdal.RasterizeOptions(
        outputBounds=extent,
        targetAlignedPixels=True,
        burnValues=[1],
        outputSRS=proj,
        initValues=[0],
        noData=255,
        xRes=30,
        yRes=30,
        layers=["pa_PROJ"],
        outputType=gdal.GDT_Byte,
        creationOptions=["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"],
        callback=cb,
    )
    gdal.Rasterize("pa.tif", "pa_PROJ.shp", options=param)


# End
