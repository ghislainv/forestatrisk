"""Process country geospatial data."""

import os
from glob import glob
from shutil import rmtree, copy2

from ..misc import make_dir
from .compute import compute_forest
from .compute import (
    compute_gadm, compute_srtm,
    compute_wdpa, compute_osm
)
from .compute import compute_biomass_avitabile


def country_compute(
    iso3,
    temp_dir="data_raw",
    output_dir="data",
    proj="EPSG:3395",
    data_country=True,
    data_forest=True,
    keep_temp_dir=False,
):
    """Process country geospatial data.

    This function computes and formats the country data. Computations
    are done in a temporary directory where data have been downloaded
    (default to "data_raw"). Then data are copied to an output
    directory (default to "data").

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param temp_dir: Temporary directory for computation. Relative
        path to the current working directory.

    :param output_dir: Output directory. Relative path to the current
        working directory.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param data_country: Boolean to compute environmental
        variables for the country. Default to "True".

    :param data_forest: Boolean to compute forest variables. Default
        to "True".

    :param keep_temp_dir: Boolean to keep the temporary
        directory. Default to "False".

    """

    # Create output directory
    make_dir(output_dir)

    # Compute aoi file and extent from GADM file
    ifile = os.path.join(temp_dir, "gadm41_" + iso3 + "_0.gpkg")
    ofile = os.path.join(temp_dir, "aoi_proj.gpkg")
    extent_reg = compute_gadm(ifile, ofile, proj)

    # Computing country data
    if data_country:
        # Changing working directory
        wd = os.getcwd()
        os.chdir(temp_dir)
        # Perform computations
        compute_osm(proj, extent_reg)
        compute_srtm(proj, extent_reg)
        compute_wdpa(iso3, proj, extent_reg)
        compute_biomass_avitabile(proj, extent_reg)
        # Moving created files
        dist_files = [f for f in glob("dist_*.tif") if f[-6] != "t"]
        proj_files = [f for f in glob("*_proj.*") if f != "aoi_proj.tif"]
        other_files = ["altitude.tif", "slope.tif", "pa.tif", "AGB.tif"]
        ifiles = dist_files + proj_files + other_files
        for ifile in ifiles:
            copy2(ifile, os.path.join(wd, output_dir))
        os.chdir(wd)

    # Computing forest data
    if data_forest:
        # Changing working directory
        wd = os.getcwd()
        os.chdir(temp_dir)
        # Perform computations
        compute_forest(proj, extent_reg)
        # Copy files for modelling
        forest_files = [f"forest_t{i + 1}.tif" for i in range(3)]
        dist_edge_files = [f"dist_edge_t{i + 1}.tif" for i in range(3)]
        dist_defor_files = [f"dist_defor_t{i + 1}.tif" for i in range(3)]
        fcc_files = ["fcc12.tif", "fcc13.tif", "fcc123.tif"]
        ifiles = forest_files + dist_edge_files + dist_defor_files + fcc_files
        for ifile in ifiles:
            if os.path.isfile(ifile):
                copy2(ifile, os.path.join(wd, output_dir))
        os.chdir(wd)

    # Keep or remove directory
    if not keep_temp_dir:
        rmtree(temp_dir, ignore_errors=True)

# End of file
