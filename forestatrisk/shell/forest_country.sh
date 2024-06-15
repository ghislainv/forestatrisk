#!/usr/bin/bash

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# GDAL version    :>=2.1.2 (OGR enabled)
# license         :GPLv3
# ==============================================================================

# Variables
iso=$1
proj=$2
extent=$3
temp_dir=$4
output_dir=$5

# Working directory
cd $temp_dir

# ===========================
# Forest
# ===========================

# Message
echo "Forest data obtained with Google Earth Engine\n"

# =====
# 0. Mosaicing
# =====

# Message
echo "Mosaicing and reprojecting\n"
# Mosaicing
gdalbuildvrt forest.vrt forest_$iso*.tif
# Reprojecting
gdalwarp -overwrite -te $extent -tap -t_srs "$proj" \
         -tr 30 30 -r near \
         -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         forest.vrt forest_src.tif

# Separate bands
# b1=2000, b2=2005, b3=2010, b4=2015, b5=2020
# t1=2000, t2=2010, t3=2020
#gdal_translate -mask none -b 2 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
#               forest_src.tif forest_t0_src.tif
gdal_translate -mask none -b 1 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t1_src.tif
gdal_translate -mask none -b 3 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t2_src.tif
gdal_translate -mask none -b 5 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_t3_src.tif

# Additional dates: 2005 and 2015
gdal_translate -mask none -b 2 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_2005_src.tif
gdal_translate -mask none -b 4 -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               forest_src.tif forest_2015_src.tif

# Rasterize country border (by default: zero outside, without nodata value)
gdal_rasterize -te $extent -tr 30 30 -tap \
	       -burn 1 \
	       -ot Byte \
	       -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
	       aoi_proj.shp aoi_proj.tif

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
echo "Computing distance to forest edge at t3 for forecasting\n"
#
gdal_proximity.py forest_t3_src.tif _dist_edge.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO

gdal_translate -a_nodata 0 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_edge.tif dist_edge_forecast.tif

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
             --NoDataValue=255 --quiet

# Compute distance
gdal_proximity.py fcc12_src.tif _dist_defor_src.tif \
		  -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
                  -values 0 -ot UInt32 -distunits GEO -use_input_nodata YES \
                  -nodata 0

gdal_translate -a_nodata 0 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_defor_src.tif dist_defor.tif

# Message
echo "Computing distance to past deforestation at t3 for forecasting\n"

# Create raster fcc23_src.tif
gdal_calc.py --overwrite -A forest_t2_src.tif -B forest_t3_src.tif \
             --outfile=fcc23_src.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

# Compute distance
gdal_proximity.py fcc23_src.tif _dist_defor_src.tif \
		  -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
                  -values 0 -ot UInt32 -distunits GEO -use_input_nodata YES \
                  -nodata 0

gdal_translate -a_nodata 0 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_defor_src.tif dist_defor_forecast.tif

# =====
# 3. Cropping forest rasters
# =====

# Message
echo "Mask forest rasters with country border\n"

# Mask forest with country border
gdal_calc.py --overwrite -A forest_t1_src.tif -B aoi_proj.tif \
             --outfile=forest_t1.tif --type=Byte \
             --calc="A*B" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --quiet

gdal_calc.py --overwrite -A forest_t2_src.tif -B aoi_proj.tif \
             --outfile=forest_t2.tif --type=Byte \
             --calc="A*B" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --quiet

gdal_calc.py --overwrite -A forest_t3_src.tif -B aoi_proj.tif \
             --outfile=forest_t3.tif --type=Byte \
             --calc="A*B" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --quiet

gdal_calc.py --overwrite -A forest_2005_src.tif -B aoi_proj.tif \
             --outfile=forest_2005.tif --type=Byte \
             --calc="A*B" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --quiet

gdal_calc.py --overwrite -A forest_2015_src.tif -B aoi_proj.tif \
             --outfile=forest_2015.tif --type=Byte \
             --calc="A*B" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --quiet

# =====
# 4. Forest-cover change rasters
# =====

# Message
echo "Computing forest-cover change rasters\n"

## fcc23
# Mask fcc23 with country border
gdal_calc.py --overwrite -A fcc23_src.tif -B aoi_proj.tif \
             --outfile=fcc23.tif --type=Byte \
             --calc="255-254*(A==1)*(B==1)-255*(A==0)*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255 --quiet

## fcc123
# Create raster fcc123.tif (0: nodata, 1: for2000, 2: for2010, 3: for2020)
gdal_calc.py --overwrite -A forest_t1.tif -B forest_t2.tif -C forest_t3.tif \
             --outfile=fcc123.tif --type=Byte \
             --calc="A+B+C" \
	     --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
	     --NoDataValue=0 --quiet

## fcc12345
# Create raster fcc12345.tif (0: nodata, 1: for2000, 2: for2005, 3: for2010, 4: for2015, 5: for2020)
gdal_calc.py --overwrite -A forest_t1.tif -B forest_2005.tif -C forest_t2.tif -D forest_2015.tif -E forest_t3.tif \
             --outfile=fcc12345.tif --type=Byte \
	     --calc="A+B+C+D+E" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=0 --quiet

# ===========================
# Cleaning
# ===========================

# Message
echo "Cleaning directory\n"

# Create clean data directory
mkdir -p ../$output_dir
mkdir -p ../$output_dir/forest
mkdir -p ../$output_dir/forecast
# Copy files
cp -t ../$output_dir dist_edge.tif dist_defor.tif fcc23.tif
cp -t ../$output_dir/forecast dist_edge_forecast.tif dist_defor_forecast.tif
cp -t ../$output_dir/forest forest_t1.tif forest_t2.tif forest_t3.tif forest_2005.tif forest_2015.tif fcc123.tif fcc12345.tif 
# Return to working director
cd ../

# End
