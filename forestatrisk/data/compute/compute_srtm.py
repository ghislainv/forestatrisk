"""Computations on SRTM data"""

import os
from glob import glob
from zipfile import ZipFile

from osgeo import gdal


def compute_srtm(proj, extent, verbose=False):
    """Compute elevation and slope.

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

    # Unzip files
    zipfiles = glob("SRTM_*.zip")
    for zipfile in zipfiles:
        outdir = os.path.splitext(zipfile)[0]
        with ZipFile(zipfile) as file:
            file.extractall(outdir)

    # Build vrt file
    tif_srtm_files = glob("SRTM_*/srtm_*.tif")
    gdal.BuildVRT("srtm.vrt", tif_srtm_files, callback=cback)

    # Merge and reproject
    param = gdal.WarpOptions(
        warpOptions=["overwrite"],
        srcSRS="EPSG:4326",
        dstSRS=proj,
        outputBounds=extent,
        targetAlignedPixels=True,
        resampleAlg=gdal.GRA_Bilinear,
        xRes=90,
        yRes=90,
        creationOptions=copts,
        callback=cback,
    )
    gdal.Warp("altitude.tif", "srtm.vrt", options=param)

    # Compute slope
    param = gdal.DEMProcessingOptions(
        creationOptions=copts, computeEdges=True, callback=cback
    )
    gdal.DEMProcessing("_slope.tif", "altitude.tif", processing="slope",
                       options=param)

    # Convert to Int16
    param = gdal.TranslateOptions(
        outputType=gdal.GDT_Int16,
        creationOptions=copts,
        callback=cback
    )
    gdal.Translate("slope.tif", "_slope.tif", options=param)


# End
