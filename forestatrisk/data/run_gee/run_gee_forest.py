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


def run_gee_forest(
    iso3,
    proj="EPSG:3395",
    output_dir="data_raw",
    keep_dir=True,
    fcc_source="jrc",
    perc=50,
    use_xee=False,
    gdrive_remote_rclone=None,
    gdrive_folder=None,
):
    """Compute forest rasters per country with Google Earth Engine (GEE).

    This function uses the iso3 code to download the country borders
    (as a shapefile) from `GADM <https://gadm.org>`_. Download is
    skipped if the shapefile is already present. Country borders are
    used to define the extent for the GEE computation.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param output_dir: Directory where shapefile for country border is saved.
        Additionaly, the forest raster is saved in this directory if "use_xee" is "True".
        Default to "data_raw".

    :param keep_dir: Boolean to keep the output_dir folder. Default
        to "True" (directory "data_raw" is not deleted).

    :param fcc_source: Source for forest-cover change data. Can be
        "gfc" (Global Forest Change) or "tmf" (Tropical Moist Forest)
        data. Abbreviation "jrc" (Joint Research Center) can also be
        used in place of "tmf".

    :param perc: Tree cover percentage threshold to define forest
        (only used if ``fcc_source="gfc"``\\ ).

    :param use_xee: Boolean to use the xarray-EE package or not. If True, then the
        forest raster is directly saved to disk in the "output_dir" directory.
        If False, then the raster is saved to Google Drive, using
        "gdrive_remote_rclone" and "gdrive_folder" parameters. Default to `False`.

    :param gdrive_remote_rclone: Name of the Google Drive remote for
        rclone. Only used if `use_xee` is `False`.

    :param gdrive_folder: Name of the Google Drive folder to use. Only used if
        `use_xee` is `False`.

    """
    # Import GEE function according to "use_xee" parameter
    if use_xee:
        from .xee_gfc import run_task
        from .xee_jrc import run_task
    else:
        from .ee_gfc import run_task, check
        from .ee_jrc import run_task, check

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

    # Google Earth Engine task
    if use_xee:
        # We run using the xee framework
        if not keep_dir:
            print("As 'use_xee' is set to True, the forest raster is directly \
                saved in the output directory. Therefore we force 'keep_dir' to True.\n \
                If this is not the expected behaviour, please delete the output directory manually.")
            keep_dir = True
        # Run xarray-EE
        if fcc_source in ["jrc", "tmf"]:
            print("Run xarray-EE")
            run_task(
                iso3=iso3,
                extent_latlong = extent_latlong,
                proj=proj,
            )
        if fcc_source == "gfc":
            print("Run xarray-EE")
            run_task(
                perc=perc,
                iso3=iso3,
                extent_latlong=extent_latlong,
                proj=proj,
                output_dir=output_dir,
            )
            print("xarray-EE running on the following extent:")
            print(str(extent_latlong))
    else:
        #Not running localy, but on GEE computers
        if fcc_source in ["jrc", "tmf"]:
            # Check data availability
            data_availability = check(gdrive_remote_rclone,
                                             gdrive_folder, iso3)
            # If not available, run GEE
            if data_availability is False:
                print("Run Google Earth Engine")
                task = run_task(
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
            data_availability = check(gdrive_remote_rclone,
                                             gdrive_folder, iso3)
            # If not available, run GEE
            if data_availability is False:
                print("Run Google Earth Engine")
                task = run_task(
                    perc=perc,
                    iso3=iso3,
                    extent_latlong=extent_latlong,
                    scale=30,
                    proj=proj,
                    gdrive_folder=gdrive_folder,
                )
                print("GEE running on the following extent:")
                print(str(extent_latlong))

    # Keep or remove directory
    if not keep_dir:
        if use_xee:
            print("As 'use_xee' is set to True, the forest raster is directly \
                  saved in the output directory. Therefore we force 'keep_dir' to True.")
        else:
            rmtree(output_dir, ignore_errors=True)

# Alias for compatibility with previous versions
country_forest_run = run_gee_forest

# End
