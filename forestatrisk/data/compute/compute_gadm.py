"""Processing GADM data."""

import os
import math

from osgeo import gdal

from ..get_vector_extent import get_vector_extent

opj = os.path.join
opd = os.path.dirname
opb = os.path.basename


def compute_gadm(ifile, ofile, proj, buff, verbose=False):
    """Processing GADM data.

    Extract layers to a new GPKG file called "aoi_latlong.gpkg" (if it
    doesn't exist yet) and reproject this file to output file. Layer
    names for country border and subjurisdictions are "aoi" (for "area
    of interest") and "subj" respectively. The extent of the area of
    interest is returned with a buffer of 5 km.

    :param ifile: Path to input GADM or aoi GPKG file.
    :param ofile: Path to aoi GPKG output file.
    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Used for reprojecting data.
    :param buff: Buffer in meter (m) used to extend the extent.
    :param verbose: Logical. Whether to print messages or not. Default
        to ``False``.

    """

    # Lat/lon AOI file
    aoi_latlon_file = opj(opd(ofile), "aoi_latlon.gpkg")

    cb = gdal.TermProgress_nocb if verbose else 0

    # Change layer and file names
    # if using file downloaded from GADM
    if opb(ifile)[:4] == "gadm":
        # Remove intermediate output file
        # if it exists
        if os.path.isfile(aoi_latlon_file):
            os.remove(aoi_latlon_file)
        # Change layer ADM_ADM_0 and file name
        gdal.VectorTranslate(
            aoi_latlon_file, ifile,
            format="GPKG",
            layers="ADM_ADM_0",
            layerName="aoi",
            callback=cb,
        )
        # Change layer ADM_ADM_1
        # NB: Use update access mode to not overwrite the file.
        gdal.VectorTranslate(
            aoi_latlon_file, ifile,
            format="GPKG",
            layers="ADM_ADM_1",
            layerName="subj",
            accessMode="update",
            callback=cb,
        )

    # Reproject AOI
    param = gdal.VectorTranslateOptions(
        accessMode="overwrite",
        srcSRS="EPSG:4326",
        dstSRS=proj,
        reproject=True,
        format="GPKG",
        callback=cb,
    )
    gdal.VectorTranslate(ofile, aoi_latlon_file,
                         options=param)

    # Compute extent
    extent_proj = get_vector_extent(ofile)

    # Region with buffer
    xmin_reg = math.floor(extent_proj[0] - buff)
    ymin_reg = math.floor(extent_proj[1] - buff)
    xmax_reg = math.ceil(extent_proj[2] + buff)
    ymax_reg = math.ceil(extent_proj[3] + buff)
    extent_reg = (xmin_reg, ymin_reg, xmax_reg, ymax_reg)

    return extent_reg

# End
