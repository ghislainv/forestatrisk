"""Allocating deforestation."""

import os

from osgeo import gdal
import pandas as pd

opj = os.path.join
opd = os.path.dirname


def allocate_deforestation(riskmap_juris_file, defor_rate_tab,
                           defor_juris_ha, years_forecast,
                           project_boundaries,
                           output_file="defor_project.csv",
                           verbose=False):
    """Allocating deforestation.

    :param riskmap_juris: Raster file with classes of deforestation
      risk at the jurisdictional level.

    :param defor_rate_tab: CSV file including the table with
      deforestation rates for each deforestation class.

    :param defor_juris_ha: Expected deforestation at the
      jurisdictional level (in hectares).

    :param years_forecast: Length of the forecasting period (in years).

    :param project_boundaries: Vector file for project boundaries.

    :param output_file: Output file with deforestation
      allocated to the project.

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
              cutlineDSName=project_boundaries,
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

    # -----------------------------
    # Join tables
    # -----------------------------

    df_project = df_count.merge(right=df_rate, on="cat", how="left")

    # Annual deforestation (ha) for project
    defor_project = (df_project["counts"] * df_project["defor_dens"]).sum()

    # Save results
    data = {
        "period": ["annual", "entire"],
        "deforestation (ha)": [round(defor_project, 1), round(defor_project * years_forecast, 1)]
    }
    res = pd.DataFrame(data)
    res.to_csv(output_file, header=True, index=False)


# Test
import os
os.chdir(os.path.expanduser("~/deforisk/MTQ-tuto-bak/outputs/far_models/forecast/"))
allocate_deforestation(
    riskmap_juris_file="prob_icar_t3.tif",
    defor_rate_tab="defrate_cat_icar_forecast.csv",
    defor_juris_ha=4000,  # About 400 ha/yr in MTQ on 2010-2020.
    years_forecast=10,
    project_boundaries="project_boundaries.gpkg",
    output_file="defor_project.csv",
    verbose=False,
)
