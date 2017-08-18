#!/usr/bin/python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

import os
import deforestprob as dfp
import pandas as pd
import pkg_resources

# List of countries to process
countries = ["Senegal", "Gambia (Islamic Republic of the)", "Guinea Bissau",
             "Guinea", "Sierra Leone", "Liberia", "Côte D'Ivoire", "Ghana",
             "Togo", "Benin", "Nigeria", "Cameroon",
             "Central African Republic", "Equatorial Guinea", "Gabon", "Congo",
             "Democratic Republic of the Congo", "Uganda", "Kenya",
             "United Republic of Tanzania", "Rwanda", "Burundi", "Madagascar",
             "Mozambique"]

# Number of countries
nctry = len(countries)

# Data-frame of country codes
file_countrycode = pkg_resources.resource_filename("deforestprob",
                                                   "data/countrycode.csv")
data_countrycode = pd.read_csv(file_countrycode, sep=";", header=0)

# Get iso3c from country name
iso3 = list()
for i in range(nctry):
    code = data_countrycode.iso3c[data_countrycode[
        "country.name.en"] == countries[i]]
    iso3.append(code.iloc[0])

# Only two countries for test
iso3 = ["CIV", "GHA"]
nctry = len(iso3)

# Projection for Africa (World Mercator)
proj_africa = "EPSG:3395"

# Original working directory
owd = os.getcwd()

# Loop on countries
for i in range(nctry):
    
    i = 1
    
    # Make new directory for country
    dfp.make_dir(iso3[i])
    os.chdir(iso3[i])
    
    # Data
    dfp.data.country(iso3=iso3[i], monthyear="Aug2017", proj=proj_africa)

    # Computation
    dfp.computation()
    
    # Return to original working directory
    os.chdir(owd)

# Combine results

# For spatial probability
os.system("find -type f -name *pred_binomial_iCAR.tif > list_pred.txt")
os.system("gdalbuildvrt -input_file_list list_pred.txt pred.vrt")
os.system("gdal_merge.py -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
-o pred.tif pred.vrt")

# For forest cover in 2050 
os.system("find -type f -name *forest_cover_2050.tif > list_fc2050.txt")
os.system("gdalbuildvrt -input_file_list list_fc2050.txt fc2050.vrt")
os.system("gdal_merge -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
-o fc2050.tif fc2050.vrt")

# Upload results to Google Drive with gdrive
os.system("gdrive list --query 'name=\"deforestprob\"' > id_deforestprob.txt")
dat = pd.read_table("id_deforestprob.txt", sep="\t", index_col=False)
dat
os.system("gdrive upload --parent " + id + " --share pred.tif")
os.system("gdrive upload --parent " + id + " --share fc2050.tif")

# End
