#!/usr/bin/env python
# -*- coding: utf-8 -*-

# =============================================================================
#
# download.py
#
# Download and unzip rasters in a new directory
#
# Ghislain Vieilledent <ghislain.vieilledent@cirad.fr>
# December 14th 2015
#
# ============================================================================

# =============================================
# Libraries
# =============================================

from __future__ import division, print_function  # Python 3 compatibility
import os
from zipfile import ZipFile  # To unzip files
from urllib import urlretrieve  # To download files from internet

# =============================================
# Download rasters
# =============================================

# Create a new directory to hold the data
destDir = "./data"
if not os.path.exists(destDir):
    os.mkdir(destDir)

# Download the zip file
print("Download data")
fname = "./data/deforpy_data.zip"
url = "http://bioscenemada.cirad.fr/githubdata/deforpy/deforpy_data.zip"
resp = urlretrieve(url, fname)
print("Data downloaded")

# Extract files from zip
print("Extract files from zip")
f = ZipFile(fname)
f.extractall(destDir)
f.close()
print("Files extracted")

# ============================================================================
# End of download.py
# ============================================================================
