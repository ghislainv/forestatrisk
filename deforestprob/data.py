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
import ee_hansen  # To compute fcc with Google EarthEngine
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
            fcc_source="gfc", perc=50,
            gdrive_folder=None):

    """Function formating the country data.

    This function downloads, computes and formats the country data.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
    GDAL/OGR. Default to "EPSG:3395" (World Mercator).

    :param monthyear: Date (month and year) for WDPA data
    (e.g. "Aug2017").

    :param fcc_source: Source for forest-cover change data. Can be
    "gfc" (Global Forest Change 2015 Hansen data) or
    "roadless". Default to "gfc".

    :param perc: Tree cover percentage threshold to define forest
    (online used if fcc_source="gcf").

    :param gdrive_folder: Name of a unique folder in your Drive
    account to export into. Defaults to the root of the drive.

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
    -lco ENCODING=UTF-8 data_raw/ctry_proj.shp data_raw/" + iso3 + "_adm0.shp"
    os.system(cmd)

    # Compute extent
    print("Compute extent")
    extent_latlong = extent_shp("data_raw/" + iso3 + "_adm0.shp")
    extent_proj = extent_shp("data_raw/ctry_proj.shp")

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
    tile_top = np.int(np.ceil((-ymax_latlong + 60.0) / 5.0))
    tile_bottom = np.int(np.ceil((-ymin_latlong + 60.0) / 5.0))
    # Format variables
    tiles_long = str(tile_left) + "-" + str(tile_right)
    tiles_lat = str(tile_top) + "-" + str(tile_bottom)

    # Run Google EarthEngine tasks
    print("Run Google Earth Engine tasks")
    if (fcc_source == "gfc"):
        tasks = ee_hansen.run_tasks(perc=perc, iso3=iso3,
                                    extent_latlong=extent_latlong,
                                    scale=30,
                                    proj=proj,
                                    gdrive_folder="deforestprob")
        print("GEE tasks running on the following extent:")
        print(str(extent_latlong))

    # Call data_country.sh
    script = pkg_resources.resource_filename("deforestprob",
                                             "shell/data_country.sh")
    args = ["sh ", script, continent, ctry_link_geofab, iso3,
            "'" + proj + "'",
            "'" + extent + "'", tiles_long, tiles_lat, monthyear]
    cmd = " ".join(args)
    os.system(cmd)

    # # Data function
    # osm(continent, country=ctry_link_geofab, proj, extent)
    # srtm(tiles_long, tiles_lat, proj, extent)
    # sapm(iso3, monthyear, proj, extent)
    # carbon(proj, extent)

    # Forest computations
    if (fcc_source == "gfc"):
        # Download Google EarthEngine results
        print("Download Google Earth Engine results")
        ee_hansen.download(tasks, path="data_raw", iso3=iso3)
        # Call forest_country.sh
        print("Forest computations")
        script = pkg_resources.resource_filename("deforestprob",
                                                 "shell/forest_country_gfc.sh")
        args = ["sh ", script, "'" + proj + "'", "'" + extent + "'"]
        cmd = " ".join(args)
        os.system(cmd)

# End

# # carbon
# def carbon(proj, extent):
#     # Message
#     print("AGB from Avitabile's map")

#     # Download
#     url = "https://bioscenemada.cirad.fr/FileTransfer/JRC/\
#     Avitabile_AGB_Map.tif"
#     fname = "Avitabile_AGB_Map.tif"
#     urlretrieve(url, fname)

#     # Resample
#     args = ["gdalwarp -overwrite -s_srs EPSG:4326",
#             "-t_srs", proj,
#             "-te", extent,
#             "-r bilinear",
#             "-co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES'",
#             "-tr 1000 1000 Avitabile_AGB_Map.tif AGB.tif"]
#     cmd = " ".join(args)
#     os.system(cmd)


# # osm (for OpenStreetMap)
# def osm(continent, country, proj, extent):
#     # Message
#     print("Borders, roads, towns and rivers from OSM")

#     # Download OSM data from Geofabrik
#     url = "http://download.geofabrik.de/" + continent
#     + "/" + country + "-latest.osm.pbf"
#     urlretrieve(url, country.osm.pbf)
#     os.system("osmconvert country.osm.pbf -o=country.o5m")

#     # Main roads
#     os.system("osmfilter country.o5m --keep='highway=motorway or \
#     highway=trunk or highway=*ary' > roads.osm")
#     os.system("ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress \
#     -sql 'SELECT osm_id, name, highway FROM lines WHERE highway IS NOT NULL' \
#     -lco ENCODING=UTF-8 roads.shp roads.osm")
#     # Main towns
#     os.system("osmfilter country.o5m --keep='place=city or place=town \
#     or place=village' > towns.osm")
#     os.system("ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress \
#     -sql 'SELECT osm_id, name, place FROM points WHERE place IS NOT NULL' \
#     -lco ENCODING=UTF-8 towns.shp towns.osm")
#     # Main rivers
#     os.system("osmfilter country.o5m --keep='waterway=river or \
#     waterway=canal' > rivers.osm")
#     os.system("ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress \
#     -sql 'SELECT osm_id, name, waterway FROM lines \
#     WHERE waterway IS NOT NULL' \
#     -lco ENCODING=UTF-8 rivers.shp rivers.osm")

#     # Rasterize after reprojection
#     # towns
#     os.system("ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs " + proj
#               + " -f 'ESRI Shapefile' \
#               -lco ENCODING=UTF-8 towns_PROJ.shp towns.shp")
#     os.system("gdal_rasterize -te " + extent + " -tap -burn 1 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' -ot Byte \
#     -a_nodata 255 \
#     -tr 150 150 -l towns_PROJ towns_PROJ.shp towns.tif")
#     # roads
#     os.system("ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs " + proj
#               + " -f 'ESRI Shapefile' \
#               -lco ENCODING=UTF-8 roads_PROJ.shp roads.shp")
#     os.system("gdal_rasterize -te " + extent + " -tap -burn 1 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' -ot Byte \
#     -a_nodata 255 \
#     -tr 150 150 -l roads_PROJ roads_PROJ.shp roads.tif")
#     # rivers
#     os.system("ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs " + proj
#               + " -f 'ESRI Shapefile' \
#               -lco ENCODING=UTF-8 rivers_PROJ.shp rivers.shp")
#     os.system("gdal_rasterize -te " + extent + " -tap -burn 1 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' -ot Byte \
#     -a_nodata 255 \
#     -tr 150 150 -l rivers_PROJ rivers_PROJ.shp rivers.tif")

#     # Compute distances
#     os.system("gdal_proximity.py roads.tif _dist_road.tif \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     -values 1 -ot UInt32 -distunits GEO")
#     os.system("gdal_proximity.py towns.tif _dist_town.tif \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     -values 1 -ot UInt32 -distunits GEO")
#     os.system("gdal_proximity.py rivers.tif _dist_river.tif \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     -values 1 -ot UInt32 -distunits GEO")

#     # Add nodata
#     os.system("gdal_translate -a_nodata 4294967295 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     _dist_road.tif dist_road.tif")
#     os.system("gdal_translate -a_nodata 4294967295 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     _dist_town.tif dist_town.tif")
#     os.system("gdal_translate -a_nodata 4294967295 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     _dist_river.tif dist_river.tif")


# # srtm
# def srtm(tiles_long, tiles_lat, proj, extent):
#     # Message
#     print("SRTM data from CGIAR-CSI")

#     # Download SRTM data from CSI CGIAR
#     url = "http://srtm.csi.cgiar.org/SRT-ZIP/SRTM_V41/"
#     + "SRTM_Data_GeoTiff/srtm_[" + tiles_long + "]_["
#     + tiles_lat + "].zip"
#     os.system("curl -L " + url + " -o 'SRTM_V41_#1_#2.zip'")

#     # Unzip
#     for z in glob.glob("SRTM_*.zip"):
#         directory = os.path.basename(z)
#         make_dir(directory)
#         f = ZipFile(z)
#         f.extractall(directory)
#         f.close()

#     # Build vrt file
#     os.system("gdalbuildvrt srtm.vrt */*.tif")

#     # Merge and reproject
#     os.system("gdalwarp -overwrite -t_srs " + proj + " -te " + extent
#               + " -r bilinear \
#               -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#               -tr 90 90 srtm.vrt altitude.tif")

#     # Compute slope and aspect
#     os.system("gdaldem slope altitude.tif slope_.tif \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES'")
#     os.system("gdaldem aspect altitude.tif aspect_.tif \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES'")

#     # Convert to Int16
#     os.system("gdal_translate -ot Int16 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     slope_.tif slope.tif")
#     os.system("gdal_translate -ot Int16 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     aspect_.tif aspect.tif")


# # sapm
# def sapm(iso3, monthyear, proj, extent):
#     # Message
#     print("Protected area network from Protected Planet")
#     # See protected planet: www.protectedplanet.net

#     # Download from Protected Planet
#     url = "https://www.protectedplanet.net/downloads/WDPA_"
#     + monthyear + "_" + iso3 + "?type=shapefile"
#     urlretrieve(url, "pa.zip")
#     f = ZipFile("pa.zip")
#     f.extractall()
#     f.close

#     # Reproject
#     input_file = "WDPA_" + monthyear + "_" + iso3 + "-shapefile-polygons.shp"
#     os.system("ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress"
#               + " -s_srs EPSG:4326 -t_srs " + proj
#               + " -lco ENCODING=UTF-8 pa_PROJ.shp " + input_file)

#     # Rasterize
#     os.system("gdal_rasterize -te " + extent + " -tap -burn 1 \
#                -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#                -init 0 \
#                -a_nodata 255 \
#                -ot Byte -tr 30 30 -l pa_PROJ pa_PROJ.shp pa.tif")


# # forest_gfc
# def forest_gfc(ctry_borders):
#     # Message
#     print("Forest data with Google EarthEngine")

#     # 1. Compute distance to forest edge in 2005
#     os.system("gdal_proximity.py fcc05_10_gfc.tif _dist_edge.tif \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     -values 0 -ot UInt32 -distunits GEO")
#     os.system("gdal_translate -a_nodata 0 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     _dist_edge.tif dist_edge.tif")

#     # 2. Compute distance to past deforestation (loss00_05)
#     # Set nodata different from 255
#     os.system("gdal_translate -a_nodata 99 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     fcc05_10_gfc.tif _fcc05_10.tif")
#     os.system("gdal_translate -a_nodata 99 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     loss00_05_gfc.tif _loss00_05.tif")
#     # Create raster _fcc00_05.tif with 1:for2005, 0:loss00_05
#     os.system("gdal_calc.py --overwrite -A _fcc05_10.tif -B _loss00_05.tif \
#     --outfile=_fcc00_05.tif --type=Byte \
#     --calc='255-254*(A>=1)*(B==0)-255*(A==0)*(B==1)' \
#     --co 'COMPRESS=LZW' --co 'PREDICTOR=2' --co 'BIGTIFF=YES' \
#     --NoDataValue=255")
#     # Mask with country border
#     os.system("gdalwarp -overwrite -srcnodata 255 -dstnodata 255 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     -cutline " + ctry_borders + " _fcc00_05.tif fcc00_05_mask.tif")
#     os.system("gdal_translate \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     fcc00_05_mask.tif fcc00_05.tif")

#     # Compute distance (with option -use_input_nodata YES)
#     os.system("gdal_proximity.py fcc00_05.tif _dist_defor.tif \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     -values 0 -ot UInt32 -distunits GEO -use_input_nodata YES")
#     os.system("gdal_translate -a_nodata 65535 \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     _dist_defor.tif dist_defor.tif")

#     # 3. Forest raster
#     # Create raster fcc05_10.tif with 1:for2010, 0:loss05_10
#     os.system("gdal_calc.py --overwrite -A _fcc05_10.tif \
#     --outfile=fcc05_10_reclass.tif --type=Byte \
#     --calc='255-254*(A==1)-255*(A==2)' \
#     --co 'COMPRESS=LZW' --co 'PREDICTOR=2' --co 'BIGTIFF=YES' \
#     --NoDataValue=255")
#     # Mask with country border
#     os.system("gdalwarp -overwrite -srcnodata 255 -dstnodata 255 \
#     -cutline " + ctry_borders + " fcc05_10_reclass.tif fcc05_10_mask.tif")
#     os.system("gdal_translate \
#     -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
#     fcc05_10_mask.tif fcc05_10.tif")
