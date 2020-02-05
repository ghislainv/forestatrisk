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
# 1. Undisturbed moist tropical forest
# 2. Moist forest within the plantation area
# 3. NEW degradation
# 4. Ongoing degradation (disturbances still detected - can be few years after
#    first degrad if long degrad)
# 5. Degraded forest (former degradation, no disturbances detected anymore)
# 6. NEW deforestation (may follow degradation)
# 7. Ongoing deforestation (disturbances still detected)
# 8. NEW Regrowth
# 9. Regrowthing
# 10. Other land cover (not water)
# 11. Permanent Water (pekel et al. 2015)
# 12. Seasonal Water (pekel et al. 2015)
# 13. Nodata (beginning of the archive) but evergreen forest later
# 14. Nodata (after the initial period) but evergreen forest later
# 15. Nodata but other land cover later
# 16. Nodata within the plantation area (comme val 2 mais nodata)
# 17. Bamboo dominated forest

# Imports
from __future__ import division, print_function  # Python 3 compatibility
import ee
import time
import subprocess


# ee_jrc.run_task
def run_task(iso3, extent_latlong, scale=30, proj=None,
             gdrive_folder=None):
    """Compute forest-cover change with Google EarthEngine.

    Compute the forest-cover change from Global Forest Change data
    with Python and GEE API. Export the results to Google Cloud
    Storage.

    Notes for GOOGLE EARTH ENGINE (abbreviated GEE):
    - GEE account is needed: https://earthengine.google.com.
    - GEE API Python client is needed: \
    https://developers.google.com/earth-engine/python_install.

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
    #path = "users/ghislainv/jrc/"

    # JRC annual product (AP)
    #AP = ee.ImageCollection(path + "AnnualChanges1982_2018")
    AP = ee.ImageCollection(
        "users/ClassifLandsat072015/Roadless36y/AnnualChanges1982_2018")
    AP = AP.mosaic().toByte().clip(region)

    # ap_allYear: forest if Y = 1, 4, 5, 13 or 14.
    AP_forest = AP.where(AP.eq(3).Or(AP.eq(4)).Or(
        AP.eq(5)).Or(AP.eq(13)).Or(AP.eq(14)), 1)
    ap_allYear = AP_forest.where(AP_forest.neq(1), 0)

    # Forest in Jan 2019
    forest2019 = ap_allYear.select(36)

    # Forest cover Jan 2015
    ap_2015_2019 = ap_allYear.select(list(range(32, 37)))
    forest2015 = ap_2015_2019.reduce(ee.Reducer.sum())
    forest2015 = forest2015.gte(1)

    # Forest cover Jan 2010
    ap_2010_2019 = ap_allYear.select(list(range(27, 37)))
    forest2010 = ap_2010_2019.reduce(ee.Reducer.sum())
    forest2010 = forest2010.gte(1)

    # Forest cover Jan 2005
    ap_2005_2019 = ap_allYear.select(list(range(22, 37)))
    forest2005 = ap_2005_2019.reduce(ee.Reducer.sum())
    forest2005 = forest2005.gte(1)

    # Forest cover Jan 2000
    ap_2000_2019 = ap_allYear.select(list(range(17, 37)))
    forest2000 = ap_2000_2019.reduce(ee.Reducer.sum())
    forest2000 = forest2000.gte(1)

    # Forest raster with five bands
    forest = forest2000.addBands(forest2005).addBands(
        forest2010).addBands(forest2015).addBands(forest2019)
    forest = forest.select([0, 1, 2, 3, 4], ["forest2000", "forest2005",
                                             "forest2010", "forest2015",
                                             "forest2019"])
    forest = forest.set("system:bandNames", ["forest2000", "forest2005",
                                             "forest2010", "forest2015",
                                             "forest2019"])

    # maxPixels
    maxPix = 1e13

    # Export forest to Google Drive
    # ! region must be lat/long coordinates with Python API.
    task = ee.batch.Export.image.toDrive(
        image=forest,
        description="forest_" + iso3,
        fileNamePrefix="forest_" + iso3,
        folder=gdrive_folder,
        region=export_coord,
        scale=scale,
        maxPixels=maxPix,
        crs=proj)
    task.start()

    # Return task
    return(task)


# ee_jrc.check
def check(gdrive_remote_rclone, gdrive_folder, iso3):
    """Function to check if the forest cover data are already present in
    the Google Drive folder.

    RClone program is needed: https://rclone.org.

    :param gdrive_remote_rclone: Google Drive remote name in rclone.
    :param gdrive_folder: the Google Drive folder to look in.
    :param iso3: Country ISO 3166-1 alpha-3 code.

    :return: A boolean indicating the presence (True) of the data in
    the folder.

    """

    # RClone command
    cmd = ["rclone", "ls", gdrive_remote_rclone + ":" + gdrive_folder]
    out = subprocess.check_output(cmd).decode("utf-8")
    # Filename to find
    fname = "forest_" + iso3
    # Check file is present
    present_in_folder = False
    if fname in out:
        present_in_folder = True
    # Return
    return(present_in_folder)


# ee_jrc.download
def download(gdrive_remote_rclone, gdrive_folder, iso3, output_path):
    """Download forest-cover data from Google Drive.

    Check that GEE tasks are completed. Download forest-cover data
    from Google Drive in the current working directory.

    RClone program is needed: https://rclone.org.

    :param gdrive_remote_rclone: Google Drive remote name in rclone.
    :param gdrive_folder: the Google Drive folder to look in.
    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param output_path: Path to download files to.

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
    cmd = ["rclone", "copy", "--include", pattern, remote_path, output_path]
    cmd = " ".join(cmd)
    subprocess.call(cmd, shell=True)

# End
