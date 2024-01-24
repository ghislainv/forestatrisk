"""Download country geospatial data."""

# Local application imports
from ..misc import make_dir
from .download import download_forest, download_osm
from .download import download_srtm, download_wdpa, download_gadm


def country_download(
        iso3,
        gdrive_remote_rclone,
        gdrive_folder,
        output_dir=".",
        gadm=True,
        srtm=True,
        wdpa=True,
        osm=True,
        forest=True):
    """Download country geospatial data.

    Function to download all the data for a specific country. It
    includes GEE forest data, GADM, OSM, SRTM, and WDPA data.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param gdrive_remote_rclone: Google Drive remote name in rclone.

    :param gdrive_folder: the Google Drive folder to download from.

    :param output_dir: Directory where data is downloaded. Default to
        current working directory.

    :param gadm: Toggle GADM data download.

    :param srtm: Toggle SRTM data download.

    :param wdpa: Toggle SRTM data download.

    :param osm: Toggle OSM data download.

    :param forest: Toggle forest data download.

    """

    # Message
    print("Downloading data for country " + iso3)

    # Create directory
    make_dir(output_dir)

    # Download
    if gadm:
        download_gadm(iso3=iso3, output_dir=output_dir)
    if srtm:
        download_srtm(iso3=iso3, output_dir=output_dir)
    if wdpa:
        download_wdpa(iso3=iso3, output_dir=output_dir)
    if osm:
        download_osm(iso3=iso3, output_dir=output_dir)
    if forest:
        download_forest(
            iso3=iso3,
            gdrive_remote_rclone=gdrive_remote_rclone,
            gdrive_folder=gdrive_folder,
            output_dir=output_dir,
        )


# End
