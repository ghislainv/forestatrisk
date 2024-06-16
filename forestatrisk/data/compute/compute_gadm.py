"""Processing GADM data."""

import os
import math

from osgeo import gdal

from ..get_vector_extent import get_vector_extent

opj = os.path.join
opd = os.path.dirname


def compute_gadm(ifile, ofile, proj, verbose=False):
    """Processing GADM data.

    Extract layers to a new GPKG file called "aoi_latlong.gpkg" (if it
    doesn't exist yet) and reproject this file to output file. Layer
    names for country border and subjurisdictions are "aoi" (for "area
    of interest") and "subj" respectively. The extent of the area of
    interest is returned with a buffer of 5 km.

    :param input_file: Path to input GADM GPKG file.
    :param output_file: Path to aoi GPKG output file.
    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Used for reprojecting data.
    :param verbose: Logical. Whether to print messages or not. Default
        to ``False``.

    """

    aoi_latlon_file = opj(opd(ofile), "aoi_latlon.gpkg")

    cb = gdal.TermProgress if verbose else 0

    # Change layer and file names
    if not os.path.isfile(aoi_latlon_file):
        # Change layer ADM_ADM_0 and file name
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

    # Region with buffer of 5km
    xmin_reg = math.floor(extent_proj[0] - 5000)
    ymin_reg = math.floor(extent_proj[1] - 5000)
    xmax_reg = math.ceil(extent_proj[2] + 5000)
    ymax_reg = math.ceil(extent_proj[3] + 5000)
    extent_reg = (xmin_reg, ymin_reg, xmax_reg, ymax_reg)

    return extent_reg

# End
