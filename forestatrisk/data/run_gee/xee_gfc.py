"""Using GEE to get forest cover change from GFC."""

# Standard library imports
from __future__ import division, print_function  # Python 3 compatibility
import os
import subprocess
import time

# Third party imports
import ee
import xarray as xr
import pandas as pd
import numpy as np
from dask.distributed import Client, LocalCluster, Lock

# ee_gfc.run_task
def run_task(perc, iso3, extent_latlong, scale=30, proj=None):
    """Compute forest-cover change with Google EarthEngine.

    Compute the forest-cover change from Global Forest Change (GFC)
    Hansen et al. data with Python and GEE API and XEE backend.

    Notes for Google Earth Engine (abbreviated GEE):

    * GEE account is needed: `<https://earthengine.google.com>`_\\ .
    * GEE API Python client is needed: \
    `<https://developers.google.com/earth-engine/python_install>`_\\ .

    :param perc: Tree cover percentage threshold to define forest.
    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param extent_latlong: List/tuple of region extent in lat/long
        (xmin, ymin, xmax, ymax).
    :param scale: Resolution in meters per pixel. Default to 30.
    :param proj: The projection for the export.

    """
    # Years
    years = [2000, 2005, 2010, 2015, 2020]

    # Region
    region = ee.Geometry.Rectangle(extent_latlong, proj="EPSG:4326", geodesic=False)
    region = region.buffer(10000).bounds()
    export_coord = region.getInfo()["coordinates"]

    # Hansen map
    IC = ee.ImageCollection(ee.Image("UMD/hansen/global_forest_change_2019_v1_7"))
    ds = xr.open_dataset(IC,
                        engine='ee',
                        crs='EPSG:4326',
                        scale=scale, # 1° ~110km => conversion to original resolution of ~30m
                        geometry=region,
                        ).drop_vars('time').squeeze()
    ds = ds.chunk({"lon": 1500, "lat": 1500})

    # Tree cover, loss, and gain
    treecover = ds["treecover2000"].load()
    lossyear = ds["lossyear"].load()

    # Forest in 2000
    forest2000 = treecover>=perc

    # Deforestation
    def determine_forest(lossyear, forest_ref, year):
        loss = (lossyear>=1) & (lossyear<=year-2000-1)
        return forest_ref.where(loss, 0).astype(np.bool).rename("forest"+str(year))
    forest = xr.merge(
        [lossyear.map_blocks(
            determine_forest,
            kwargs={"forest_ref":forest2000, "year":year}
            ) for year in years[1:]]
    )
    forest['forest2000'] = forest2000

    # Prepare the raster and save it to disk
    forest_date_list = [f"forest{i}" for i in years]
    forest = xr.concat([forest[i] for i in forest_date_list],dim=pd.Index(forest_date_list, name="bands")).\
                astype('b').\
                rio.set_spatial_dims(x_dim="lon", y_dim="lat").\
                rio.write_crs("epsg:4326").\
                rio.write_coordinate_system().\
                rename({"lon": "x", "lat": "y"}).\
                transpose("bands", "y", "x").\
                rename("forest").\
                rio.reproject(proj)

    # Save to disk
    forest.rio.to_raster(f"forest_{iso3}.tif", tiled=True, driver="GTiff", compress="LZW")
    # Parallel processing with Dask
    # with LocalCluster() as cluster, Client(cluster) as client:
    #     forest.rio.to_raster(f"forest_{iso3}.tif", tiled=True, driver="GTiff", compress="LZW", lock=Lock("rio", client=client),)