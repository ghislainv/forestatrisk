#!/usr/bin/env python
# -*- coding: utf-8 -*-

# =============================================================================
#
# rfmodel.py
#
# Use the Random Forest algorithm to compute the spatial
# probability of deforestation
#
# Ghislain Vieilledent <ghislain.vieilledent@cirad.fr>
# December 15th 2015
#
# ============================================================================

# =============================================
# Libraries
# =============================================

from __future__ import division, print_function  # Python 3 compatibility
from sklearn.ensemble import RandomForestClassifier
import cPickle as pickle  # To save objects
import numpy as np
import os
import sys
from tqdm import tqdm  # Progress bar
from osgeo import gdal
import psutil  # CPU count
from block import makeblock

# =============================================
# Functions
# =============================================


# Function to save an object in a file
def save_object(obj, filename):
    with open(filename, "wb") as output:
        pickle.dump(obj, output, -1)


# Function to make a directory
def make_dir(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)


# Function to rescale from 1-1000000 to 1-65535 (UInt16)
def rescale(value):
    return(((value - 1) * 65534 / 999999) + 1)

# =============================================
# Import and format data
# =============================================

print("Import training data-set")

# Data-set
dataset = np.genfromtxt("data/sample.txt",
                        delimiter=",", missing_values="nan",
                        names=True, dtype="f8")

# Explicative variables (train)
train = dataset[["sapm", "dist_road", "dist_town", "dist_edge",
                 "dist_patch", "altitude", "X", "Y"]]
# Transform structured numpy array into 2D array
varnames = train.dtype.names
train = train.view((np.float64, len(varnames)))
# Remove lines with NA
w = ~np.isnan(train).any(axis=1)
train = train[w]

# Response variable (target)
target = dataset["defor"]
target[np.isnan(target)] = 0
target = target[w]

# =============================================
# Run Random Forest
# =============================================

# Create and train Random Forest
# For Multi-core CPUs, use n_jobs argument
njobs = max(1, psutil.cpu_count() - 2)
rf = RandomForestClassifier(n_estimators=500, n_jobs=njobs)
print ("Run Random Forest on " + str(njobs) + " CPU")
rf.fit(train, target)

# Variable importance
importances = rf.feature_importances_
std = np.std([tree.feature_importances_ for tree in rf.estimators_],
             axis=0)
indices = np.argsort(importances)[::-1]

# Print the feature ranking
print("Feature rank:")
for v in range(len(varnames)):
    sentence = "%d. " + varnames[indices[v]] + " (%f)"
    print(sentence % (v + 1, importances[indices[v]]))

# Predict on taining data-set
print("Predict on the new data-set")
test = train
pred = rf.predict_proba(test)[:, 1]

# Save results
print("Save model and output")
make_dir("output")  # make output directory
save_object(rf, "output/rfmodel.pkl")
np.savetxt("output/predict.txt", pred, delimiter=",", fmt="%f")
print("Done")

# =============================================
# Predictions on the whole data-set
# =============================================

# Mask on forest
fmaskR = gdal.Open("data/dist_edge.tif")
fmaskB = fmaskR.GetRasterBand(1)
fmaskND = fmaskB.GetNoDataValue()
if fmaskND is None:
    print("NoData value is not specified for forest raster file")
    sys.exit(1)

# Make vrt with gdalbuildvrt
print("Make virtual raster with variables as raster bands")
inputvar = "data/sapm.tif data/dist_road.tif data/dist_town.tif \
data/dist_edge.tif data/dist_patch.tif data/altitude.tif"
outputfile = "data/var.vrt"
os.system("gdalbuildvrt -separate -o " + outputfile + " " + inputvar)

# Load vrt file
stack = gdal.Open("data/var.vrt")
ncol = stack.RasterXSize
nrow = stack.RasterYSize
nband = stack.RasterCount
gt = stack.GetGeoTransform()
Xmin = gt[0]
Xmax = gt[0] + gt[1] * ncol
proj = stack.GetProjection()

# List of nodata values
bandND = np.zeros(nband)
for k in range(nband):
    band = stack.GetRasterBand(k + 1)
    if band is None:
        print("NoData value is not specified for input raster file %d" % k)
        sys.exit(1)
    bandND[k] = band.GetNoDataValue()
bandND = bandND.astype(np.float32)

