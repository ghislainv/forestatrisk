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


# ee_biomass_whrc.run_task
def run_task(iso3, extent_latlong, scale=30, proj=None,
             gdrive_folder=None):
    """Extract a biomass map using Google Earth Engine.

    Based on country extent, extract a biomass map from the Woods Hole
    Research Center (WHRC) Zarin et al. data (v1 2016) with Python and
    GEE API. Export the results to Google Drive.

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
    region = region.buffer(1000).bounds()
    export_coord = region.getInfo()["coordinates"]

    # WHRC product
    biomass = ee.Image(
        "projects/forestatrisk/assets/biomass/biomass_whrc_v1_2016")
    biomass = biomass.toInt16().clip(region)

    # maxPixels
    maxpix = 1e13

    # Export forest to Google Drive
    # ! region must be lat/long coordinates with Python API.
    # NoData value to -9999
    task = ee.batch.Export.image.toDrive(
        image=biomass.unmask(-9999),
        description="biomass_whrc_" + iso3,
        fileNamePrefix="biomass_whrc_" + iso3,
        folder=gdrive_folder,
        region=export_coord,
        scale=scale,
        maxPixels=maxpix,
        crs=proj)
    task.start()

    # Return task
    return task


# ee_biomass_whrc.check
def check(gdrive_remote_rclone, gdrive_folder, iso3):
    """Function to check if the biomass data is already present in
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
    pattern = "'biomass_whrc_" + iso3 + "*.tif'"
    cmd = ["rclone", "lsf", "--include", pattern, remote_path]
    cmd = " ".join(cmd)
    out = subprocess.check_output(cmd, shell=True).decode("utf-8")
    # Filename to find
    fname = "biomass_whrc_" + iso3
    # Check file is present
    present_in_folder = False
    if fname in out:
        present_in_folder = True
    # Return
    return present_in_folder


# ee_biomass_whrc.download
def download(gdrive_remote_rclone,
             gdrive_folder,
             iso3,
             output_dir="."):
    """Download biomass data from Google Drive.

    Check that GEE task is completed. Wait for the task to be
    completed. Then download biomass data from Google Drive in the
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
    pattern = "'biomass_whrc_" + iso3 + "*.tif'"
    cmd = ["rclone", "copy", "--include", pattern, remote_path, output_dir]
    cmd = " ".join(cmd)
    subprocess.call(cmd, shell=True)

# End
