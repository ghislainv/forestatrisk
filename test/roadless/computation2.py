#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

import numpy as np
from patsy import dmatrices
import deforestprob as dfp
import matplotlib.pyplot as plt
import pickle


# computation
def computation(fcc_source="roadless"):

    # Make output directory
    dfp.make_dir("output_2005_2015")

    # ========================================================
    # Sample points
    # ========================================================

    dataset = dfp.sample(nsamp=10000, Seed=1234, csize=10,
                         var_dir="data",
                         input_forest_raster="fcc12.tif",
                         output_file="output_2005_2015/sample.txt",
                         blk_rows=0)

    # To import data as pandas DataFrame if necessary
    # import pandas as pd
    # dataset = pd.read_table("output_2005_2015/sample.txt", delimiter=",")
    # dataset.head(5)

    # Descriptive statistics
    # Model formulas
    formula_1 = "fcc12 ~ dist_road + dist_town + dist_river + \
    dist_defor + dist_edge + altitude + slope + aspect - 1"
    # Standardized variables (mean=0, std=1)
    formula_2 = "fcc12 ~ scale(dist_road) + scale(dist_town) + \
    scale(dist_river) + scale(dist_defor) + scale(dist_edge) + \
    scale(altitude) + scale(slope) + scale(aspect) - 1"
    formulas = (formula_1, formula_2)

    # Remove NA from data-set (otherwise scale() and
    # model_binomial_iCAR doesn't work)
    dataset = dataset.dropna(axis=0)

    # Loop on formulas
    for f in range(len(formulas)):
        # Output file
        of = "output_2005_2015/correlation_" + str(f) + ".pdf"
        # Data
        y, data = dmatrices(formulas[f], data=dataset,
                            return_type="dataframe")
        # Plots
        figs = dfp.plot.correlation(y=y, data=data,
                                    plots_per_page=3,
                                    figsize=(7, 8),
                                    dpi=100,
                                    output_file=of)
        plt.close("all")

    # ========================================================
    # hSDM model
    # ========================================================

    # Set number of trials to one
    dataset["trial"] = 1

    # Spatial cells for spatial-autocorrelation
    nneigh, adj = dfp.cellneigh(raster="data/fcc12.tif", csize=10, rank=1)

    # List of variables
    variables = ["C(pa)", "scale(altitude)", "scale(slope)",
                 "scale(dist_defor)", "scale(dist_edge)", "scale(dist_road)",
                 "scale(dist_town)", "scale(dist_river)"]
    variables = np.array(variables)

    # Run model while there is non-significant variables
    var_remove = True
    while(np.any(var_remove)):

        # Formula
        right_part = " + ".join(variables) + " + cell"
        left_part = "I(1-fcc12) + trial ~ "
        formula = left_part + right_part

        # Model
        mod_binomial_iCAR = dfp.model_binomial_iCAR(
            # Observations
            suitability_formula=formula, data=dataset,
            # Spatial structure
            n_neighbors=nneigh, neighbors=adj,
            # Chains
            burnin=1000, mcmc=1000, thin=1,
            # Starting values
            beta_start=-99)

        # Ecological and statistical significance
        effects = mod_binomial_iCAR.betas[1:]
        # MCMC = mod_binomial_iCAR.mcmc
        # CI_low = np.percentile(MCMC, 2.5, axis=0)[1:-2]
        # CI_high = np.percentile(MCMC, 97.5, axis=0)[1:-2]
        positive_effects = (effects >= 0)
        # zero_in_CI = ((CI_low * CI_high) <= 0)

        # Keeping only significant variables
        var_remove = positive_effects
        # var_remove = np.logical_or(positive_effects, zero_in_CI)
        var_keep = np.logical_not(var_remove)
        variables = variables[var_keep]

    # Re-run the model with longer MCMC and estimated initial values
    mod_binomial_iCAR = dfp.model_binomial_iCAR(
        # Observations
        suitability_formula=formula, data=dataset,
        # Spatial structure
        n_neighbors=nneigh, neighbors=adj,
        # Chains
        burnin=5000, mcmc=5000, thin=5,
        # Starting values
        beta_start=mod_binomial_iCAR.betas)

    # Summary
    print(mod_binomial_iCAR)
    # Write summary in file
    f = open("output_2005_2015/summary_hSDM.txt", "w")
    f.write(str(mod_binomial_iCAR))
    f.close()

    # Plot
    figs = mod_binomial_iCAR.plot(output_file="output_2005_2015/mcmc.pdf",
                                  plots_per_page=3,
                                  figsize=(9, 6),
                                  dpi=100)
    plt.close("all")

    # ========================================================
    # Resampling spatial random effects
    # ========================================================

    # Spatial random effects
    rho = mod_binomial_iCAR.rho

    # Resample
    dfp.resample_rho(rho=rho, input_raster="data/fcc12.tif",
                     output_file="output_2005_2015/rho.tif",
                     csize_orig=10, csize_new=1,
                     figsize=(5, 5),
                     dpi=150)

    # ========================================================
    # Predicting spatial probability of deforestation
    # ========================================================

    # Compute predictions
    dfp.predict(mod_binomial_iCAR, var_dir="data",
                input_cell_raster="output_2005_2015/rho.tif",
                input_forest_raster="data/forest/forest_t3.tif",
                output_file="output_2005_2015/prob.tif",
                blk_rows=128)

    # ========================================================
    # Mean annual deforestation rate (ha.yr-1)
    # ========================================================

    # Forest cover
    fc = list()
    for i in range(4):
        rast = "data/forest/forest_t" + str(i) + ".tif"
        val = dfp.countpix(input_raster=rast,
                           value=1)
        fc.append(val["area"])
    # Save results to disk
    f = open("output_2005_2015/forest_cover.txt", "w")
    for i in fc:
        f.write(str(i) + "\n")
    f.close()

    # Annual deforestation
    T = 10.0 if (fcc_source == "roadless") else 9.0
    annual_defor = (fc[1] - fc[3]) / T
    # Amount of deforestation (ha) for 35 years
    defor_35yr = np.rint(annual_defor * 35)

    # ========================================================
    # Predicting forest cover change
    # ========================================================

    # Compute future forest cover
    stats = dfp.deforest(input_raster="output_2005_2015/prob.tif",
                         hectares=defor_35yr,
                         output_file="output_2005_2015/fcc_35yr.tif",
                         blk_rows=128)

    # Save stats to disk with pickle
    pickle.dump(stats, open("output_2005_2015/stats.pickle", "wb"))

    # Plot histograms of probabilities
    fig_freq = dfp.plot.freq_prob(stats,
                                  output_file="output_2005_2015/freq_prob.png")
    plt.close(fig_freq)

    # ========================================================
    # Additional figures
    # ========================================================

    # Forest in 2015
    fig_forest = dfp.plot.forest("data/forest/forest_t3.tif",
                                 borders="data/ctry_PROJ.shp",
                                 output_file="output_2005_2015/forest_t3.png")
    plt.close(fig_forest)

    # Forest-cover change 2005-2010
    fig_fcc = dfp.plot.fcc("data/fcc12.tif",
                           borders="data/ctry_PROJ.shp",
                           output_file="output_2005_2015/fcc12.png")
    plt.close(fig_fcc)

    # Original spatial random effects
    fig_rho_orig = dfp.plot.rho("output_2005_2015/rho_orig.tif",
                                borders="data/ctry_PROJ.shp",
                                output_file="output_2005_2015/rho_orig.png")
    plt.close(fig_rho_orig)

    # Interpolated spatial random effects
    fig_rho = dfp.plot.rho("output_2005_2015/rho.tif",
                           borders="data/ctry_PROJ.shp",
                           output_file="output_2005_2015/rho.png")
    plt.close(fig_rho)

    # Spatial probability of deforestation
    fig_prob = dfp.plot.prob("output_2005_2015/prob.tif",
                             borders="data/ctry_PROJ.shp",
                             output_file="output_2005_2015/prob.png")
    plt.close(fig_prob)

    # Forest-cover change 2010-2050
    fig_fcc_35yr = dfp.plot.fcc("output_2005_2015/fcc_35yr.tif",
                                borders="data/ctry_PROJ.shp",
                                output_file="output_2005_2015/fcc_35yr.png")
    plt.close(fig_fcc_35yr)

# End
