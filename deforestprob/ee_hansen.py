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


# ee_hansen
def ee_hansen(perc=50, iso3, extent, proj=None, gdrive_folder=None):

    """Compute forest-cover change with Google EarthEngine.

    Compute the forest-cover change from Global Forest Change data
    with Python and GEE API. Export the results to user's Google
    Drive. Download the data in the current working directory.
    Notes:
    1. GOOGLE EARTH ENGINE (abbreviated GEE)
    - GEE account is needed: https://earthengine.google.com.
    - GEE API Python client is needed: \
    https://developers.google.com/earth-engine/python_install.
    2. GOOGLE DRIVE CLIENT
    - gdrive software is needed: https://github.com/prasmussen/gdrive.

    :param perc: Tree cover percentage threshold to define forest.
    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param extent: List/tuple of region coordinates (xmin, ymin, xmax, ymax).
    :param proj: The projection of the region.
    :param gdrive_folder: Name of a unique folder in your Drive account \
    to export into. Defaults to the root of the drive.

    :return: The commands to download the results using gdrive.

    """

    # Region
    region = ee.Geometry.Rectangle(extent, proj, geodesic=False)

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

    # Forest-cover change 2005-2010
    fcc05_10 = forest2005.where(loss00_10.eq(1).And(forest2005.eq(1)), 2)

    # maxPixels
    maxPix = 10000000000

    # Export fcc05_10 to drive
    task0 = ee.batch.Export.image.toDrive(
        image=fcc05_10,
        description='export_fcc',
        region=region.getInfo()['coordinates'],
        scale=30,
        maxPixels=maxPix,
        crs=proj,
        folder=gdrive_folder,
        fileNamePrefix='fcc05_10_' + iso3)
    task0.start()
    t0_status = str(task0.status()[u'state'])

    # Export loss00_05 to drive
    task1 = ee.batch.Export.image.toDrive(
        image=loss00_05,
        description='export_loss',
        region=region.getInfo()['coordinates'],
        scale=30,
        maxPixels=maxPix,
        crs=proj,
        folder=gdrive_folder,
        fileNamePrefix='loss00_05_' + iso3)
    task1.start()
    t1_status = str(task1.status()[u'state'])

    # Export forest2014 to drive
    task2 = ee.batch.Export.image.toDrive(
        image=forest2014,
        description='export_forest',
        region=region.getInfo()['coordinates'],
        scale=30,
        maxPixels=maxPix,
        crs=proj,
        folder=gdrive_folder,
        fileNamePrefix='forest2014_' + iso3)
    task2.start()
    t2_status = str(task2.status()[u'state'])

    # Check tasks status
    while ((t0_status != "COMPLETED") or
           (t1_status != "COMPLETED") or
           (t2_status != "COMPLETED")):
        # We wait 1 min
        time.sleep(60)
        # We reactualize the status
        t0_status = str(task0.status()[u'state'])
        t1_status = str(task1.status()[u'state'])
        t2_status = str(task2.status()[u'state'])

    # Commands to download results with gdrive
    # cmd0
    cmd0_query = "\"trashed = false and name contains 'fcc05_10_" + iso3 + "'\""
    cmd0_args = ["gdrive", "download", "query", "-f", "--recursive",
                 cmd0_query]
    cmd0 = " ".join(cmd0_args)
    # cmd1
    cmd1_query = "\"trashed = false and name contains 'loss00_05_" + iso3 + "'\""
    cmd1_args = ["gdrive", "download", "query", "-f", "--recursive",
             cmd1_query]
    cmd1 = " ".join(cmd1_args)
    # cmd2
    cmd2_query = "\"trashed = false and name contains 'forest2014_" + iso3 + "'\""
    cmd2_args = ["gdrive", "download", "query", "-f", "--recursive",
                 cmd2_query]
    cmd2 = " ".join(cmd2_args)

    # Download the results with gdrive
    os.system(cmd0)
    os.system(cmd1)
    os.system(cmd2)

    # Return the commands
    return({'cmd0': cmd0, 'cmd1': cmd1, 'cmd2': cmd2})

# End
