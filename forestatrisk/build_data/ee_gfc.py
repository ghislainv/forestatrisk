#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Standard library imports
from __future__ import division, print_function  # Python 3 compatibility
import subprocess
import time

# Third party imports
import ee


# ee_gfc.run_task
def run_task(perc, iso3, extent_latlong, scale=30, proj=None,
             gdrive_folder=None):
    """Compute forest-cover change with Google EarthEngine.

    Compute the forest-cover change from Global Forest Change (GFC)
    Hansen et al. data with Python and GEE API. Export the results to
    Google Drive.

    Notes for Google Earth Engine (abbreviated GEE):

    * GEE account is needed: `<https://earthengine.google.com>`_\\ .
    * GEE API Python client is needed: \
    `<https://developers.google.com/earth-engine/python_install>`_\\ .

    :param perc: Tree cover percentage threshold to define forest.
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

    # Hansen map
    gfc = ee.Image("UMD/hansen/global_forest_change_2019_v1_7").clip(region)

    # Tree cover, loss, and gain
    treecover = gfc.select(["treecover2000"])
    lossyear = gfc.select(["lossyear"])

    # Forest in 2000
    forest2000 = treecover.gte(perc)
    forest2000 = forest2000.toByte()

    # Deforestation
    loss01_04 = lossyear.gte(1).And(lossyear.lte(4))
    loss01_09 = lossyear.gte(1).And(lossyear.lte(9))
    loss01_14 = lossyear.gte(1).And(lossyear.lte(14))

    # Forest
    forest2005 = forest2000.where(loss01_04.eq(1), 0)
    forest2010 = forest2000.where(loss01_09.eq(1), 0)
    forest2015 = forest2000.where(loss01_14.eq(1), 0)
    forest2020 = forest2000.where(lossyear.gte(1), 0)

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


# ee_gfc.check
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
    return(present_in_folder)


# ee_gfc.download
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
