"""Allocating deforestation."""

import os

import numpy as np
from osgeo import gdal
import pandas as pd

# Local application imports
from forestatrisk.misc import progress_bar, makeblock

opj = os.path.join
opd = os.path.dirname


def allocate_deforestation(riskmap_juris_file, defor_rate_tab,
                           defor_juris_ha, years_forecast,
                           project_borders,
                           output_file="defor_project.csv",
                           defor_density_map=False,
                           blk_rows=128,
                           verbose=False):
    """Allocating deforestation.

    :param riskmap_juris_file: Raster file with classes of deforestation
      risk at the jurisdictional level.

    :param defor_rate_tab: CSV file including the table with
      deforestation rates for each deforestation class.

    :param defor_juris_ha: Expected deforestation at the
      jurisdictional level (in hectares).

    :param years_forecast: Length of the forecasting period (in years).

    :param project_borders: Vector file for project borders.

    :param output_file: Output file with deforestation
      allocated to the project.

    :param defor_density_map: Compute the deforestation density map
      for the jurisdiction. Deforestation density is provided in
      ha/pixel/year (hectares of deforestation per pixel per year).
      Deforestation densities are floating-point numbers. For large
      jurisdictions (e.g. country scale) and high resolutions (e.g. 30
      m), this will produce a large raster file which will occupy
      a large amount of space on disk (e.g. several gigabytes).

    :param blk_rows: If > 0, number of rows for block (else 256x256).

    :param verbose: If True, print messages.

    """

    # Callback
    cback = gdal.TermProgress_nocb if verbose else 0

    # Creation options
    copts = ["COMPRESS=DEFLATE", "BIGTIFF=YES"]

    # ---------------------------------------
    # Crop riskmap to project boundaries
    # ---------------------------------------

    out_dir = opd(output_file)
    ofile = opj(out_dir, "project_riskmap.tif")
    gdal.Warp(ofile, riskmap_juris_file,
              cropToCutline=True,
              warpOptions=["CUTLINE_ALL_TOUCHED=TRUE"],
              cutlineDSName=project_borders,
              creationOptions=copts,
              callback=cback)

    # ---------------------------------------
    # Compute number of pixels for each class
    # ---------------------------------------

    nvalues = 65535
    with gdal.Open(ofile) as ds:
        band = ds.GetRasterBand(1)
        counts = band.GetHistogram(0.5, 65535.5, nvalues, 0, 0)
    data = {
        "cat": [i + 1 for i in range(65535)],
        "counts": counts}
    df_count = pd.DataFrame(data)

    # Upload deforestation rates
    df_rate = pd.read_csv(defor_rate_tab)

    # -----------------------------
    # Compute deforestation density
    # -----------------------------

    # Pixel area
    pixel_area = df_rate.loc[0, "pixel_area"]

    # Correction factor, either ndefor / sum_i p_i
    # or theta * nfor / sum_i p_i
    sum_pi = (df_rate["nfor"] * df_rate["rate_mod"]).sum()
    correction_factor = defor_juris_ha / (pixel_area * sum_pi)

    # Absolute deforestation rate
    df_rate["rate_abs"] = df_rate["rate_mod"] * correction_factor

    # Deforestation density (ha/pixel/yr)
    df_rate["defor_dens"] = df_rate["rate_abs"] * pixel_area / years_forecast

    # Save the df_rate table
    ofile = opj(out_dir, "defrate_cat_forecast.csv")
    df_rate.to_csv(ofile)

    # -----------------------------
    # Join tables
    # -----------------------------

    df_project = df_count.merge(right=df_rate, on="cat", how="left")

    # Annual deforestation (ha) for project
    defor_project = (df_project["counts"] * df_project["defor_dens"]).sum()

    # Save results
    data = {
        "period": ["annual", "entire"],
        "length (yr)": [1, years_forecast],
        "deforestation (ha)": [
            round(defor_project, 1),
            round(defor_project * years_forecast, 1)
        ]
    }
    res = pd.DataFrame(data)
    res.to_csv(output_file, header=True, index=False)

    # -----------------------------
    # Get deforestation density map
    # -----------------------------

    if defor_density_map:
        riskmap_r = gdal.Open(riskmap_juris_file)
        riskmap_b = riskmap_r.GetRasterBand(1)
        gt = riskmap_r.GetGeoTransform()
        proj = riskmap_r.GetProjection()
        ncol = riskmap_r.RasterXSize
        nrow = riskmap_r.RasterYSize

        output_file = opj(out_dir, "deforestation_density_map.tif")
        driver = gdal.GetDriverByName("GTiff")
        if os.path.isfile(output_file):
            os.remove(output_file)
        ddm_r = driver.Create(
            output_file,
            ncol,
            nrow,
            1,
            gdal.GDT_Float64,
            ["COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"],
        )
        ddm_r.SetGeoTransform(gt)
        ddm_r.SetProjection(proj)
        ddm_b = ddm_r.GetRasterBand(1)
        ddm_b.SetNoDataValue(-9999.0)

        # Make blocks
        blockinfo = makeblock(riskmap_juris_file, blk_rows=blk_rows)
        nblock = blockinfo[0]
        nblock_x = blockinfo[1]
        x = blockinfo[3]
        y = blockinfo[4]
        nx = blockinfo[5]
        ny = blockinfo[6]
        if verbose:
            print(f"Divide region in {nblock} blocks")

        # Write raster of dd
        if verbose:
            print("Write deforestation density raster")
        # Loop on blocks of data
        for b in range(nblock):
            # Progress bar
            progress_bar(nblock, b + 1)
            # Position in 1D-arrays
            px = b % nblock_x
            py = b // nblock_x
            # Data for one block
            risk_data = riskmap_b.ReadAsArray(x[px], y[py], nx[px], ny[py])
            risk_data = risk_data.flatten(order="C")
            # Get defor density from risk class
            defor_dens = np.zeros(len(risk_data))
            defor_dens[risk_data == 0] = -9999.0
            which_rows = risk_data[risk_data != 0] - 1
            defor_dens[risk_data != 0] = df_rate.loc[which_rows, "defor_dens"]
            defor_dens = defor_dens.reshape((ny[py], nx[px]), order="C")
            # Write deforestation densities
            ddm_b.WriteArray(defor_dens, x[px], y[py])

        # Compute statistics
        if verbose:
            print("Compute statistics")
        ddm_b.FlushCache()  # Write cache data to disk
        ddm_b.ComputeStatistics(False)

        # Dereference gdal datasets
        riskmap_b = None
        ddm_b = None
        del riskmap_r, ddm_r


# # Test
# import os
# os.chdir(
#     os.path.expanduser("~/deforisk/MTQ-tuto/outputs/far_models/forecast/")
# )
# allocate_deforestation(
#     riskmap_juris_file="prob_icar_t3.tif",
#     defor_rate_tab="defrate_cat_icar_forecast.csv",
#     defor_juris_ha=4000,  # About 400 ha/yr in MTQ on 2010-2020.
#     years_forecast=10,
#     project_borders="project_boundaries.gpkg",
#     output_file="defor_project.csv",
#     defor_density_map=True,
#     blk_rows=128,
#     verbose=False,
# )

# End Of File
