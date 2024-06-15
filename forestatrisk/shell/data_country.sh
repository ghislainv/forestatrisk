#!/usr/bin/bash

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# GDAL version    :>=2.1.2 (OGR enabled)
# osmtools        :https://gitlab.com/osm-c-tools/osmctools
# license         :GPLv3
# ==============================================================================

# Variables
iso=$1
proj=$2  # see http://epsg.io 
extent=$3  # xmin ymin xmax ymax
temp_dir=$4
output_dir=$5

# Working directory
cd $temp_dir

# ===================================
# Distance to road, town, and river
# ===================================

# Message
echo "Distance to road, town, and river from OSM\n"
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
        -lco ENCODING=UTF-8 towns_proj.shp towns.shp
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" -ot Byte \
               -a_nodata 255 -a_srs "$proj" \
               -tr 150 150 -l towns_proj towns_proj.shp towns.tif
# roads
ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs "$proj" -f 'ESRI Shapefile' \
        -lco ENCODING=UTF-8 roads_proj.shp roads.shp
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" -ot Byte \
               -a_nodata 255 -a_srs "$proj" \
               -tr 150 150 -l roads_proj roads_proj.shp roads.tif
# rivers
ogr2ogr -overwrite -s_srs EPSG:4326 -t_srs "$proj" -f 'ESRI Shapefile' \
        -lco ENCODING=UTF-8 rivers_proj.shp rivers.shp
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" -ot Byte \
               -a_nodata 255 -a_srs "$proj" \
               -tr 150 150 -l rivers_proj rivers_proj.shp rivers.tif

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
gdaldem slope altitude.tif _slope.tif -compute_edges \
	-co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES"

# Convert to Int16
gdal_translate -ot Int16 \
	       -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
	       _slope.tif slope.tif

# ===========================
# WDPA
# ===========================

# Message
echo "Protected area network from Protected Planet\n"

# Reproject and filter
input_file="pa_"$iso".shp"
ogr2ogr -overwrite -skipfailures -f "ESRI Shapefile" \
	-where "status='Designated' OR status='Inscribed' OR status='Established' OR (status='Proposed' AND CAST(SUBSTR(date,7,4) AS INTEGER) < 2010)" \
        -s_srs EPSG:4326 -t_srs "$proj" \
        -lco ENCODING=UTF-8 pa_proj.shp $input_file

# Rasterize
gdal_rasterize -te $extent -tap -burn 1 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               -init 0 \
               -a_nodata 255 -a_srs "$proj" \
               -ot Byte -tr 30 30 -l pa_proj pa_proj.shp pa.tif

# ===========================
# Carbon
# ===========================

# Message
echo "AGB from Avitabile's map\n"

# Resample
gdalwarp -overwrite -s_srs EPSG:4326 -t_srs "$proj" \
         -te $extent -tap -r bilinear \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -tr 1000 1000 \
	 /vsicurl/https://forestatrisk.cirad.fr/tropics/agb/Avitabile_AGB_Map_cog.tif \
	 AGB.tif

# ===========================
# Cleaning
# ===========================

# Message
echo "Cleaning directory\n"

# Create clean data directory
mkdir -p ../$output_dir
mkdir -p ../$output_dir/emissions
# Copy files
cp -t ../$output_dir dist_*.tif *_proj.* altitude.tif slope.tif pa.tif
cp -t ../$output_dir/emissions AGB.tif
# Return to working director
cd ../

# End
