"""Download WDPA data."""

import os

from pywdpa import get_wdpa

from ...misc import make_dir


def download_wdpa(iso3, output_dir="."):
    """Download protected areas.

    Protected areas come from the World Database on Protected Areas
    (\\ `<https://www.protectedplanet.net/>`_\\ ). This function uses the
    ``pywdpa`` python package.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_dir: Directory where shapefiles for protected areas
        are downloaded. Default to current working directory.

    """

    # Create directory
    make_dir(output_dir)

    # Check for existing data
    fname = os.path.join(output_dir, "pa_" + iso3 + ".shp")
    if os.path.isfile(fname) is not True:
        owd = os.getcwd()
        os.chdir(output_dir)
        get_wdpa(iso3)
        os.chdir(owd)


# End
