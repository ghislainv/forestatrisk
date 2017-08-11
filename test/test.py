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
iso3 = ["CIV", "COD"]

# Projection for Africa (World Mercator)
proj_africa = "EPSG:3395"

# Loop on countries
for i in range(nctry):
    
    i = 0
    
    # Make new directory for country
    dfp.make_dir(iso3[i])
    os.chdir(iso3[i])
    
    # 
    dfp.data.country(iso3=iso3[i], monthyear="Aug2017", proj=proj_africa)
    
    # Get out of directory
    os.chdir("../")

# End
