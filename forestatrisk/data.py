#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Import
from __future__ import division, print_function  # Python 3 compatibility
import numpy as np
import os
from shutil import rmtree
from osgeo import ogr
#import ee_hansen_gcs
#import ee_roadless_gcs
from . import ee_jrc
from zipfile import ZipFile  # To unzip files
import pandas as pd
import pkg_resources
from .miscellaneous import make_dir
try:
    from urllib.request import urlretrieve  # To download files from internet
except ImportError:
    from urllib import urlretrieve  # urllib with Python 2


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
            data_forest=True,
            keep_data_raw=False,
            fcc_source="jrc", perc=50,
            gdrive_remote_rclone=None,
            gdrive_folder=None):
    """Function formating the country data.

    This function downloads, computes and formats the country data.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
    GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param monthyear: Date (month and year) for WDPA data
    (e.g. "Aug2017").

    :param data_country: Boolean for running data_country.sh to
    compute country landscape variables. Default to "True".

    :param data_forest: Boolean for running data_forest.sh to
    compute forest landscape variables. Default to "True".

    :param keep_data_raw: Boolean to keep the data_raw folder. Default
    to "False".

    :param fcc_source: Source for forest-cover change data. Can be
    "gfc" (Global Forest Change data) or "jrc" (Joint Research Center
    data). Default to "jrc".

    :param perc: Tree cover percentage threshold to define forest
    (online used if fcc_source="gcf").

    :param gdrive_remote_rclone: Name of the Google Drive remote for rclone.

    :param gdrive_folder: Name of the Google Drive folder to use.

    """

    # Identify continent and country from iso3
    print("Identify continent and country from iso3")
    # Geofabrik data
    file_geofab = pkg_resources.resource_filename("forestatrisk",
                                                  "data/ctry_geofab.csv")
    data_geofab = pd.read_csv(file_geofab, sep=";", header=0)
    # Country
    ctry_link_geofab = data_geofab.ctry_link[data_geofab.iso3 == iso3]
    ctry_link_geofab = ctry_link_geofab.iloc[0]
    # Continent
    continent = data_geofab.continent[data_geofab.iso3 == iso3]
    continent = continent.iloc[0].lower()

    # Create data_raw directory
    print("Create data_raw directory")
    make_dir("data_raw")

    # Download the zipfile from gadm.org
    print("Download data")
    url = "http://biogeo.ucdavis.edu/data/gadm3.6/shp/gadm36_" + iso3 + "_shp.zip"
    fname = "data_raw/" + iso3 + "_shp.zip"
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
    -lco ENCODING=UTF-8 data_raw/ctry_PROJ.shp data_raw/gadm36_" + iso3 + "_0.shp"
    os.system(cmd)

    # Compute extent
    print("Compute extent")
    extent_latlong = extent_shp("data_raw/gadm36_" + iso3 + "_0.shp")
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
    # Format variables, zfill is for having 01 and not 1
    tiles_long = str(tile_left).zfill(2) + "-" + str(tile_right).zfill(2)
    tiles_lat = str(tile_top).zfill(2) + "-" + str(tile_bottom).zfill(2)

    # Google EarthEngine task
    if (data_forest):
        if (fcc_source == "jrc"):
            # Check data availability
            data_availability = ee_jrc.check(gdrive_remote_rclone,
                                             gdrive_folder, iso3)
            # If not available, run GEE
            if data_availability is False:
                print("Run Google Earth Engine")
                task = ee_jrc.run_task(iso3=iso3,
                                       extent_latlong=extent_latlong,
                                       scale=30,
                                       proj=proj,
                                       gdrive_folder=gdrive_folder)
                print("GEE running on the following extent:")
                print(str(extent_latlong))

    # Call data_country.sh
    if (data_country):
        script = pkg_resources.resource_filename("forestatrisk",
                                                 "shell/data_country.sh")
        args = ["sh ", script, continent, ctry_link_geofab, iso3,
                "'" + proj + "'",
                "'" + extent + "'", tiles_long, tiles_lat, monthyear]
        cmd = " ".join(args)
        os.system(cmd)

    # Forest computations
    if (data_forest):
        if (fcc_source == "jrc"):
            # Download Google EarthEngine results
            print("Download Google Earth Engine results locally")
            ee_jrc.download(gdrive_remote_rclone,
                            gdrive_folder,
                            iso3,
                            output_path="data_raw")
            # Call forest_country.sh
            print("Forest computations")
            script = pkg_resources.resource_filename("forestatrisk",
                                                     "shell/forest_country.sh")
            args = ["sh ", script, "'" + proj + "'", "'" + extent + "'"]
            cmd = " ".join(args)
            os.system(cmd)

    # Delete data_raw
    if (keep_data_raw is False):
        for root, dirs, files in os.walk("data_raw", topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))


# country_forest_gdrive
def country_forest_gdrive(iso3, proj="EPSG:3395",
                          output_dir="tmp",
                          keep_dir=False,
                          fcc_source="jrc", perc=50,
                          gdrive_remote_rclone=None,
                          gdrive_folder=None):
    """Function to compute the forest rasters per country and have them
    ready on Google Drive.

    This function downloads, computes and formats the country data.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
    GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param output_dir: Directory where shapefile for country border is saved.

    :param keep_dir: Boolean to keep the output_dir folder. Default
    to "False" (directory "tmp" is deleted).

    :param fcc_source: Source for forest-cover change data. Can be
    "gfc" (Global Forest Change data) or "jrc" (Joint Research Center
    data). Default to "jrc".

    :param perc: Tree cover percentage threshold to define forest
    (online used if fcc_source="gcf").

    :param gdrive_remote_rclone: Name of the Google Drive remote for rclone.

    :param gdrive_folder: Name of the Google Drive folder to use.

    """

    # Create temp directory
    print("Create temp directory")
    make_dir(output_dir)

    # Download the zipfile from gadm.org
    print("Download data")
    url = "http://biogeo.ucdavis.edu/data/gadm3.6/shp/gadm36_" + iso3 + "_shp.zip"
    fname = output_dir + "/" + iso3 + "_shp.zip"
    urlretrieve(url, fname)

    # Extract files from zip
    print("Extract files from zip")
    destDir = output_dir
    f = ZipFile(fname)
    f.extractall(destDir)
    f.close()
    print("Files extracted")

    # Compute extent
    print("Compute extent")
    extent_latlong = extent_shp(output_dir + "/gadm36_" + iso3 + "_0.shp")

    # Keep or remove directory
    if not keep_dir:
        rmtree(output_dir, ignore_errors=True)

    # Google EarthEngine task
    if (fcc_source == "jrc"):
        # Check data availability
        data_availability = ee_jrc.check(gdrive_remote_rclone,
                                         gdrive_folder, iso3)
        # If not available, run GEE
        if data_availability is False:
            print("Run Google Earth Engine")
            task = ee_jrc.run_task(iso3=iso3,
                                   extent_latlong=extent_latlong,
                                   scale=30,
                                   proj=proj,
                                   gdrive_folder=gdrive_folder)
            print("GEE running on the following extent:")
            print(str(extent_latlong))

# End
