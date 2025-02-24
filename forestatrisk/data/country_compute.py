"""Process country geospatial data."""

import os
from glob import glob
from shutil import rmtree, copy2
import importlib.resources as importlib_resources

import pandas as pd

from ..misc import make_dir
from .compute import compute_forest
from .compute import (
    compute_gadm, compute_srtm,
    compute_wdpa, compute_osm
)
from .compute import compute_biomass_avitabile


def get_iso_wdpa(isocode):
    """Get isocode for WDPA from country/state isocode.

    The isocode for WDPA is always three letters (XXX) while the
    country/state isocode can be three letters (XXX) or more
    (XXX-XX).

    :param isocode: Country/state isocode.

    :return: isocode for wdpa.

    """
    relative_path = os.path.join("csv", "ctry_run.csv")
    ref = importlib_resources.files("forestatrisk") / relative_path
    with importlib_resources.as_file(ref) as path:
        data_run = pd.read_csv(path, sep=";", header=0)
    iso_wdpa = data_run.loc[data_run["iso3"] == isocode,
                            "iso_wdpa"].values[0]
    return iso_wdpa


def country_compute(
    aoi_code,
    iso_code,
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

    :param aoi_code: Area of Interest isocode. Used for GADM.

    :param iso_code: Country/state isocode. Used for WDPA and OSM.

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

    # Reproject aoi file and compute extent
    # with compute_gadm()
    ifile = os.path.join(temp_dir, "gadm41_" + aoi_code + "_0.gpkg")
    if not os.path.isfile(ifile):
        ifile = os.path.join(temp_dir, "aoi_latlon.gpkg")
    ofile = os.path.join(temp_dir, "aoi_proj.gpkg")
    extent_reg = compute_gadm(ifile, ofile, proj, buff=5000)

    # Computing country data
    if data_country:
        # Changing working directory
        wd = os.getcwd()
        os.chdir(temp_dir)
        # Get iso for wdpa
        iso_wdpa = get_iso_wdpa(iso_code)
        # Perform computations
        compute_osm(proj, extent_reg)
        compute_srtm(proj, extent_reg)
        compute_wdpa(iso_wdpa, proj, extent_reg)
        compute_biomass_avitabile(proj, extent_reg)
        # Moving created files
        dist_files = [f for f in glob("dist_*.tif") if f[-6] != "t"]
        aoi_files = ["aoi_proj.tif", "aoi_proj.gpkg"]
        proj_files = [f for f in glob("*_proj.*") if f not in aoi_files]
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
        aoi_file = ["aoi_proj.gpkg"]
        ifiles = (forest_files + dist_edge_files +
                  dist_defor_files + fcc_files + aoi_file)
        for ifile in ifiles:
            if os.path.isfile(ifile):
                copy2(ifile, os.path.join(wd, output_dir))
        os.chdir(wd)

    # Keep or remove directory
    if not keep_temp_dir:
        rmtree(temp_dir, ignore_errors=True)

# End of file
