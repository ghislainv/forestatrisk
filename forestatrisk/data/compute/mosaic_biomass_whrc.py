"""Mosaic WHRC biomass data."""

import os
from glob import glob

from osgeo import gdal

from ...misc import make_dir


def mosaic_biomass_whrc(
    iso3, input_dir="data_raw", output_dir="data", proj="EPSG:3395"
):
    """Function to mosaic biomass images from WHRC.

    This function mosaics the biomass data obtained from GEE. No
    reprojection is performed.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param input_dir: Directory with input files for biomass.

    :param output_dir: Output directory.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    """

    # Create output directory
    make_dir("data")

    # Mosaicing
    files_tif = os.path.join(input_dir, "biomass_whrc_" + iso3 + "*.tif")
    input_list = glob(files_tif)
    output_file = os.path.join(input_dir, "biomass_whrc.vrt")
    gdal.BuildVRT(output_file, input_list)

    # Compressing
    input_file = os.path.join(input_dir, "biomass_whrc.vrt")
    output_file = os.path.join(output_dir, "biomass_whrc.tif")
    param = gdal.TranslateOptions(
        options=["overwrite", "tap"],
        format="GTiff",
        noData=-9999,
        outputSRS=proj,
        creationOptions=[
            "TILED=YES",
            "BLOCKXSIZE=256",
            "BLOCKYSIZE=256",
            "COMPRESS=DEFLATE",
            "PREDICTOR=2",
            "BIGTIFF=YES",
        ],
    )
    gdal.Translate(output_file, input_file, options=param)


# End
