"""Using GEE to get forest cover change from TMF."""

# Annual product legend
# ---------------------
# 1. Undisturbed Tropical moist forest (TMF)
# 2. Degraded TMF
# 3. Deforested land
# 4. Forest regrowth
# 5. Permanent or seasonal water
# 6. Other land cover

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

# ee_jrc.run_task
def run_task(iso3, extent_latlong, scale=0.0002727272727, proj=None):
    """Compute forest-cover change with Google Earth Engine.

    Compute the forest-cover change from Joint Research Center (JRC)
    Vancutsem et al. data (v1\\_2020) with Python and GEE API and XEE backend.

    Notes for Google Earth Engine (abbreviated GEE):

    * GEE account is needed: `<https://earthengine.google.com>`_\\ .
    * GEE API Python client is needed: \
    `<https://developers.google.com/earth-engine/python_install>`_\\ .

    :param iso3: Country ISO 3166-1 alpha-3 code.
    :param extent_latlong: List/tuple of region extent in lat/long
        (xmin, ymin, xmax, ymax).
    :param scale: Resolution in degrees per pixel (as the default unit of the projection).
        Default to 0.0002727272727, which corresponds to 30m.
    :param proj: The projection for the export.

    :return: Google Earth Engine task.

    """
    # Years
    years = [2000, 2005, 2010, 2015, 2020]

    # Region
    region = ee.Geometry.Rectangle(extent_latlong, proj="EPSG:4326", geodesic=False)
    region = region.buffer(10000).bounds()
    export_coord = region.getInfo()["coordinates"]

    # JRC annual product (AP)
    IC = ee.ImageCollection("projects/JRC/TMF/v1_2022/AnnualChanges")
    ds = xr.open_dataset(IC,
                        engine='ee',
                        crs='EPSG:4326',
                        scale=scale, # 1° ~110km => conversion to original resolution of ~30m
                        geometry=region,
                        ).isel(time=2).drop_vars('time').squeeze()
    ds = ds.chunk({"lon": 1500, "lat": 1500})

    # Reorganize AP dataset
    date_list = range(years[0]-1, years[-1] + 1)
    AP = xr.concat(
        [ds[f"Dec{i}"] for i in date_list],
        dim = pd.Index(date_list, name="years")
        ).rename("Annuals Products")

    # AP_allYear: forest if Y = 1 or 2.
    def forest_masking(AP):
        return xr.where((AP==1) + (AP==2), 1, 0)
    AP_forest = AP.map_blocks(forest_masking)


    # Forest cover for each year
    def determine_forest(AP_forest, year, ref_year):
        return AP_forest.\
            sel(years=slice(year-1, ref_year+1)).\
            sum("years").\
            rename("forest"+str(year)) >= 1
    forest = xr.merge(
        [AP_forest.map_blocks(
            determine_forest,
            kwargs={"year":year, "ref_year":years[-1]}
            ) for year in years]
        )

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