# Make blocks
blockinfo = makeblock("data/var.vrt", byrows=True, nrows=128)
nblock = blockinfo[0]
nblock_x = blockinfo[1]
nblock_y = blockinfo[2]
x = blockinfo[3]
y = blockinfo[4]
nx = blockinfo[5]
ny = blockinfo[6]
print("Divide region in " + str(nblock) + " blocks")

# Rasters of predictions
print("Create a raster file on disk for projections")
driver = gdal.GetDriverByName("GTiff")
Pdrv = driver.Create("output/proba.tif", ncol, nrow, 1, gdal.GDT_UInt16,
                     ["COMPRESS=LZW", "PREDICTOR=2"])
Pdrv.SetGeoTransform(gt)
Pdrv.SetProjection(proj)
Pband = Pdrv.GetRasterBand(1)
Pband.SetNoDataValue(0)

# Predict by block
# Message
print("Predict deforestation probability by block")
# Loop on blocks of data
for b in tqdm(range(nblock)):
    # Position in 1D-arrays
    px = b % nblock_x
    py = b // nblock_x
    # Number of pixels
    npix = nx[px] * ny[py]
    # Data for one block of the stack (shape = (nband,nrow,ncol))
    data = stack.ReadAsArray(x[px], y[py], nx[px], ny[py])
    # Replace ND values with nan
    for i in range(nband):
        data[i][np.nonzero(data[i] == bandND[i])] = -9999
    # Forest mask
    fmaskA = fmaskB.ReadAsArray(x[px], y[py], nx[px], ny[py])
    fmaskA = fmaskA.astype(np.float32)  # From uint to float
    fmaskA[np.nonzero(fmaskA == fmaskND)] = -9999
    fmaskA = fmaskA[np.newaxis, :, :]
    # X an Y coordinates
    X = np.arange(gt[0], gt[0] + nx[px] * gt[1], gt[1]) + 0.5 * gt[1]
    X = np.repeat(X[np.newaxis, :], ny[py], axis=0)
    X = X[np.newaxis, :, :]
    Y = np.arange(gt[3], gt[3] + ny[py] * gt[5], gt[5]) + 0.5 * gt[5]
    Y = np.repeat(Y[:, np.newaxis], nx[px], axis=1)
    Y = Y[np.newaxis, :, :]
    # Concatenate forest mask and coordinates with stack
    data = np.concatenate((data, X, Y, fmaskA), axis=0)
    del X, Y, fmaskA
    # Transpose and reshape to 2D array
    data = data.transpose(1, 2, 0)
    data = data.reshape(npix, nband + 3)
    # Observations without NA
    w = np.nonzero(~(data == -9999).any(axis=1))
    # Remove observations with NA for Random Forest
    data = data[w]
    data = data[:, :-1]
    # Predict with Random Forest model
    pred = np.zeros(npix)  # Initialize with nodata value (0)
    if len(w[0]) > 0:
        # Get predictions into an array
        rfp = np.array(rf.predict_proba(data)[:, 1])
        # Avoid nodata value (0) for low proba
        rfp[rfp < 1e-06] = 1e-06
        # np.rint: round to nearest integer
        rfp = np.rint(1000000 * rfp)
        # Rescale and return to pred
        pred[w] = rescale(rfp)
    pred = pred.reshape(ny[py], nx[px])
    # Assign prediction to raster row
    Pband.WriteArray(pred, x[px], y[py])

# Compute statistics after setting NoData
print("Compute statistics")
Pband.FlushCache()  # Write cache data to disk
Pband.ComputeStatistics(False)

# Set color table  # Not working
# print "Set color table"
# ct = gdal.ColorTable()
# ct.SetColorEntry(0, (0, 0, 0, 0))
# ct.CreateColorRamp(1, (34, 139, 34, 255), 18152, (255, 165, 0, 255))
# ct.CreateColorRamp(18152, (255, 165, 0, 255), 30071, (255, 0, 0, 255))
# ct.CreateColorRamp(30071, (255, 0, 0, 255), 65535, (0, 0, 0, 255))
# Pband.SetRasterColorTable(ct)

# Dereference objects
ct = None
Pband = None

# Build overviews, save, and close  # Not really necessary, increase file size
print("Build overview, save, and close")
# Pdrv.BuildOverviews("average", [2, 4, 8, 16, 32])
del Pdrv  # Dereference: write the data modifications and close

# Set color table a posteriori
# print "Set color table a posteriori"
# os.system("gdal_translate output/proba.vrt output/proba2010.tif")

# ============================================================================
# End of rfmodel.py
# ============================================================================
