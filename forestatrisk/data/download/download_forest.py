"""Download forest cover data."""

import os
from glob import glob

from ..run_gee import ee_jrc


def download_forest(iso3, gdrive_remote_rclone,
                    gdrive_folder, output_dir="."):
    """Download forest cover data from Google Drive.

    .. deprecated:: 1.1.4
       Use function ``get_fcc`` in the ``geefcc`` package.

    .. warning::
       Will be removed in future versions.

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

    # If no data locally try to download the data
    if len(raster_list) == 0:
        ee_jrc.download(
            gdrive_remote_rclone, gdrive_folder,
            iso3, output_dir
        )


# End
