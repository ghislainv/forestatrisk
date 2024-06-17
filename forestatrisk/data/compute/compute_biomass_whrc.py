"""Process WHRC biomass data."""

import os
from glob import glob
from osgeo import gdal

from ...misc import make_dir


def compute_biomass_whrc(
    iso3, input_dir="data_raw", output_dir="data", proj="EPSG:3395"
):
    """Function to mosaic and resample biomass data from WHRC.

    This function mosaics and resamples the biomass data obtained from
    GEE. A reprojection can be performed.

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
    output_file = os.path.join(input_dir, "biomass_whrc_gee.vrt")
    gdal.BuildVRT(output_file, input_list)

    # Resampling without compression using .vrt file
    # See: https://trac.osgeo.org/gdal/wiki/UserDocs/GdalWarp...
    # ...#GeoTIFFoutput-coCOMPRESSisbroken
    input_file = os.path.join(input_dir, "biomass_whrc_gee.vrt")
    output_file = os.path.join(input_dir, "biomass_whrc_warp.vrt")
    param = gdal.WarpOptions(
        options=["overwrite", "tap"],
        format="VRT",
        xRes=30,
        yRes=30,
        srcNodata=-9999,
        dstNodata=-9999,
        srcSRS="EPSG:4326",
        dstSRS=proj,
        resampleAlg=gdal.GRA_Bilinear,
        outputType=gdal.GDT_Int16,
        multithread=True,
        warpMemoryLimit=500,
        warpOptions=["NUM_THREADS=ALL_CPUS"],
    )
    gdal.Warp(output_file, input_file, options=param)

    # Compressing
    input_file = os.path.join(input_dir, "biomass_whrc_warp.vrt")
    output_file = os.path.join(output_dir, "biomass_whrc.tif")
    param = gdal.TranslateOptions(
        options=["overwrite", "tap"],
        format="GTiff",
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
