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
def run_tasks(perc, iso3, extent, scale=30, proj=None, gdrive_folder=None):

    """Compute forest-cover change with Google EarthEngine.

    Compute the forest-cover change from Global Forest Change data
    with Python and GEE API. Export the results to user's Google
    Drive.

    Notes for GOOGLE EARTH ENGINE (abbreviated GEE):
    - GEE account is needed: https://earthengine.google.com.
    - GEE API Python client is needed: \
    https://developers.google.com/earth-engine/python_install.

    :param perc: Tree cover percentage threshold to define forest.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    :param extent: List/tuple of region coordinates (xmin, ymin, xmax, ymax).

    :param scale: Resolution in meters per pixel. Default to 30.

    :param proj: The projection of the region.

    :param gdrive_folder: Name of a unique folder in your Drive
    account to export into. Defaults to the root of the drive.

    :return: List of Google EarthEngine tasks.

    """

    # Region
    region = ee.Geometry.Rectangle(extent, proj, geodesic=False)
    region = region.buffer(10000)

    # Hansen map
    gfc = ee.Image('UMD/hansen/global_forest_change_2015').clip(region)

    # Tree cover, loss, and gain
    treecover = gfc.select(['treecover2000'])
    lossyear = gfc.select(['lossyear'])

    # Forest in 2000
    forest2000 = treecover.gte(perc)

    # Deforestation
    loss00_05 = lossyear.gte(1).And(lossyear.lte(5))
    loss00_10 = lossyear.gte(1).And(lossyear.lte(10))

    # Forest
    forest2005 = forest2000.where(loss00_05.eq(1), 0)
    forest2010 = forest2000.where(loss00_10.eq(1), 0)
    forest2014 = forest2000.where(lossyear.gte(1), 0)

    # maxPixels
    maxPix = 10000000000

    # Export forest2000 to drive
    task0 = ee.batch.Export.image.toDrive(
        image=forest2000,
        description='export_forest2000',
        region=region.getInfo()['coordinates'],
        scale=scale,
        maxPixels=maxPix,
        crs=proj,
        folder=gdrive_folder,
        fileNamePrefix='forest2000_' + iso3)
    task0.start()

    # Export forest2005 to drive
    task1 = ee.batch.Export.image.toDrive(
        image=forest2005,
        description='export_forest2005',
        region=region.getInfo()['coordinates'],
        scale=scale,
        maxPixels=maxPix,
        crs=proj,
        folder=gdrive_folder,
        fileNamePrefix='forest2005_' + iso3)
    task1.start()

    # Export forest2010 to drive
    task2 = ee.batch.Export.image.toDrive(
        image=forest2010,
        description='export_forest2010',
        region=region.getInfo()['coordinates'],
        scale=scale,
        maxPixels=maxPix,
        crs=proj,
        folder=gdrive_folder,
        fileNamePrefix='forest2010_' + iso3)
    task2.start()

    # Export forest2014 to drive
    task3 = ee.batch.Export.image.toDrive(
        image=forest2014,
        description='export_forest2014',
        region=region.getInfo()['coordinates'],
        scale=scale,
        maxPixels=maxPix,
        crs=proj,
        folder=gdrive_folder,
        fileNamePrefix='forest2014_' + iso3)
    task3.start()

    # Return list of tasks
    return([task0, task1, task2, task3])


# ee_hansen.download
def download(tasks, path, iso3):

    """Download forest-cover change data from Google Drive after.

    Check that GEE tasks are completed. Download forest-cover change
    data from Google Drive in the current working directory.

    Notes for GOOGLE DRIVE CLIENT:
    - gdrive software is needed: https://github.com/prasmussen/gdrive.

    :param tasks: List of Google EarthEngine tasks.

    :param path: Download path.

    :param iso3: Country ISO 3166-1 alpha-3 code.

    """

    # Tasks
    task0 = tasks[0]
    task1 = tasks[1]
    task2 = tasks[2]
    task3 = tasks[3]

    # Task status
    t0_status = str(task0.status()[u'state'])
    t1_status = str(task1.status()[u'state'])
    t2_status = str(task2.status()[u'state'])
    t3_status = str(task3.status()[u'state'])

    # Check task status
    while ((t0_status != "COMPLETED") or
           (t1_status != "COMPLETED") or
           (t2_status != "COMPLETED") or
           (t3_status != "COMPLETED")):
        # We wait 1 min
        time.sleep(60)
        # We reactualize the status
        t0_status = str(task0.status()[u'state'])
        t1_status = str(task1.status()[u'state'])
        t2_status = str(task2.status()[u'state'])
        t3_status = str(task3.status()[u'state'])

    # Commands to download results with gdrive
    files = ["forest2000_", "forest2005_", "forest2010_", "forest2014_"]
    for f in files:
        query = "\"trashed = false and name contains '" + f + iso3 + "'\""
        args = ["gdrive", "download", "query", "-f", "--path", path, query]
        cmd = " ".join(args)
        # Download the results with gdrive
        os.system(cmd)

# End
