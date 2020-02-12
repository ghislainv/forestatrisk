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
from glob import glob # To explore files in a folder
from . import ee_jrc
from zipfile import ZipFile  # To unzip files
from pywdpa import get_wdpa
import pandas as pd
import pkg_resources
import subprocess
from .miscellaneous import make_dir
try:
    from urllib.request import urlretrieve  # Python 3
except ImportError:
    from urllib import urlretrieve  # urlretrieve with Python 2
try:
    from urllib.error import HTTPError  # Python 3
except ImportError:
    from urllib2 import HTTPError  # HTTPError with Python 2


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


# tiles_srtm
def tiles_srtm(extent_latlong):
    """Compute lat/long tiles for SRTM data from an extent.

    This function computes lat/long tiles for SRTM data from an extent
    in lat/long. See <http://dwtkns.com/srtm/>. SRTM tiles are 5x5
    degrees. x: -180/+180, y: +60/-60.

    :param extent_latlong: Extent in lat/long: (xmin, ymin, xmax, ymax).

    :return: A tuple of two strings indicating tile numbers for lat and long.

    """

    # Tiles for SRTM data
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
    return (tiles_long, tiles_lat)


# country
def country(iso3, proj="EPSG:3395",
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
    print("Identify database, continent, and country from iso3")
    # Geofabrik data
    file_run = pkg_resources.resource_filename("forestatrisk",
                                               "data/ctry_run.csv")
    data_run = pd.read_csv(file_run, sep=";", header=0)
    if data_run.ctry_geofab[data_run.iso3 == iso3] != "NA":
        # Database
        db_osm = "geofab"
        # Country
        country = data_run.ctry_geofab[data_run.iso3 == iso3]
        country = country.iloc[0]
        # Continent
        continent = data_run.cont_geofab[data_run.iso3 == iso3]
        continent = continent.iloc[0]
        # Download OSM data from Geofabrik
        url = ["http://download.geofabrik.de/", continent, "/",
               country, "-latest.osm.pbf"]
        url = "".join(url)
        urlretrieve(url, fname)
    else:
        # Database
        db_osm = "osmfr"
        # Country
        country = data_run.ctry_osmfr[data_run.iso3 == iso3]
        country = country.iloc[0]
        # Continent
        continent = data_run.cont_osmfr[data_run.iso3 == iso3]
        continent = continent.iloc[0]
        # Download OSM data from openstreetmap.fr
        url = ["https://download.openstreetmap.fr/extracts/", continent, "/",
               country, ".osm.pbf"]
        url = "".join(url)
        urlretrieve(url, fname)

    # Create data_raw directory
    print("Create data_raw directory")
    make_dir("data_raw")

    # Download the zipfile from gadm.org
    print("Download GADM data")
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
    subprocess.call(cmd, shell=True)

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

    # Tiles for SRTM data
    print("Tiles for SRTM data")
    tiles_long, tiles_lat = tiles_srtm(extent_latlong)

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
        args = ["sh ", script, db_osm, continent, country, iso3,
                "'" + proj + "'",
                "'" + extent + "'", tiles_long, tiles_lat]
        cmd = " ".join(args)
        subprocess.call(cmd, shell=True)

    # Forest computations
    if (data_forest):
        if (fcc_source == "jrc"):
            # Download Google EarthEngine results
            print("Download Google Earth Engine results locally")
            ee_jrc.download(gdrive_remote_rclone,
                            gdrive_folder,
                            iso3,
                            output_dir="data_raw")
            # Call forest_country.sh
            print("Forest computations")
            script = pkg_resources.resource_filename("forestatrisk",
                                                     "shell/forest_country.sh")
            args = ["sh ", script, "'" + proj + "'", "'" + extent + "'"]
            cmd = " ".join(args)
            subprocess.call(cmd, shell=True)

    # Delete data_raw
    if (keep_data_raw is False):
        for root, dirs, files in os.walk("data_raw", topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))


# country_forest_gdrive
def country_forest_gdrive(iso3, proj="EPSG:3395",
                          output_dir="data_raw",
                          keep_dir=True,
                          fcc_source="jrc", perc=50,
                          gdrive_remote_rclone=None,
                          gdrive_folder=None):
    """Compute the forest rasters per country with GEE and have them
    ready on Google Drive.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
    GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param output_dir: Directory where shapefile for country border is saved.

    :param keep_dir: Boolean to keep the output_dir folder. Default
    to "True" (directory "data_raw" is not deleted).

    :param fcc_source: Source for forest-cover change data. Can be
    "gfc" (Global Forest Change data) or "jrc" (Joint Research Center
    data). Default to "jrc".

    :param perc: Tree cover percentage threshold to define forest
    (online used if fcc_source="gcf").

    :param gdrive_remote_rclone: Name of the Google Drive remote for rclone.

    :param gdrive_folder: Name of the Google Drive folder to use.

    """

    # Create directory
    make_dir(output_dir)

    # Check for existing data
    shp_name = output_dir + "/gadm36_" + iso3 + "_0.shp"
    if os.path.isfile(shp_name) is not True:

        # Download the zipfile from gadm.org
        fname = output_dir + "/" + iso3 + "_shp.zip"
        url = "http://biogeo.ucdavis.edu/data/gadm3.6/shp/gadm36_" + iso3 + "_shp.zip"
        urlretrieve(url, fname)

        # Extract files from zip
        destDir = output_dir
        f = ZipFile(fname)
        f.extractall(destDir)
        f.close()

    # Compute extent
    extent_latlong = extent_shp(shp_name)

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


