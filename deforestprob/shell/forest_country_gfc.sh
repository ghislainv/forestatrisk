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

# =====
# 0. Mosaicing
# =====

# Message
echo "Mosaicing and reprojecting\n"
#
gdalbuildvrt fcc05_10_gfc.vrt fcc05_10_*.tif
gdal_translate -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         fcc05_10_gfc.vrt fcc05_10_gfc.tif

gdalbuildvrt loss00_05_gfc.vrt loss00_05_*.tif
gdal_translate -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         loss00_05_gfc.vrt loss00_05_gfc.tif

gdalbuildvrt forest2014.vrt forest2014_*.tif
gdal_translate -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
         forest2014.vrt forest2014.tif

# =====
# 1. Compute distance to forest edge in 2005
# =====

# Message
echo "Distance to forest edge\n"
#
gdal_proximity.py fcc05_10_gfc.tif _dist_edge.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO
gdal_translate -a_nodata 0 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_edge.tif dist_edge.tif

# =====
# 2. Compute distance to past deforestation (loss00_05)
# =====

# Message
echo "Distance to past deforestation\n"

# Set nodata different from 255
gdal_translate -a_nodata 99 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               fcc05_10_gfc.tif _fcc05_10.tif
gdal_translate -a_nodata 99 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               loss00_05_gfc.tif _loss00_05.tif

# Create raster _fcc00_05.tif with 1:for2005, 0:loss00_05
gdal_calc.py --overwrite -A _fcc05_10.tif -B _loss00_05.tif \
             --outfile=_fcc00_05.tif --type=Byte \
             --calc="255-254*(A>=1)*(B==0)-255*(A==0)*(B==1)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Mask with country border (-co does not work with cutline !)
gdalwarp -overwrite -srcnodata 255 -dstnodata 255 \
         -cutline ctry_proj.shp \
         _fcc00_05.tif fcc00_05_mask.tif
gdal_translate -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               fcc00_05_mask.tif fcc00_05.tif

# Compute distance (with option -use_input_nodata YES, it is much more efficient)
gdal_proximity.py fcc00_05.tif _dist_defor.tif \
                  -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
                  -values 0 -ot UInt32 -distunits GEO -use_input_nodata YES
gdal_translate -a_nodata 65535 \
               -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               _dist_defor.tif dist_defor.tif

# =====
# 3. Forest raster
# =====

# Create raster fcc05_10.tif with 1:for2010, 0:loss05_10
gdal_calc.py --overwrite -A _fcc05_10.tif \
             --outfile=fcc05_10_reclass.tif --type=Byte \
             --calc="255-254*(A==1)-255*(A==2)" \
             --co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" \
             --NoDataValue=255

# Mask with country border (-co does not work with cutline !)
gdalwarp -overwrite -srcnodata 255 -dstnodata 255 \
         -cutline ctry_proj.shp \
          fcc05_10_reclass.tif fcc05_10_mask.tif
gdal_translate -co "COMPRESS=LZW" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
               fcc05_10_mask.tif fcc05_10.tif

# ===========================
# Cleaning
# ===========================

# Message
echo "Cleaning directory\n"

# Create clean data directory
mkdir -p ../data
# Copy files
cp -t ../data dist_defor.tif dist_edge.tif fcc05_10.tif
# Remove raw data directory
cd ../
# rm -R data_raw


# End
