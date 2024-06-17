"""Processing WDPA data."""

from osgeo import gdal


def compute_wdpa(iso, proj, extent, where=None, verbose=False):
    """Process geospatial data on protected areas.

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
    cback = gdal.TermProgress if verbose else 0

    # Defaut value for where
    if where is None:
        where_statement = (
            "status='Designated' OR "
            "status='Inscribed' OR "
            "status='Established' OR "
            "(status='Proposed' AND "
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
        callback=cback
    )
    gdal.VectorTranslate("pa_proj.shp", "pa_" + iso + ".shp", options=param)

    # Rasterize
    param = gdal.RasterizeOptions(
        outputBounds=extent,
        targetAlignedPixels=True,
        burnValues=[1],
        outputSRS=proj,
        initValues=[0],
        noData=255,
        xRes=30,
        yRes=30,
        layers=["pa_proj"],
        outputType=gdal.GDT_Byte,
        creationOptions=["COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"],
        callback=cback
    )
    gdal.Rasterize("pa.tif", "pa_proj.shp", options=param)


# End
