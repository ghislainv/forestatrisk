"""Download GADM data."""

import os
from zipfile import ZipFile

try:
    from urllib.request import urlretrieve  # Python 3
except ImportError:
    from urllib import urlretrieve  # urlretrieve with Python 2

from ...misc import make_dir


def download_gadm(iso3, output_dir="."):
    """Download GADM data for a country.

    Download GADM (Global Administrative Areas) for a specific
    country. See `<https://gadm.org>`_\\ .

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_dir: Directory where data is downloaded. Default to
        current working directory.

    """

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


# End
