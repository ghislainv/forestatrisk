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
import psutil
import multiprocessing as mp

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

# Number of cpu
total_cpu = psutil.cpu_count()
num_cpu = int(total_cpu * 0.75) if total_cpu > 2 else 1


# Function for multiprocessing
def compute(iso3):

    # Make new directory for country
    os.chdir(owd)
    dfp.make_dir(iso3)
    os.chdir(os.path.join(owd, iso3))

    # Data
    dfp.data.country(iso3=iso3, monthyear="Aug2017", proj=proj_africa)

    # Computation
    dfp.computation()

    # Return country iso code
    return(iso3)

# Parallel computation
pool = mp.Pool(processes=num_cpu)
results = [pool.apply_async(compute, args=(x,)) for x in iso3]
pool.close()
pool.join()
output = [p.get() for p in results]
print(output)

# Combine results

# For spatial probability
os.system("find -type f -name *pred_binomial_iCAR.tif > list_pred.txt")
os.system("gdalbuildvrt -input_file_list list_pred.txt pred.vrt")
os.system("gdal_translate -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
pred.vrt pred.tif")

# For forest cover in 2050
os.system("find -type f -name *fcc_40yr.tif > list_fcc_40yr.txt")
os.system("gdalbuildvrt -input_file_list list_fcc_40yr.txt fcc_40yr.vrt")
os.system("gdal_translate -co 'COMPRESS=LZW' -co 'PREDICTOR=2' -co 'BIGTIFF=YES' \
fcc_40yr.vrt fcc_40yr.tif")

# Upload results to Google Cloud Storage with gsutil
os.system("gsutil -o GSUtil:parallel_composite_upload_threshold=150M \
cp fcc_40yr.tif gs://deforestprob/output/fcc_40yr.tif")
os.system("gsutil -o GSUtil:parallel_composite_upload_threshold=150M \
cp pred.tif gs://deforestprob/output/pred.tif")

# End
