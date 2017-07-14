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
from zipfile import ZipFile  # To unzip files
from urllib import urlretrieve  # To download files from internet
import pandas as pd
import pkg_resources
from miscellaneous import make_dir

# File with African projection information
file_proj = pkg_resources.resource_filename("deforestprob",
                                            "data/proj.prj")


# Extent of a shapefile
def extent_shp(inShapefile):
    inDriver = ogr.GetDriverByName("ESRI Shapefile")
    inDataSource = inDriver.Open(inShapefile, 0)
    inLayer = inDataSource.GetLayer()
    extent = inLayer.GetExtent()
    return(extent)  # xmin, xmax, ymin, ymax


# data_ctry
def data_country(iso3, proj=file_proj, monthyear="July2017"):

    """Function formating the country data.

    This function downloads, computes and formats the country data.

    :param iso3: country ISO 3166-1 alpha-3 code.
    :param proj: coordinate system as in GDAL/OGR (e.g. 'EPSG:4326').
    :param monthyear: date (month and year) for WDPA data(e.g. "July2017")

    """

    # Identify continent and country from iso3
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
    make_dir("data_raw")

    # Download the zipfile from gadm.org
    print "Download data"
    url = "http://biogeo.ucdavis.edu/data/gadm2.8/shp/" + iso3 + "_adm_shp.zip"
    fname = "data_raw/" + iso3 + "_adm_shp.zip"
    urlretrieve(url, fname)

    # Extract files from zip
    print "Extract files from zip"
    destDir = "data_raw"
    f = ZipFile(fname)
    f.extractall(destDir)
    f.close()
    print "Files extracted"

    # Reproject
    cmd = "ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs " + proj + " -f 'ESRI Shapefile' \
    -lco ENCODING=UTF-8 data_raw/ctry_proj.shp data_raw/" + iso3 + "_adm0.shp"
    os.system(cmd)

    # Computing extents
    extent_latlong = extent_shp("data_raw/" + iso3 + "_adm0.shp")
    extent_proj = extent_shp("data_raw/ctry_proj.shp")

    # Region with buffer of 5km
    xmin_reg = np.floor(extent_proj[0] - 5000)
    xmax_reg = np.ceil(extent_proj[1] + 5000)
    ymin_reg = np.floor(extent_proj[2] - 5000)
    ymax_reg = np.ceil(extent_proj[3] + 5000)
    extent_reg = (xmin_reg, ymin_reg, xmax_reg, ymax_reg)
    extent = " ".join(map(str, extent_reg))

    # Tiles for SRTM data (see http://dwtkns.com/srtm/)
    # SRTM tiles are 5x5 degrees
    # x: -180/+180
    # y: +60/-60
    xmin_latlong = np.floor(extent_latlong[0])
    xmax_latlong = np.ceil(extent_latlong[1])
    ymin_latlong = np.floor(extent_latlong[2])
    ymax_latlong = np.ceil(extent_latlong[3])
    # Compute SRTM tile numbers
    tile_left = np.int(np.ceil((xmin_latlong + 180.0) / 5.0))
    tile_right = np.int(np.ceil((xmax_latlong + 180.0) / 5.0))
    tile_top = np.int(np.ceil((-ymax_latlong + 60.0) / 5.0))
    tile_bottom = np.int(np.ceil((-ymin_latlong + 60.0) / 5.0))
    # Format variables
    tiles_long = str(tile_left) + "-" + str(tile_right)
    tiles_lat = str(tile_top) + "-" + str(tile_bottom)

    # Call data.sh
    script = pkg_resources.resource_filename("deforestprob",
                                             "shell/data_country.sh")
    args = ["sh ", script, continent, ctry_link_geofab, iso3, "'" + proj + "'",
            "'" + extent + "'", tiles_long, tiles_lat, monthyear]
    cmd = " ".join(args)
    os.system(cmd)

# ============================================================================
# End of country.py
# ============================================================================
