#!/usr/bin/bash

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# GDAL version    :>=2.1.2 (OGR enabled)
# osmtools        :https://gitlab.com/osm-c-tools/osmctools
# license         :GPLv3
# ==============================================================================

# Working directory
cd data_raw

# Variables
continent=$1
country=$2
iso=$3
proj=$4  # see http://epsg.io 
extent=$5  # xmin ymin xmax ymax
tiles_long=$6  # see http://dwtkns.com/srtm/
tiles_lat=$7
monthyear=$8

# ===========================
# Borders, roads and town
# ===========================

# Message
echo "Borders, roads, towns and rivers from OSM\n"

# Download OSM data from Geofabrik
url="http://download.geofabrik.de/"$continent"/"$country"-latest.osm.pbf"
wget -nc -O country.osm.pbf $url
osmconvert country.osm.pbf -o=country.o5m

# Main roads
osmfilter country.o5m --keep='highway=motorway or highway=trunk or highway=*ary' > roads.osm
ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress \
        -sql 'SELECT osm_id, name, highway FROM lines WHERE highway IS NOT NULL' \
        -lco ENCODING=UTF-8 roads.shp roads.osm
# Main towns
osmfilter country.o5m --keep='place=city or place=town or place=village' > towns.osm
ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress \
        -sql 'SELECT osm_id, name, place FROM points WHERE place IS NOT NULL' \
        -lco ENCODING=UTF-8 towns.shp towns.osm
# Main rivers
osmfilter country.o5m --keep='waterway=river or waterway=canal' > rivers.osm
ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress \
        -sql 'SELECT osm_id, name, waterway FROM lines WHERE waterway IS NOT NULL' \
        -lco ENCODING=UTF-8 rivers.shp rivers.osm

# Rasterize after reprojection
# We need to use -a_srs for gdal_rasterize because reprojection 
# with ogr2ogr can lead to different projection definition (see WKT)
# towns
ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs "$proj" -f 'ESRI Shapefile' \
        -lco ENCODING=UTF-8 towns_PROJ.shp towns.shp
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" -ot Byte \
               -a_nodata 255 -a_srs "$proj" \
               -tr 150 150 -l towns_PROJ towns_PROJ.shp towns.tif
# roads
ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs "$proj" -f 'ESRI Shapefile' \
        -lco ENCODING=UTF-8 roads_PROJ.shp roads.shp
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" -ot Byte \
               -a_nodata 255 -a_srs "$proj" \
               -tr 150 150 -l roads_PROJ roads_PROJ.shp roads.tif
# rivers
ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs "$proj" -f 'ESRI Shapefile' \
        -lco ENCODING=UTF-8 rivers_PROJ.shp rivers.shp
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" -ot Byte \
               -a_nodata 255 -a_srs "$proj" \
               -tr 150 150 -l rivers_PROJ rivers_PROJ.shp rivers.tif

# Compute distances
gdal_proximity.py roads.tif _dist_road.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 1 -ot UInt32 -distunits GEO
gdal_proximity.py towns.tif _dist_town.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 1 -ot UInt32 -distunits GEO
gdal_proximity.py rivers.tif _dist_river.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 1 -ot UInt32 -distunits GEO

# Add nodata
gdal_translate -a_nodata 4294967295 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_road.tif dist_road.tif
gdal_translate -a_nodata 4294967295 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_town.tif dist_town.tif
gdal_translate -a_nodata 4294967295 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_river.tif dist_river.tif

# ===========================
# SRTM
# ===========================

# Message
echo "SRTM data from CGIAR-CSI\n"

# Download SRTM data from CSI CGIAR
url="http://srtm.csi.cgiar.org/wp-content/uploads/files/srtm_5x5/TIFF/srtm_["$tiles_long"]_["$tiles_lat"].zip"
curl -L $url -o 'SRTM_V41_#1_#2.zip'

# Unzip
for z in SRTM_*.zip; do
d=$(basename $z .zip)
mkdir $d && unzip $z -d $d
done

# Build vrt file
gdalbuildvrt srtm.vrt SRTM_*/*.tif

# Merge and reproject
gdalwarp -overwrite -t_srs "$proj" -te $extent -tap -r bilinear \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -tr 90 90 srtm.vrt altitude.tif

# Compute slope
gdaldem slope altitude.tif slope_.tif -compute_edges -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES"

# Convert to Int16
gdal_translate -ot Int16 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" slope_.tif slope.tif

# ===========================
# SAPM
# ===========================

# Message
echo "Protected area network from Protected Planet\n"
# See protected planet: www.protectedplanet.net

# Download from Protected Planet
pywdpa.py $iso

# Reproject
input_file="pa_"$iso".shp"
ogr2ogr -overwrite -skipfailures -f 'ESRI Shapefile' -progress \
        -s_srs EPSG:4326 -t_srs "$proj" \
        -lco ENCODING=UTF-8 pa_PROJ.shp $input_file

# Rasterize
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               -init 0 \
               -a_nodata 255 -a_srs "$proj" \
               -ot Byte -tr 30 30 -l pa_PROJ pa_PROJ.shp pa.tif

# ===========================
# Carbon
# ===========================

# Message
echo "AGB from Avitabile's map\n"

# Download
# url="https://bioscenemada.cirad.fr/FileTransfer/JRC/Avitabile_AGB_Map.tif"
# wget -O Avitabile_AGB_Map.tif $url
cp /home/www/bioscenemada/FileTransfer/JRC/Avitabile_AGB_Map.tif ./

# Resample
gdalwarp -overwrite -s_srs EPSG:4326 -t_srs "$proj" \
         -te $extent -tap -r bilinear \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -tr 1000 1000 Avitabile_AGB_Map.tif AGB.tif

# ===========================
# Cleaning
# ===========================

# Message
echo "Cleaning directory\n"

# Create clean data directory
mkdir -p ../data
mkdir -p ../data/emissions
# Copy files
cp -t ../data dist_*.tif *_PROJ.* altitude.tif slope.tif pa.tif
cp -t ../data/emissions AGB.tif
# Remove AGB to save some space on disk if folder data_raw is not removed
rm Avitabile_AGB_Map.tif
# Return to working director
cd ../

# End
