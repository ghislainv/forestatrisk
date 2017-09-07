#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Import
import numpy as np
import os
from osgeo import ogr
import ee_hansen
import ee_roadless
from zipfile import ZipFile  # To unzip files
from urllib import urlretrieve  # To download files from internet
import pandas as pd
import pkg_resources
from miscellaneous import make_dir


# Extent of a shapefile
def extent_shp(inShapefile):
    """Compute the extent of a shapefile.

    This function computes the extent (xmin, xmax, ymin, ymax) of a
    shapefile.

    :param inShapefile: Path to the input shapefile.

    :return: The extent as a tuple (xmin, ymin, xmax, ymax)

    """

    inDriver = ogr.GetDriverByName("ESRI Shapefile")
    inDataSource = inDriver.Open(inShapefile, 0)
    inLayer = inDataSource.GetLayer()
    extent = inLayer.GetExtent()
    extent = (extent[0], extent[2], extent[1], extent[3])
    return(extent)  # (xmin, ymin, xmax, ymax)


# country
def country(iso3, monthyear, proj="EPSG:3395",
            data_country=True,
            fcc_source="gfc", perc=50,
            gs_bucket=None):
    """Function formating the country data.

    This function downloads, computes and formats the country data.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
    GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param monthyear: Date (month and year) for WDPA data
    (e.g. "Aug2017").

    :param data_country: Boolean for running data_country.sh to
    compute country landscape variables. Default to "True".

    :param fcc_source: Source for forest-cover change data. Can be
    "gfc" (Global Forest Change 2015 Hansen data) or
    "roadless". Default to "gfc".

    :param perc: Tree cover percentage threshold to define forest
    (online used if fcc_source="gcf").

    :param gs_bucket: Name of the google storage bucket to use.

    """

    # Identify continent and country from iso3
    print("Identify continent and country from iso3")
    # Continent
    file_countrycode = pkg_resources.resource_filename("deforestprob",
                                                       "data/countrycode.csv")
    data_countrycode = pd.read_csv(file_countrycode, sep=";", header=0)
    continent = data_countrycode.continent[data_countrycode.iso3c == iso3]
    continent = continent.iloc[0].lower()
    # Country
    file_geofab = pkg_resources.resource_filename("deforestprob",
                                                  "data/ctry_geofab.csv")
    data_geofab = pd.read_csv(file_geofab, sep=";", header=0)
    ctry_link_geofab = data_geofab.ctry_link[data_geofab.iso3 == iso3]
    ctry_link_geofab = ctry_link_geofab.iloc[0]

    # Create data_raw directory
    print("Create data_raw directory")
    make_dir("data_raw")

    # Download the zipfile from gadm.org
    print("Download data")
    url = "http://biogeo.ucdavis.edu/data/gadm2.8/shp/" + iso3 + "_adm_shp.zip"
    fname = "data_raw/" + iso3 + "_adm_shp.zip"
    urlretrieve(url, fname)

    # Extract files from zip
    print("Extract files from zip")
    destDir = "data_raw"
    f = ZipFile(fname)
    f.extractall(destDir)
    f.close()
    print("Files extracted")

    # Reproject
    cmd = "ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs '" + proj + "' -f 'ESRI Shapefile' \
    -lco ENCODING=UTF-8 data_raw/ctry_PROJ.shp data_raw/" + iso3 + "_adm0.shp"
    os.system(cmd)

    # Compute extent
    print("Compute extent")
    extent_latlong = extent_shp("data_raw/" + iso3 + "_adm0.shp")
    extent_proj = extent_shp("data_raw/ctry_PROJ.shp")

    # Region with buffer of 5km
    print("Region with buffer of 5km")
    xmin_reg = np.floor(extent_proj[0] - 5000)
    ymin_reg = np.floor(extent_proj[1] - 5000)
    xmax_reg = np.ceil(extent_proj[2] + 5000)
    ymax_reg = np.ceil(extent_proj[3] + 5000)
    extent_reg = (xmin_reg, ymin_reg, xmax_reg, ymax_reg)
    extent = " ".join(map(str, extent_reg))

    # Tiles for SRTM data (see http://dwtkns.com/srtm/)
    print("Tiles for SRTM data")
    # SRTM tiles are 5x5 degrees
    # x: -180/+180
    # y: +60/-60
    xmin_latlong = np.floor(extent_latlong[0])
    ymin_latlong = np.floor(extent_latlong[1])
    xmax_latlong = np.ceil(extent_latlong[2])
    ymax_latlong = np.ceil(extent_latlong[3])
    # Compute SRTM tile numbers
    tile_left = np.int(np.ceil((xmin_latlong + 180.0) / 5.0))
    tile_right = np.int(np.ceil((xmax_latlong + 180.0) / 5.0))
    if (tile_right == tile_left):
        # Trick to make curl globbing work in data_country.sh
        tile_right = tile_left + 1
    tile_top = np.int(np.ceil((-ymax_latlong + 60.0) / 5.0))
    tile_bottom = np.int(np.ceil((-ymin_latlong + 60.0) / 5.0))
    if (tile_bottom == tile_top):
        tile_bottom = tile_top + 1
    # Format variables
    tiles_long = str(tile_left) + "-" + str(tile_right)
    tiles_lat = str(tile_top) + "-" + str(tile_bottom)

    # Google EarthEngine task
    if (fcc_source == "gfc"):
        # Check data availability
        data_availability = ee_hansen.check(gs_bucket, iso3)
        # If not available, run GEE
        if data_availability is False:
            print("Run Google Earth Engine")
            task = ee_hansen.run_task(perc=perc, iso3=iso3,
                                      extent_latlong=extent_latlong,
                                      scale=30,
                                      proj=proj,
                                      gs_bucket=gs_bucket)
            print("GEE running on the following extent:")
            print(str(extent_latlong))

    # Google EarthEngine task
    if (fcc_source == "roadless"):
        # Check data availability
        data_availability = ee_roadless.check(gs_bucket, iso3)
        # If not available, run GEE
        if data_availability is False:
            print("Run Google Earth Engine")
            task = ee_roadless.run_task(perc=perc, iso3=iso3,
                                        extent_latlong=extent_latlong,
                                        scale=30,
                                        proj=proj,
                                        gs_bucket=gs_bucket)
            print("GEE running on the following extent:")
            print(str(extent_latlong))

    # Call data_country.sh
    if (data_country):
        script = pkg_resources.resource_filename("deforestprob",
                                                 "shell/data_country.sh")
        args = ["sh ", script, continent, ctry_link_geofab, iso3,
                "'" + proj + "'",
                "'" + extent + "'", tiles_long, tiles_lat, monthyear]
        cmd = " ".join(args)
        os.system(cmd)

    # Forest computations
    if (fcc_source == "gfc"):
        # Download Google EarthEngine results
        print("Download Google Earth Engine results locally")
        ee_hansen.download(gs_bucket, iso3,
                           path="data_raw")
        # Call forest_country.sh
        print("Forest computations")
        script = pkg_resources.resource_filename("deforestprob",
                                                 "shell/forest_country.sh")
        args = ["sh ", script, "'" + proj + "'", "'" + extent + "'"]
        cmd = " ".join(args)
        os.system(cmd)

    # Forest computations
    if (fcc_source == "roadless"):
        # Download Google EarthEngine results
        print("Download Google Earth Engine results locally")
        ee_hansen.download(gs_bucket, iso3,
                           path="data_raw")
        # Call forest_country.sh
        print("Forest computations")
        script = pkg_resources.resource_filename("deforestprob",
                                                 "shell/forest_country.sh")
        args = ["sh ", script, "'" + proj + "'", "'" + extent + "'"]
        cmd = " ".join(args)
        os.system(cmd)

# End
