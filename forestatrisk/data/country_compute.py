"""Process country geospatial data."""

import os
from glob import glob
from shutil import rmtree, copy2
import math

from osgeo import gdal

from ..misc import make_dir
from .compute import compute_forest
from .compute import compute_srtm, compute_wdpa, compute_osm
from .compute import compute_biomass_avitabile
from .get_vector_extent import get_vector_extent


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

    # Reproject GADM
    ofile = os.path.join(temp_dir, "ctry_PROJ.gpkg")
    ifile = os.path.join(temp_dir, "gadm41_" + iso3 + "_0.gpkg")
    param = gdal.VectorTranslateOptions(
        accessMode="overwrite",
        srcSRS="EPSG:4326",
        dstSRS=proj,
        reproject=True,
        format="GPKG",
        layerCreationOptions=["ENCODING=UTF-8"],
    )
    gdal.VectorTranslate(ofile, ifile, options=param)

    # Compute extent
    ifile = os.path.join(temp_dir, "ctry_PROJ.gpkg")
    extent_proj = get_vector_extent(ifile)

    # Region with buffer of 5km
    xmin_reg = math.floor(extent_proj[0] - 5000)
    ymin_reg = math.floor(extent_proj[1] - 5000)
    xmax_reg = math.ceil(extent_proj[2] + 5000)
    ymax_reg = math.ceil(extent_proj[3] + 5000)
    extent_reg = (xmin_reg, ymin_reg, xmax_reg, ymax_reg)

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
        make_dir(os.path.join(wd, output_dir, "emissions"))
        copy2("AGB.tif", os.path.join(wd, output_dir, "emissions"))
        dist_files = [f for f in glob("dist_*.tif") if f[-6] != "t"]
        proj_files = [f for f in glob("*_PROJ.*") if f != "ctry_PROJ.tif"]
        other_files = ["altitude.tif", "slope.tif", "pa.tif"]
        files = dist_files + proj_files + other_files
        for file in files:
            copy2(file, os.path.join(wd, output_dir))
        os.chdir(wd)

    # Computing forest data
    if data_forest:
        # Changing working directory
        wd = os.getcwd()
        os.chdir(temp_dir)
        # Perform computations
        compute_forest(proj, extent_reg)
        # Create directories
        make_dir(os.path.join(wd, output_dir, "forest"))
        make_dir(os.path.join(wd, output_dir, "validation"))
        make_dir(os.path.join(wd, output_dir, "forecast"))
        # Copy files for modelling
        ifiles = ["dist_edge_t1.tif", "dist_defor_t1.tif", "fcc12.tif"]
        ofiles = ["dist_edge.tif", "dist_defor.tif", "fcc.tif"]
        for (ifile, ofile) in zip(ifiles, ofiles):
            if os.path.isfile(ifile):
                copy2(ifile, os.path.join(wd, output_dir, ofile))
        # Copy files for validation
        files = ["dist_edge_t2.tif", "dist_defor_t2.tif"]
        for file in files:
            if os.path.isfile(file):
                copy2(file, os.path.join(wd, output_dir, "validation"))
        # Copy files for forecast
        files = ["dist_edge_t3.tif", "dist_defor_t3.tif", "fcc13.tif"]
        for file in files:
            if os.path.isfile(file):
                copy2(file, os.path.join(wd, output_dir, "forecast"))
        # Forest data
        files = [f"forest_t{i}.tif" for i in range(4)]
        files.append("fcc123.tif")
        for file in files:
            if os.path.isfile(file):
                copy2(file, os.path.join(wd, output_dir, "forest"))
        os.chdir(wd)

    # Keep or remove directory
    if not keep_temp_dir:
        rmtree(temp_dir, ignore_errors=True)

# End of file
