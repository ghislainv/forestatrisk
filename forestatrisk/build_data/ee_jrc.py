#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Annual product legend
# 1. Tropical moist forest (TMF including bamboo-dominated forest and mangroves)
# 2. TMF converted later in a tree plantation
# 3. NEW degradation
# 4. Ongoing degradation (disturbances still detected - can be few years after first degrad if several degradation stages)
# 5. Degraded forest (former degradation, no disturbances detected anymore)
# 6. NEW deforestation (may follow degradation)
# 7. Ongoing deforestation (disturbances still detected)
# 8. NEW Regrowth
# 9. Regrowthing
# 10. Other land cover (not water)
# 11. Permanent Water (pekel et al.2015)
# 12. Seasonal Water (pekel et al.2015)
# 13. Init period without valid data - Init class = TMF
# 14. Init period with min 1 valid obs - Init class = TMF
# 15. Nodata  - Init class = other LC
# 16. Init period without valid data - Init class = Plantation

# Standard library imports
from __future__ import division, print_function  # Python 3 compatibility
import subprocess
import time

# Third party imports
import ee


# ee_jrc.run_task
def run_task(iso3, extent_latlong, scale=30, proj=None,
             gdrive_folder=None):
    """Compute forest-cover change with Google Earth Engine.

    Compute the forest-cover change from Joint Research Center (JRC)
    Vancutsem et al. data with Python and GEE API. Export the results
    to Google Drive.

    Notes for Google Earth Engine (abbreviated GEE):

    * GEE account is needed: `<https://earthengine.google.com>`_\\ .
    * GEE API Python client is needed: \
    `<https://developers.google.com/earth-engine/python_install>`_\\ .

    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param extent_latlong: List/tuple of region extent in lat/long
        (xmin, ymin, xmax, ymax).
    :param scale: Resolution in meters per pixel. Default to 30.
    :param proj: The projection for the export.
    :param gdrive_folder: Name of the Google Drive folder to export to.

    :return: Google Earth Engine task.

    """

    # Region
    region = ee.Geometry.Rectangle(extent_latlong, proj="EPSG:4326",
                                   geodesic=False)
    region = region.buffer(10000).bounds()
    export_coord = region.getInfo()["coordinates"]

    # Path to JRC products
    # path = "users/ghislainv/jrc/"

    # JRC annual product (AP)
    # AP = ee.ImageCollection(path + "AnnualChanges1982_2019")
    AP = ee.ImageCollection(
        "users/ClassifLandsat072015/Roadless2019/AnnualChanges_1982_2019")
    AP = AP.mosaic().toByte()
    AP = AP.clip(region)

    # ap_allYear: forest if Y = 1, 2, 3, 4, 5, 13, or 14.
    AP_forest = AP.where(AP.eq(2).Or(AP.eq(3)).Or(AP.eq(4)).Or(
        AP.eq(5)).Or(AP.eq(13)).Or(AP.eq(14)), 1)
    ap_allYear = AP_forest.where(AP_forest.neq(1), 0)

    # Forest in Jan 2020
    forest2020 = ap_allYear.select(37)

    # Forest cover Jan 2015
    ap_2015_2020 = ap_allYear.select(list(range(32, 38)))
    forest2015 = ap_2015_2020.reduce(ee.Reducer.sum())
    forest2015 = forest2015.gte(1)

    # Forest cover Jan 2010
    ap_2010_2020 = ap_allYear.select(list(range(27, 38)))
    forest2010 = ap_2010_2020.reduce(ee.Reducer.sum())
    forest2010 = forest2010.gte(1)

    # Forest cover Jan 2005
    ap_2005_2020 = ap_allYear.select(list(range(22, 38)))
    forest2005 = ap_2005_2020.reduce(ee.Reducer.sum())
    forest2005 = forest2005.gte(1)

    # Forest cover Jan 2000
    ap_2000_2020 = ap_allYear.select(list(range(17, 38)))
    forest2000 = ap_2000_2020.reduce(ee.Reducer.sum())
    forest2000 = forest2000.gte(1)

    # Forest raster with five bands
    forest = forest2000.addBands(forest2005).addBands(
        forest2010).addBands(forest2015).addBands(forest2020)
    forest = forest.select([0, 1, 2, 3, 4], ["forest2000", "forest2005",
                                             "forest2010", "forest2015",
                                             "forest2020"])
    forest = forest.set("system:bandNames", ["forest2000", "forest2005",
                                             "forest2010", "forest2015",
                                             "forest2020"])

    # maxPixels
    maxpix = 1e13

    # Export forest to Google Drive
    # ! region must be lat/long coordinates with Python API.
    task = ee.batch.Export.image.toDrive(
        image=forest,
        description="forest_" + iso3,
        fileNamePrefix="forest_" + iso3,
        folder=gdrive_folder,
        region=export_coord,
        scale=scale,
        maxPixels=maxpix,
        crs=proj)
    task.start()

    # Return task
    return task


# ee_jrc.check
def check(gdrive_remote_rclone, gdrive_folder, iso3):
    """Function to check if the forest cover data are already present in
    the Google Drive folder.

    RClone program is needed: `<https://rclone.org>`_\\ .

    :param gdrive_remote_rclone: Google Drive remote name in rclone.
    :param gdrive_folder: the Google Drive folder to look in.
    :param iso3: Country ISO 3166-1 alpha-3 code.

    :return: A boolean indicating the presence (True) of the data in
        the folder.

    """

    # RClone command
    remote_path = gdrive_remote_rclone + ":" + gdrive_folder
    pattern = "'forest_" + iso3 + "*.tif'"
    cmd = ["rclone", "lsf", "--include", pattern, remote_path]
    cmd = " ".join(cmd)
    out = subprocess.check_output(cmd, shell=True).decode("utf-8")
    # Filename to find
    fname = "forest_" + iso3
    # Check file is present
    present_in_folder = False
    if fname in out:
        present_in_folder = True
    # Return
    return present_in_folder


# ee_jrc.download
def download(gdrive_remote_rclone,
             gdrive_folder,
             iso3,
             output_dir="."):
    """Download forest-cover data from Google Drive.

    Check that GEE task is completed. Wait for the task to be
    completed. Then download forest-cover data from Google Drive in the
    current working directory.

    RClone program is needed: `<https://rclone.org>`_\\ .

    :param gdrive_remote_rclone: Google Drive remote name in rclone.

    :param gdrive_folder: the Google Drive folder to look in.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_dir: Output directory to download files to. Default
        to current working directory.

    """

    # Data availability
    data_availability = check(gdrive_remote_rclone,
                              gdrive_folder,
                              iso3)

    # Check task status
    while data_availability is False:
        # We wait 1 min
        time.sleep(60)
        # We reactualize the status
        data_availability = check(gdrive_remote_rclone,
                                  gdrive_folder,
                                  iso3)

    # Commands to download results with rclone
    remote_path = gdrive_remote_rclone + ":" + gdrive_folder
    pattern = "'forest_" + iso3 + "*.tif'"
    cmd = ["rclone", "copy", "--include", pattern, remote_path, output_dir]
    cmd = " ".join(cmd)
    subprocess.call(cmd, shell=True)

# End
