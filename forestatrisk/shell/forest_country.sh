#!/usr/bin/bash

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# GDAL version    :>=2.1.2 (OGR enabled)
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
# b1=2000, b2=2005, b3=2010, b4=2015, b5=2019
# t0=2005, t1=2010, t2=2015, t3=2019
gdal_translate -mask none -b 2 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t0_src.tif
gdal_translate -mask none -b 3 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t1_src.tif
gdal_translate -mask none -b 4 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t2_src.tif
gdal_translate -mask none -b 5 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t3_src.tif

# Rasterize country border
gdal_rasterize -te $extent -tr 30 30 -tap \
	       -burn 1 -a_nodata 255 \
	       -ot Byte \
	       -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
	       ctry_PROJ.shp ctry_PROJ.tif 

# =====
# 1. Compute distance to forest edge at t2
# =====

# Message
echo "Computing distance to forest edge\n"
#
gdal_proximity.py forest_t2_src.tif _dist_edge.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO

gdal_translate -a_nodata 0 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_edge.tif dist_edge.tif

# Message
echo "Computing distance to forest edge at t3 for projections\n"
#
gdal_proximity.py forest_t3_src.tif _dist_edge_proj.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO

gdal_translate -a_nodata 0 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_edge_proj.tif dist_edge_proj.tif

# =====
# 2. Compute distance to past deforestation
# =====

# Message
echo "Computing distance to past deforestation\n"

# Create raster fcc12_src.tif
gdal_calc.py --overwrite -A forest_t1_src.tif -B forest_t2_src.tif \
             --outfile=fcc12_src.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Compute distance
gdal_proximity.py fcc12_src.tif _dist_defor_src.tif \
                  -values 0 -ot UInt32 -distunits GEO -use_input_nodata YES \
                  -nodata 4294967295

# Mask with forest_t2_src.tif
gdal_calc.py --overwrite -A _dist_defor_src.tif -B forest_t2_src.tif \
             --outfile=dist_defor.tif --type=UInt32 \
             --calc="A*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=0

# gdal_translate -a_nodata 0 \
#                -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
#                _dist_defor.tif dist_defor.tif

# Message
echo "Computing distance to past deforestation at t3 for projections\n"

# Create raster fcc23_src.tif
gdal_calc.py --overwrite -A forest_t2_src.tif -B forest_t3_src.tif \
             --outfile=fcc23_src.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Compute distance
gdal_proximity.py fcc23_src.tif _dist_defor_src.tif \
                  -values 0 -ot UInt32 -distunits GEO -use_input_nodata YES \
                  -nodata 4294967295

# Mask with forest_t3_src.tif
gdal_calc.py --overwrite -A _dist_defor_src.tif -B forest_t3_src.tif \
             --outfile=dist_defor_proj.tif --type=UInt32 \
             --calc="A*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=0

# gdal_translate -a_nodata 0 \
#                -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
#                _dist_defor.tif dist_defor.tif

# =====
# 3. Forest-cover change rasters
# =====

# Message
echo "Computing forest-cover change rasters\n"

## fcc23
# Mask fcc23 with country border
gdal_calc.py --overwrite -A fcc23_src.tif -B ctry_PROJ.tif \
             --outfile=fcc23.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==0)*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

## fcc13
# Create raster fcc13_src.tif
# Raster is directly masked with country border 
gdal_calc.py --overwrite -A forest_t1_src.tif -B forest_t3_src.tif -C ctry_PROJ.tif \
             --outfile=fcc13.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)*(C==1)-255*(A==1)*(B==0)*(C==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

# =====
# 4. Cropping forest rasters
# =====

# Message
echo "Mask forest rasters with country border\n"

# Mask forest with country border
gdal_calc.py --overwrite -A forest_t0_src.tif -B ctry_PROJ.tif \
             --outfile=forest_t0.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

gdal_calc.py --overwrite -A forest_t1_src.tif -B ctry_PROJ.tif \
             --outfile=forest_t1.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

gdal_calc.py --overwrite -A forest_t2_src.tif -B ctry_PROJ.tif \
             --outfile=forest_t2.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

gdal_calc.py --overwrite -A forest_t3_src.tif -B ctry_PROJ.tif \
             --outfile=forest_t3.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

# ===========================
# Cleaning
# ===========================

# Message
echo "Cleaning directory\n"

# Create clean data directory
mkdir -p ../data
mkdir -p ../data/forest
mkdir -p ../data/proj
# Copy files
cp -t ../data dist_edge.tif dist_defor.tif fcc23.tif
cp -t ../data/proj dist_edge_proj.tif dist_defor_proj.tif
cp -t ../data/forest forest_t0.tif forest_t1.tif forest_t2.tif forest_t3.tif fcc13.tif

# End
