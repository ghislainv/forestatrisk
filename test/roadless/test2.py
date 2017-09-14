#!/usr/bin/python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# PRIOR TO EXECUTING THE FOLLOWING SCRIPT, AUTHENTICATE TO
# 1. Google Earth Engine: earthengine authenticate
# 2. Google Cloud Storage: gcloud auth application-default login

import os
import deforestprob as dfp
import pandas as pd
import pkg_resources
import psutil
import multiprocessing as mp
# from computation2 import computation
import matplotlib.pyplot as plt

# List of countries to process
countries = ["Senegal", "Gambia (Islamic Republic of the)", "Guinea Bissau",
             "Guinea", "Sierra Leone", "Liberia", "Côte D'Ivoire", "Ghana",
             "Togo", "Benin", "Nigeria", "Cameroon",
             "Central African Republic", "Equatorial Guinea", "Gabon", "Congo",
             "Democratic Republic of the Congo", "Uganda", "Kenya",
             "United Republic of Tanzania", "Rwanda", "Burundi", "Madagascar",
             "Mozambique", "Angola", "Zambia", "Malawi", "South Sudan",
             "Ethiopia"]

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
iso3.sort()

# Only some countries
# iso3 = ["MOZ", "MWI", "NGA", "RWA", "SEN", "SLE", "SSD", "TGO", "TZA"]
# nctry = len(iso3)

# Projection for Africa (World Mercator)
proj_africa = "EPSG:3395"

# Original working directory
owd = os.getcwd()

# Number of cpu
total_cpu = psutil.cpu_count()
num_cpu = int(total_cpu * 0.75) if total_cpu > 2 else 1
num_cpu = 3


# Function for multiprocessing
def compute(iso3):

    # Make new directory for country
    os.chdir(owd)
    dfp.make_dir(iso3)
    os.chdir(os.path.join(owd, iso3))

    # Data
    # dfp.data.country(iso3=iso3, monthyear="Sep2017",
    #                  proj=proj_africa,
    #                  data_country=False,
    #                  fcc_source="roadless",
    #                  gs_bucket="deforestprob")

    # Computation
    # computation(fcc_source="roadless")

    # Plot
    # Forest in 2015
    fig_forest = dfp.plot.forest("data/forest/forest_t3.tif",
                                 borders="data/ctry_PROJ.shp",
                                 output_file="output_2005_2015/forest_t3.png")
    plt.close(fig_forest)

    # Forest-cover change 2005-2010
    fig_fcc = dfp.plot.fcc("data/fcc12.tif",
                           borders="data/ctry_PROJ.shp",
                           output_file="output_2005_2015/fcc12.png")
    plt.close(fig_fcc)

    # Original spatial random effects
    fig_rho_orig = dfp.plot.rho("output_2005_2015/rho_orig.tif",
                                borders="data/ctry_PROJ.shp",
                                output_file="output_2005_2015/rho_orig.png")
    plt.close(fig_rho_orig)

    # Interpolated spatial random effects
    fig_rho = dfp.plot.rho("output_2005_2015/rho.tif",
                           borders="data/ctry_PROJ.shp",
                           output_file="output_2005_2015/rho.png")
    plt.close(fig_rho)

    # Spatial probability of deforestation
    fig_prob = dfp.plot.prob("output_2005_2015/prob.tif",
                             borders="data/ctry_PROJ.shp",
                             output_file="output_2005_2015/prob.png")
    plt.close(fig_prob)

    # Forest-cover change 2010-2050
    fig_fcc_35yr = dfp.plot.fcc("output_2005_2015/fcc_35yr.tif",
                                borders="data/ctry_PROJ.shp",
                                output_file="output_2005_2015/fcc_35yr.png")
    plt.close(fig_fcc_35yr)

    # Return country iso code
    return(iso3)

# For loop
for i in iso3:
    compute(i)

# Parallel computation
pool = mp.Pool(processes=num_cpu)
results = [pool.apply_async(compute, args=(x,)) for x in iso3]
pool.close()
pool.join()
output = [p.get() for p in results]
print(output)

# Combine results

# Combine country borders
os.system("find . -type f -name *ctry_PROJ.shp \
-exec ogr2ogr -update -append borders.shp {} \;")

# Spatial probability
os.system("find . -type f -name *prob.tif > list_find_prob.txt")
os.system(
    "grep 'output_2005_2015/prob.tif' list_find_prob.txt > list_prob.txt")
os.system("gdalbuildvrt -input_file_list list_prob.txt prob.vrt")
os.system("gdal_translate -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
prob.vrt prob.tif")
# Build overview
os.system("gdaladdo -ro -r nearest prob.tif 16")
# Plot
dfp.plot.prob("prob.tif", output_file="prob.png",
              borders="borders.shp", zoom=None, dpi=300,
              lw=0.5, c="grey")

# Forest cover in 2050
os.system(
    "find . -type f -name *fcc_35yr.tif > list_fcc_35yr.txt")
os.system("gdalbuildvrt -input_file_list list_fcc_35yr.txt fcc_35yr.vrt")
os.system("gdal_translate -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
fcc_35yr.vrt fcc_35yr.tif")
# Build overview
os.system("gdaladdo -ro -r nearest --config COMPRESS_OVERVIEW LZW \
--config PREDICTOR_OVERVIEW 2 \
--config BIGTIFF_OVERVIEW YES \
fcc_35yr.tif 16")
# Plot
dfp.plot.fcc("fcc_35yr.tif", output_file="fcc_35yr.png",
             borders="borders.shp", zoom=None, dpi=300,
             lw=0.5, c="grey")

# Upload results to Google Cloud Storage with gsutil
# os.system("gsutil -o GSUtil:parallel_composite_upload_threshold=150M \
# cp fcc_35yr.tif gs://deforestprob/output_roadless/fcc_35yr.tif")
# os.system("gsutil cp fcc_35yr.png \
# gs://deforestprob/output_roadless/fcc_35yr.png")
# os.system("gsutil -o GSUtil:parallel_composite_upload_threshold=150M \
# cp prob.tif gs://deforestprob/output_roadless/prob.tif")
# os.system("gsutil cp prob.png gs://deforestprob/output_roadless/prob.png")

# End
