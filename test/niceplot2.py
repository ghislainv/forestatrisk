from mpl_toolkits.basemap import Basemap
import osr
import gdal
import matplotlib.pyplot as plt
import numpy as np


def convertXY(xy_source, inproj, outproj):
    # function to convert coordinates

    shape = xy_source[0, :, :].shape
    size = xy_source[0, :, :].size

    # the ct object takes and returns pairs of x,y, not 2d grids
    # so the the grid needs to be reshaped (flattened) and back.
    ct = osr.CoordinateTransformation(inproj, outproj)
    xy_target = np.array(ct.TransformPoints(xy_source.reshape(2, size).T))

    xx = xy_target[:, 0].reshape(shape)
    yy = xy_target[:, 1].reshape(shape)

    return xx, yy

# ===========================
# Read the data and metadata
ds = gdal.Open("fcc_40yr.tif")
proj = ds.GetProjection()
gt = ds.GetGeoTransform()
bd = ds.GetRasterBand(1)
xres = gt[1]
yres = gt[5]
XSize = ds.RasterXSize
YSize = ds.RasterYSize
xmin = gt[0]
xmax = gt[0] + (xres * XSize)
ymax = gt[3]
ymin = gt[3] + (yres * YSize)

# Overview
ov = bd.GetOverview(2)
data = ov.ReadAsArray()
YSize_ov, XSize_ov = data.shape
xres_ov = (xmax-xmin)/XSize_ov
yres_ov = -(ymax-ymin)/YSize_ov

# get the edge coordinates and add half the
# resolution to go to center coordinates
xmin_center_ov = gt[0] + xres_ov * 0.5
xmax_center_ov = gt[0] + (xres_ov * XSize_ov) - xres_ov * 0.5
ymin_center_ov = gt[3] + (yres_ov * YSize_ov) + yres_ov * 0.5
ymax_center_ov = gt[3] - yres_ov * 0.5

# Dereference driver
ds = None

# create a grid of xy coordinates in the original projection
xy_source = np.mgrid[xmin_center_ov:xmax_center_ov+xres_ov:xres_ov,
                     ymax_center_ov+yres_ov:ymin_center_ov:yres_ov]

# Create the figure and basemap object
fig = plt.figure()
# setup mercator map projection
m = Basemap(llcrnrlon=-20., llcrnrlat=-40., urcrnrlon=60., urcrnrlat=40.,
            resolution='l', projection='merc',
            lat_0=40., lon_0=-20., lat_ts=20.)

# Create the projection objects for the convertion
inproj = osr.SpatialReference()
inproj.ImportFromWkt(proj)

# Get the target projection from the basemap object
outproj = osr.SpatialReference()
outproj.ImportFromProj4(m.proj4string)

# Convert from source projection to basemap projection
ct = osr.CoordinateTransformation(inproj, outproj)
xx, yy = convertXY(xy_source, inproj, outproj)

# plot the data (first layer)
m.pcolormesh(xx, yy, data[:, :].T)

# annotate
m.drawcountries()
m.drawcoastlines(linewidth=.5)
m.drawparallels(np.arange(-20, 40, 20), labels=[1, 1, 0, 1])
m.drawmeridians(np.arange(0, 60, 20), labels=[1, 1, 0, 1])

plt.savefig("prob_Africa.png", dpi=300)

# End
