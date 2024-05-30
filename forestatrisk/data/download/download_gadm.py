"""Download GADM data."""

import os
from urllib.request import urlretrieve


def download_gadm(iso3, output_file):
    """Download GADM data for a country.

    Download GADM (Global Administrative Areas) for a specific
    country. See `<https://gadm.org>`_\\ .

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_file: Path to output GPKG file.

    """

    # Check for existing file
    if not os.path.isfile(output_file):

        # Download the file from gadm.org
        url = ("https://geodata.ucdavis.edu/gadm/gadm4.1/"
               f"gpkg/gadm41_{iso3}.gpkg")
        urlretrieve(url, output_file)


# End
