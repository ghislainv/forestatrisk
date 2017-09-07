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
# Mosaicing
gdalbuildvrt forest.vrt forest_*.tif
# Remove RGBA interpretation of the four bands
gdal_translate -co "PHOTOMETRIC=MINISBLACK" -co "ALPHA=NO" \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest.vrt forest_norgba.tif
# Reprojecting
gdalwarp -te $extent -tap -t_srs "$proj" \
         -tr 30 30 -r near \
         -co "PHOTOMETRIC=MINISBLACK" -co "ALPHA=NO" \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         forest_norgba.tif forest_src.tif

# Separate bands
gdal_translate -mask none -b 1 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t0_src.tif
gdal_translate -mask none -b 2 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t1_src.tif
gdal_translate -mask none -b 3 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t2_src.tif
gdal_translate -mask none -b 4 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t3_src.tif

# =====
# 1. Compute distance to forest edge at t1
# =====

# Message
echo "Computing distance to forest edge\n"
#
gdal_proximity.py forest_t1_src.tif _dist_edge.tif \
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

# Create raster fcc01_src.tif
gdal_calc.py --overwrite -A forest_t0_src.tif -B forest_t1_src.tif \
             --outfile=fcc01_src.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Compute distance
gdal_proximity.py fcc01_src.tif _dist_defor_src.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO

# Mask with forest_t1_src.tif
gdal_calc.py --overwrite -A _dist_defor_src.tif -B forest_t1_src.tif \
             --outfile=dist_defor.tif --type=UInt32 \
             --calc="A*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=0

# gdal_translate -a_nodata 0 \
#                -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
#                _dist_defor.tif dist_defor.tif

# =====
# 3. Forest-cover change raster
# =====

# Message
echo "Computing forest-cover change raster\n"

# Create raster fcc12_src.tif
gdal_calc.py --overwrite -A forest_t1_src.tif -B forest_t2_src.tif \
             --outfile=fcc12_src.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Mask with country border
gdalwarp -overwrite -srcnodata 255 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_PROJ.shp \
         fcc12_src.tif fcc12.tif

# =====
# 4. Cropping forest rasters
# =====

# Message
echo "Cropping forest rasters\n"

# Mask with country border
gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_PROJ.shp \
         forest_t0_src.tif forest_t0.tif

gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_PROJ.shp \
         forest_t1_src.tif forest_t1.tif

gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_PROJ.shp \
         forest_t2_src.tif forest_t2.tif

gdalwarp -overwrite -srcnodata 0 -dstnodata 255 \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         -cutline ctry_PROJ.shp \
         forest_t3_src.tif forest_t3.tif

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
rm -R data_raw

# End
