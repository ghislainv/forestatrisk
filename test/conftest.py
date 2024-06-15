#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# # ForastAtRisk Tropics

# This notebook provides a minimal and reproducible example for the
# following scientific article:

# **Vieilledent G., C. Vancutsem, and F. Achard.** Spatial forecasting
# **of forest cover change in the humid tropics over the 21st century.

# We use the [Guadeloupe](https://en.wikipedia.org/wiki/Guadeloupe)
# archipelago as a case study.

# Imports
import os
from shutil import copy2
from zipfile import ZipFile

try:
    from urllib.request import urlretrieve  # Python 3
except ImportError:
    from urllib import urlretrieve  # urlretrieve with Python 2

import pytest
import forestatrisk as far


@pytest.fixture(scope="session", autouse=True)
def gstart():
    """Test get started notebook."""
    # We create a directory to hold the outputs with the help of the
    # function `.make_dir()`.

    # Make output directory
    os.chdir("test")
    far.make_dir("output")

    # ## 1. Data

    # ### 1.1 Import and unzip the data

    # Source of the data
    url = (
        "https://github.com/ghislainv/forestatrisk/"
        "raw/master/docsrc/notebooks/data_GLP.zip"
    )
    if os.path.exists("data_GLP.zip") is False:
        urlretrieve(url, "data_GLP.zip")

    with ZipFile("data_GLP.zip", "r") as zfile:
        zfile.extractall("data")

    # ### 1.2 Files

    # The `data` folder includes:

    # - Forest cover change data for the period 2010-2020 as a GeoTiff
    #   raster file (`data/fcc23.tif`).

    # - Spatial explanatory variables as GeoTiff raster files (`.tif`
    #   extension, eg. `data/dist_edge.tif` for distance to forest
    #   edge).

    # - Additional folders: `forest`, `forecast`, and `emissions`, with
    #   forest cover change for different periods of time, explanatory
    #   variables at different dates used for projections in the future,
    #   and forest carbon data for computing carbon emissions.

    # Plot forest
    fig_fcc23 = far.plot.fcc(
        input_fcc_raster="data/fcc23.tif",
        maxpixels=1e8,
        output_file="output/fcc23.png",
        borders="data/aoi_proj.shp",
        linewidth=0.3,
        dpi=500,
    )

    # ### 1.3 Sampling the observations

    # Sample points
    dataset = far.sample(
        nsamp=10000,
        adapt=True,
        seed=1234,
        csize=10,
        var_dir="data",
        input_forest_raster="fcc23.tif",
        output_file="output/sample.txt",
        blk_rows=0,
    )

    # Remove NA from data-set (otherwise scale() and
    # model_binomial_iCAR doesn't work)
    dataset = dataset.dropna(axis=0)
    # Set number of trials to one for far.model_binomial_iCAR()
    dataset["trial"] = 1
    # Print the first five rows
    print(dataset.head(5))

    # ## 2. Model

    # ### 2.1 Model preparation

    # Neighborhood for spatial-autocorrelation
    nneigh, adj = far.cellneigh(raster="data/fcc23.tif", csize=10, rank=1)

    # List of variables
    variables = [
        "scale(altitude)",
        "scale(slope)",
        "scale(dist_defor)",
        "scale(dist_edge)",
        "scale(dist_road)",
        "scale(dist_town)",
        "scale(dist_river)",
    ]

    # Formula
    right_part = " + ".join(variables) + " + cell"
    left_part = "I(1-fcc23) + trial ~ "
    formula = left_part + right_part

    # Starting values
    # 0 for the test to avoid relying on scikit-learn if set to -99
    beta_start = 0

    # Priors
    priorVrho = -1  # -1="1/Gamma"

    # ### 2.3 iCAR model

    # Run the model
    mod_binomial_iCAR = far.model_binomial_iCAR(
        # Observations
        suitability_formula=formula,
        data=dataset,
        # Spatial structure
        n_neighbors=nneigh,
        neighbors=adj,
        # Priors
        priorVrho=priorVrho,
        # Chains
        burnin=100,
        mcmc=100,
        thin=1,
        # Starting values
        beta_start=beta_start,
    )

    # ### 2.4 Model summary

    # Predictions
    pred_icar = mod_binomial_iCAR.theta_pred

    # Summary
    print(mod_binomial_iCAR)
    # Write summary in file
    with open(
            "output/summary_hSDM.txt",
            "w",
            encoding="UTF-8") as file:
        file.write(str(mod_binomial_iCAR))

    # ## 3. Predict

    # ### 3.1 Interpolate spatial random effects

    # Spatial random effects
    rho = mod_binomial_iCAR.rho

    # Interpolate
    far.interpolate_rho(
        rho=rho,
        input_raster="data/fcc23.tif",
        output_file="output/rho.tif",
        csize_orig=10,
        csize_new=1,
    )

    # ### 3.2 Predict deforestation probability

    # Update dist_edge and dist_defor at t3
    os.rename("data/dist_edge.tif", "data/dist_edge.tif.bak")
    os.rename("data/dist_defor.tif", "data/dist_defor.tif.bak")
    copy2("data/forecast/dist_edge_forecast.tif", "data/dist_edge.tif")
    copy2("data/forecast/dist_defor_forecast.tif", "data/dist_defor.tif")

    # Compute predictions
    far.predict_raster_binomial_iCAR(
        mod_binomial_iCAR,
        var_dir="data",
        input_cell_raster="output/rho.tif",
        input_forest_raster="data/forest/forest_t3.tif",
        output_file="output/prob.tif",
        blk_rows=10,  # Reduced number of lines to avoid memory problems
    )

    # Reinitialize data
    os.remove("data/dist_edge.tif")
    os.remove("data/dist_defor.tif")
    os.rename("data/dist_edge.tif.bak", "data/dist_edge.tif")
    os.rename("data/dist_defor.tif.bak", "data/dist_defor.tif")

    # ## 4. Project future forest cover change

    # Forest cover
    fc = []
    dates = ["t2", "t3"]
    ndates = len(dates)

    for i in range(ndates):
        rast = "data/forest/forest_" + dates[i] + ".tif"
        val = far.countpix(input_raster=rast, value=1)
        fc.append(val["area"])  # area in ha

    # Save results to disk
    f = open("output/forest_cover.txt", "w")
    for i in fc:
        f.write(str(i) + "\n")
    f.close()
    # Annual deforestation
    T = 10.0
    annual_defor = (fc[0] - fc[1]) / T
    msg = (
        "Mean annual deforested area during " "the period 2020-2030: {} ha/yr"
    ).format(annual_defor)
    print(msg)

    # Projected deforestation (ha) during 2020-2050
    defor = annual_defor * 30

    # Compute future forest cover in 2050
    stats = far.deforest(
        input_raster="output/prob.tif",
        hectares=defor,
        output_file="output/fcc_2050.tif",
        blk_rows=128,
    )

    # ## 5. Figures

    # ### 5.1 Historical forest cover change

    # Forest cover change for the period 2000-2010-2020

    # Plot forest
    fig_fcc123 = far.plot.fcc123(
        input_fcc_raster="data/forest/fcc123.tif",
        maxpixels=1e8,
        output_file="output/fcc123.png",
        borders="data/ctry_PROJ.shp",
        linewidth=0.3,
        figsize=(6, 5),
        dpi=500,
    )

    # ### 5.2 Spatial random effects

    # Original spatial random effects
    fig_rho_orig = far.plot.rho(
        "output/rho_orig.tif",
        borders="data/ctry_PROJ.shp",
        linewidth=0.5,
        output_file="output/rho_orig.png",
        figsize=(9, 5),
        dpi=80,
    )

    # Interpolated spatial random effects
    fig_rho = far.plot.rho(
        "output/rho.tif",
        borders="data/ctry_PROJ.shp",
        linewidth=0.5,
        output_file="output/rho.png",
        figsize=(9, 5),
        dpi=80,
    )

    # ### 5.3 Spatial probability of deforestation

    # Spatial probability of deforestation
    fig_prob = far.plot.prob(
        "output/prob.tif",
        maxpixels=1e8,
        borders="data/ctry_PROJ.shp",
        linewidth=0.3,
        legend=True,
        output_file="output/prob.png",
        figsize=(6, 5),
        dpi=500,
    )

    # ### 5.4 Future forest cover

    # Projected forest cover change (2020-2050)
    fcc_2050 = far.plot.fcc(
        "output/fcc_2050.tif",
        maxpixels=1e8,
        borders="data/ctry_PROJ.shp",
        linewidth=0.3,
        output_file="output/fcc_2050.png",
        figsize=(6, 5),
        dpi=500,
    )

    return {
        "dataset": dataset,
        "nneigh": nneigh,
        "adj": adj,
        "pred_icar": pred_icar,
        "rho": rho,
        "fc": fc,
    }


# End Of File
