"""Download OSM data."""

import os

try:
    from urllib.request import urlretrieve  # Python 3
except ImportError:
    from urllib import urlretrieve  # urlretrieve with Python 2

try:
    import importlib.resources as importlib_resources  # Python >= 3.9
except ImportError:
    import importlib_resources

import pandas as pd

from ...misc import make_dir


def download_osm(iso3, output_dir="."):
    """Download OSM data for a country.

    Download OpenStreetMap data from Geofabrik.de or OpenStreetMap.fr
    for aspecific country.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_dir: Directory where data is downloaded. Default to
        current working directory.

    """

    # Create directory
    make_dir(output_dir)

    # Check for existing data
    fname = os.path.join(output_dir, "country.osm.pbf")
    if os.path.isfile(fname) is not True:
        # Identify continent and country from iso3
        relative_path = os.path.join("csv", "ctry_run.csv")
        ref = importlib_resources.files("forestatrisk") / relative_path
        with importlib_resources.as_file(ref) as path:
            data_run = pd.read_csv(path, sep=";", header=0)
        # Check if data is available on Geofabrik
        if not pd.isna(data_run.ctry_geofab[data_run.iso3 == iso3].iloc[0]):
            # Country
            country = data_run.ctry_geofab[data_run.iso3 == iso3]
            country = country.iloc[0]
            # Continent
            continent = data_run.cont_geofab[data_run.iso3 == iso3]
            continent = continent.iloc[0]
            # Download OSM data from Geofabrik
            url = [
                "http://download.geofabrik.de/",
                continent,
                "/",
                country,
                "-latest.osm.pbf",
            ]
            url = "".join(url)
            urlretrieve(url, fname)
        # Else use openstreetmap.fr
        else:
            # Country
            country = data_run.ctry_osmfr[data_run.iso3 == iso3]
            country = country.iloc[0]
            # Continent
            continent = data_run.cont_osmfr[data_run.iso3 == iso3]
            continent = continent.iloc[0]
            # Download OSM data from openstreetmap.fr
            url = [
                "https://download.openstreetmap.fr/extracts/",
                continent,
                "/",
                country,
                ".osm.pbf",
            ]
            url = "".join(url)
            urlretrieve(url, fname)


# End
