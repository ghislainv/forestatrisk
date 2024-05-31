"""Download country geospatial data."""

import os

import geefcc as gf

from ..misc import make_dir
from .download import download_gadm, download_osm
from .download import download_srtm, download_wdpa

opj = os.path.join


def country_download(
        get_fcc_args,
        iso3,
        output_dir=".",
        gadm=True,
        srtm=True,
        wdpa=True,
        osm=True,
        forest=True):
    """Download country geospatial data.

    Function to download all the data for a specific country. It
    includes GEE forest data, GADM, OSM, SRTM, and WDPA data.

    .. versionadded:: 1.2
       The ``get_fcc_args`` parameter.

    .. versionremoved:: 1.2
       The ``gdrive_remote_rclone`` and ``gdrive_folder`` parameters.

    :param get_fcc_args: Dictionary of arguments for function
       ``get_fcc()`` from Python package ``geefcc``. For example:
       ``{"aoi": "MTQ", "buff": 0.08983152841195216 , "years": [2000,
       2010, 2020], "source": "tmf", "perc": 75, "tile_size": 1,
       "parallel": True, "ncpu": None, "output_file":
       "forest_MTQ.tiff"}``.

    :param iso3: Country iso code used to download GADM, OSM, SRTM,
        and WDPA data. The iso code should correspond to the country
        to which the aoi provided in ``get_fcc_args`` belongs.

    :param output_dir: Directory where data is downloaded. Default to
        current working directory.

    :param gadm: Toggle GADM data download.

    :param srtm: Toggle SRTM data download.

    :param wdpa: Toggle WDPA data download.

    :param osm: Toggle OSM data download.

    :param forest: Toggle forest data download.

    """

    # Message
    print("Downloading data for country " + iso3)

    # Create directory
    make_dir(output_dir)

    # Download
    if gadm:
        ofile = opj(output_dir, "gadm41_" + iso3 + "_0.gpkg")
        download_gadm(iso3=iso3, output_file=ofile)
    if srtm:
        download_srtm(iso3=iso3, output_dir=output_dir)
    if wdpa:
        download_wdpa(iso3=iso3, output_dir=output_dir)
    if osm:
        download_osm(iso3=iso3, output_dir=output_dir)
    if forest:
        gf.get_fcc(
            aoi=get_fcc_args["aoi"],
            buff=get_fcc_args.get("buff", 0),
            years=get_fcc_args.get("years", [2000, 2010, 2020]),
            source=get_fcc_args.get("source", "tmf"),
            perc=get_fcc_args.get("perc", 75),
            tile_size=get_fcc_args.get("tile_size", 1),
            parallel=get_fcc_args.get("parallel", True),
            ncpu=get_fcc_args.get("ncpu", None),
            output_file=get_fcc_args.get("output_file", "fcc.tif")
        )

# End
