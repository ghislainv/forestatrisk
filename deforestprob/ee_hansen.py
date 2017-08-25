#!/usr/bin/env python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Imports
import ee
import time
import os

# Initialize
ee.Initialize()


# ee_hansen.run_tasks
def run_tasks(perc, iso3, extent_latlong, scale=30, proj=None,
              gs_bucket=None):

    """Compute forest-cover change with Google EarthEngine.

    Compute the forest-cover change from Global Forest Change data
    with Python and GEE API. Export the results to Google Cloud
    Storage.

    Notes for GOOGLE EARTH ENGINE (abbreviated GEE):
    - GEE account is needed: https://earthengine.google.com.
    - GEE API Python client is needed: \
    https://developers.google.com/earth-engine/python_install.

    :param perc: Tree cover percentage threshold to define forest.
    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param extent_latlong: List/tuple of region extent in lat/long
    (xmin, ymin, xmax, ymax).
    :param scale: Resolution in meters per pixel. Default to 30.
    :param proj: The projection for the export.
    :param gs_bucket: Name of the google storage bucket to export to.

    :return: List of Google EarthEngine tasks.

    """

    # Region
    region = ee.Geometry.Rectangle(extent_latlong, proj="EPSG:4326",
                                   geodesic=False)
    region = region.buffer(10000).bounds()
    export_coord = region.getInfo()["coordinates"]

    # Hansen map
    gfc = ee.Image("UMD/hansen/global_forest_change_2015").clip(region)

    # Tree cover, loss, and gain
    treecover = gfc.select(["treecover2000"])
    lossyear = gfc.select(["lossyear"])

    # Forest in 2000
    forest2000 = treecover.gte(perc)
    forest2000 = forest2000.toByte()

    # Deforestation
    loss00_05 = lossyear.gte(1).And(lossyear.lte(5))
    loss00_10 = lossyear.gte(1).And(lossyear.lte(10))

    # Forest
    forest2005 = forest2000.where(loss00_05.eq(1), 0)
    forest2010 = forest2000.where(loss00_10.eq(1), 0)
    forest2014 = forest2000.where(lossyear.gte(1), 0)

    # Forest raster with four bands
    forest = forest2000.addBands(forest2005).addBands(
        forest2010).addBands(forest2014)
    forest = forest.select([0, 1, 2, 3], ["forest2000",
                                          "forest2005",
                                          "forest2010", "forest2014"])
    forest = forest.set("system:bandNames", ["forest2000",
                                             "forest2005",
                                             "forest2010", "forest2014"])

    # maxPixels
    maxPix = 1e10

    # Export forest to cloud storage
    # ! region must be lat/long coordinates with Python API.
    task = ee.batch.Export.image.toCloudStorage(
        image=forest,
        description="forest_" + iso3,
        bucket=gs_bucket,
        region=export_coord,
        scale=scale,
        maxPixels=maxPix,
        crs=proj,
        fileNamePrefix="input/forest_" + iso3)
    task.start()

    # Return task
    return(task)


# ee_hansen.download
def download(task, gs_bucket, path, iso3):

    """Download forest-cover data from Google Cloud Storage.

    Check that GEE tasks are completed. Download forest-cover data
    from Google Cloud Storage in the current working directory.

    Notes for GOOGLE DRIVE CLIENT:
    - gdrive software is needed: https://github.com/prasmussen/gdrive.

    :param task: Google EarthEngine task.
    :param gs_bucket: Name of the google storage bucket to download from.
    :param path: Path to download files to.
    :param iso3: Country ISO 3166-1 alpha-3 code.

    """

    # Task status
    t_status = str(task.status()[u'state'])

    # Check task status
    while (t_status != "COMPLETED"):
        # We wait 1 min
        time.sleep(60)
        # We reactualize the status
        t_status = str(task.status()[u'state'])

    # Commands to download results with gsutil
    cmd = ["gsutil cp gs://", gs_bucket,
           "/input/forest_", iso3, "*.tif ", path]
    "".join(cmd)
    os.system(cmd)

# End
