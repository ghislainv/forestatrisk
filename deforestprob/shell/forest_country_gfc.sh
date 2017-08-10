#!/usr/bin/bash

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# GDAL version    :2.1.2 (OGR enabled)
# license         :GPLv3
# ==============================================================================

# Working directory
cd data_raw

# ===========================
# Forest
# ===========================

# Message
echo "Forest data obtained with Google EarthEngine\n"

# Variables
proj=$1
extent=$2

# =====
# 0. Mosaicing
# =====

# Message
echo "Mosaicing and reprojecting\n"
#
gdalbuildvrt forest2000.vrt forest2000_*.tif
gdalwarp -te $extent -tap -t_srs "$proj" \
         -tr 30 30 -r near \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         forest2000.vrt forest_t0_gfc.tif

gdalbuildvrt forest2005.vrt forest2005_*.tif
gdalwarp -te $extent -tap -t_srs "$proj" \
         -tr 30 30 -r near \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         forest2005.vrt forest_t1_gfc.tif

gdalbuildvrt forest2010.vrt forest2010_*.tif
gdalwarp -te $extent -tap -t_srs "$proj" \
         -tr 30 30 -r near \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         forest2010.vrt forest_t2_gfc.tif

gdalbuildvrt forest2014.vrt forest2014_*.tif
gdalwarp -te $extent -tap -t_srs "$proj" \
         -tr 30 30 -r near \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         forest2014.vrt forest_t3_gfc.tif

# =====
# 1. Compute distance to forest edge at t1
# =====

# Message
echo "Computing distance to forest edge\n"
#
gdal_proximity.py forest_t1_gfc.tif _dist_edge.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO

gdal_translate -a_nodata 0 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_edge.tif dist_edge.tif

# =====
# 2. Compute distance to past deforestation
# =====

# Message
echo "Computing distance to past deforestation\n"

# Create raster fcc01_gfc.tif
gdal_calc.py --overwrite -A forest_t0_gfc.tif -B forest_t1_gfc.tif \
             --outfile=fcc01_gfc.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Compute distance
gdal_proximity.py fcc01_gfc.tif _dist_defor_gfc.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO

# Mask with forest_t1_gfc.tif
gdal_calc.py --overwrite -A _dist_defor_gfc.tif -B forest_t1_gfc.tif \
             --outfile=dist_defor.tif --type=UInt32 \
             --calc="A*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# gdal_translate -a_nodata 0 \
#                -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
#                _dist_defor.tif dist_defor.tif

# =====
# 3. Forest-cover change raster
# =====

# Message
echo "Computing forest-cover change raster\n"

# Create raster fcc12_gfc.tif
gdal_calc.py --overwrite -A forest_t1_gfc.tif -B forest_t2_gfc.tif \
             --outfile=fcc12_gfc.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Mask with country border
gdalwarp -overwrite -srcnodata 255 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_proj.shp \
         fcc12_gfc.tif fcc12.tif

# =====
# 4. Cropping forest rasters
# =====

# Message
echo "Cropping forest rasters\n"

# Mask with country border
gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_proj.shp \
         forest_t0_gfc.tif forest_t0.tif

gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_proj.shp \
         forest_t1_gfc.tif forest_t1.tif

gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_proj.shp \
         forest_t2_gfc.tif forest_t2.tif

gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_proj.shp \
         forest_t3_gfc.tif forest_t3.tif

# ===========================
# Cleaning
# ===========================

# Message
echo "Cleaning directory\n"

# Create clean data directory
mkdir -p ../data
mkdir -p ../data/forest
# Copy files
cp -t ../data dist_defor.tif dist_edge.tif fcc12.tif
cp -t ../data/forest forest_t0.tif forest_t1.tif forest_t2.tif forest_t3.tif
# Remove raw data directory
cd ../
# rm -R data_raw


# End
