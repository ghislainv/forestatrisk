"""Download forest cover data."""

import os
from glob import glob
import subprocess

from ..run_gee import ee_jrc


def download_forest(iso3, gdrive_remote_rclone,
                    gdrive_folder, output_dir="."):
    """Download forest cover data from Google Drive.

    Download forest cover data from Google Drive in the current
    working directory. Print a message if the file is not available.

    RClone program is needed: `<https://rclone.org>`_\\ .

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param gdrive_remote_rclone: Google Drive remote name in rclone.

    :param gdrive_folder: the Google Drive folder to download from.

    :param output_dir: Output directory to download files to. Default
        to current working directory.

    """

    # Check for existing data locally
    files_tif = os.path.join(output_dir, "forest_" + iso3 + "*.tif")
    raster_list = glob(files_tif)

    # If no data locally check if available in gdrive
    if len(raster_list) == 0:
        # Data availability in gdrive
        data_availability = ee_jrc.check(gdrive_remote_rclone,
                                         gdrive_folder, iso3)

        # Donwload if available in gdrive
        if data_availability is True:
            # Commands to download results with rclone
            remote_path = gdrive_remote_rclone + ":" + gdrive_folder
            pattern = "'forest_" + iso3 + "*.tif'"
            cmd = ["rclone", "copy", "--include", pattern,
                   remote_path, output_dir]
            cmd = " ".join(cmd)
            subprocess.call(cmd, shell=True)
            print("Data for {0:3s} have been downloaded".format(iso3))

        else:
            print("Data for {0:3s} are not available".format(iso3))


# End
