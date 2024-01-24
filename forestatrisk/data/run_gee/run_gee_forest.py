"""Run GEE forest."""

import os
from shutil import rmtree
from zipfile import ZipFile  # To unzip files

try:
    from urllib.request import urlretrieve  # Python 3
except ImportError:
    from urllib import urlretrieve  # urlretrieve with Python 2

from ...misc import make_dir
from ..extent_shp import extent_shp

from . import ee_gfc, ee_jrc


def run_gee_forest(
    iso3,
    proj="EPSG:3395",
    output_dir="data_raw",
    keep_dir=True,
    fcc_source="jrc",
    perc=50,
    gdrive_remote_rclone=None,
    gdrive_folder=None,
):
    """Compute forest rasters per country and export them to Google Drive
    with Google Earth Engine (GEE).

    This function uses the iso3 code to download the country borders
    (as a shapefile) from `GADM <https://gadm.org>`_. Download is
    skipped if the shapefile is already present. Country borders are
    used to define the extent for the GEE computation.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param output_dir: Directory where shapefile for country border is saved.

    :param keep_dir: Boolean to keep the output_dir folder. Default
        to "True" (directory "data_raw" is not deleted).

    :param fcc_source: Source for forest-cover change data. Can be
        "gfc" (Global Forest Change) or "tmf" (Tropical Moist Forest)
        data. Abbreviation "jrc" (Joint Research Center) can also be
        used in place of "tmf".

    :param perc: Tree cover percentage threshold to define forest
        (only used if ``fcc_source="gfc"``\\ ).

    :param gdrive_remote_rclone: Name of the Google Drive remote for
        rclone.

    :param gdrive_folder: Name of the Google Drive folder to use.

    """

    # Create directory
    make_dir(output_dir)

    # Check for existing data
    shp_name = os.path.join(output_dir, "gadm36_" + iso3 + "_0.shp")
    if os.path.isfile(shp_name) is not True:

        # Download the zipfile from gadm.org
        fname = os.path.join(output_dir, iso3 + "_shp.zip")
        url = (
            "https://biogeo.ucdavis.edu/data/gadm3.6/"
            "shp/gadm36_" + iso3 + "_shp.zip"
        )
        urlretrieve(url, fname)

        # Extract files from zip
        with ZipFile(fname) as file:
            file.extractall(output_dir)

    # Compute extent
    extent_latlong = extent_shp(shp_name)

    # Keep or remove directory
    if not keep_dir:
        rmtree(output_dir, ignore_errors=True)

    # Google Earth Engine task
    if fcc_source in ["jrc", "tmf"]:
        # Check data availability
        data_availability = ee_jrc.check(gdrive_remote_rclone,
                                         gdrive_folder, iso3)
        # If not available, run GEE
        if data_availability is False:
            print("Run Google Earth Engine")
            task = ee_jrc.run_task(
                iso3=iso3,
                extent_latlong=extent_latlong,
                scale=30,
                proj=proj,
                gdrive_folder=gdrive_folder,
            )
            print("GEE running on the following extent:")
            print(str(extent_latlong))
    if fcc_source == "gfc":
        # Check data availability
        data_availability = ee_gfc.check(gdrive_remote_rclone,
                                         gdrive_folder, iso3)
        # If not available, run GEE
        if data_availability is False:
            print("Run Google Earth Engine")
            task = ee_gfc.run_task(
                perc=perc,
                iso3=iso3,
                extent_latlong=extent_latlong,
                scale=30,
                proj=proj,
                gdrive_folder=gdrive_folder,
            )
            print("GEE running on the following extent:")
            print(str(extent_latlong))


# Alias for compatibility with previous versions
country_forest_run = run_gee_forest

# End