# country_forest_download
def country_forest_download(iso3,
                            gdrive_remote_rclone,
                            gdrive_folder,
                            output_dir=os.getcwd()):
    """Download forest-cover data from Google Drive.

    Download forest-cover data from Google Drive in the current
    working directory. Print a message if the file is not available.

    RClone program is needed: https://rclone.org.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param gdrive_remote_rclone: Google Drive remote name in rclone.

    :param gdrive_folder: the Google Drive folder to look in.

    :param output_dir: Output directory to download files to. Default
    to current working directory.

    """

    # Check for existing data locally 
    srtm_tif = output_dir + "/forest_" + iso3 + "*.tif"
    raster_list = glob(srtm_tif)

    # If no data locally check if available in gdrive
    if len(raster_list) == 0:
        # Data availability in gdrive
        data_availability = ee_jrc.check(gdrive_remote_rclone,
                                         gdrive_folder,
                                         iso3)

        # Donwload if available in gdrive
        if data_availability is True:
            # Commands to download results with rclone
            remote_path = gdrive_remote_rclone + ":" + gdrive_folder
            pattern = "'forest_" + iso3 + "*.tif'"
            cmd = ["rclone", "copy", "--include", pattern, remote_path, output_dir]
            cmd = " ".join(cmd)
            subprocess.call(cmd, shell=True)
            print("Data for {0:3s} has been downloaded".format(iso3))

        else:
            print("Data for {0:3s} is not available".format(iso3))


# country_wdpa
def country_wdpa(iso3, output_dir=os.getcwd()):
    """Function to download the protected areas per country.

    Protected areas comes from the World Database on Protected Areas
    (<https://www.protectedplanet.net/>). This function uses the
    pywdpa python package.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_dir: Directory where shapefiles for protected areas
    are downloaded. Default to current working directory.

    """

    # Create directory
    make_dir(output_dir)

    # Check for existing data
    fname = output_dir + "/pa_" + iso3 + ".shp"
    if os.path.isfile(fname) is not True:
        # Download WDPA
        get_wdpa(iso3, output_dir)


# country_osm
def country_osm(iso3, output_dir=os.getcwd()):
    """Function to download OSM data for a country.

    Function to download OpenStreetMap data from Geofabrik for a
    specific country.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_dir: Directory where data is downloaded. Default to
    current working directory.

    """

    # Create directory
    make_dir(output_dir)

    # Check for existing data
    fname = output_dir + "/" + "country.osm.pbf"
    if os.path.isfile(fname) is not True:
        # Identify continent and country from iso3
        file_run = pkg_resources.resource_filename("forestatrisk",
                                                   "data/ctry_run.csv")
        data_run = pd.read_csv(file_run, sep=";", header=0)
        # Check if data is available on Geofabrik
        if not pd.isna(data_run.ctry_geofab[data_run.iso3 == iso3].iloc[0]):
            # Country
            country = data_run.ctry_geofab[data_run.iso3 == iso3]
            country = country.iloc[0]
            # Continent
            continent = data_run.cont_geofab[data_run.iso3 == iso3]
            continent = continent.iloc[0]
            # Download OSM data from Geofabrik
            url = ["http://download.geofabrik.de/", continent, "/",
                   country, "-latest.osm.pbf"]
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
            url = ["https://download.openstreetmap.fr/extracts/", continent, "/",
                   country, ".osm.pbf"]
            url = "".join(url)
            urlretrieve(url, fname)


# country_srtm
def country_srtm(iso3, output_dir=os.getcwd()):
    """Function to download SRTM data for a country.

    Function to download SRTM data (Shuttle Radar Topographic Mission
    v4.1) from CSI-CGIAR for a specific country.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param output_dir: Directory where data is downloaded. Default to
    current working directory.

    """

    # Create directory
    make_dir(output_dir)

    # Check for existing data
    shp_name = output_dir + "/gadm36_" + iso3 + "_0.shp"
    if os.path.isfile(shp_name) is not True:

        # Download the zipfile from gadm.org
        fname = output_dir + "/" + iso3 + "_shp.zip"
        url = "http://biogeo.ucdavis.edu/data/gadm3.6/shp/gadm36_" + iso3 + "_shp.zip"
        urlretrieve(url, fname)

        # Extract files from zip
        destDir = output_dir
        f = ZipFile(fname)
        f.extractall(destDir)
        f.close()

    # Compute extent and SRTM tiles
    extent_latlong = extent_shp(shp_name)
    tiles_long, tiles_lat = tiles_srtm(extent_latlong)
    tiles_long = [int(i) for i in tiles_long.split("-")]
    tiles_lat = [int(i) for i in tiles_lat.split("-")]

    # Download SRTM data from CSI CGIAR
    for tlong in range(tiles_long[0], tiles_long[1] + 1):
        for tlat in range(tiles_lat[0], tiles_lat[1] + 1):
            # Check for existing data
            fname = output_dir + "/SRTM_V41_" + tlong + "_" + tlat + ".zip"
            if os.path.isfile(fname) is not True:
                # Download
                url=["http://srtm.csi.cgiar.org/",
                     "wp-content/uploads/files/srtm_5x5/TIFF/srtm_", tlong,
                     "_", tlat, ".zip"]
                url = "".join(url)
                try:
                    urlretrieve(url, fname)
                except HTTPError as err:
                    if err.code == 404:
                        print("SRTM not existing for tile: " + tlong + "_" + tlat)
                    else:
                        raise

# End
