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
import pickle


# computation
def computation():

    # Make output directory
    dfp.make_dir("output")

    # ========================================================
    # Sample points
    # ========================================================

    dataset = dfp.sample(nsamp=10000, Seed=1234, csize=10,
                         var_dir="data",
                         input_forest_raster="fcc12.tif",
                         output_file="output/sample.txt",
                         blk_rows=0)

    # To import data as pandas DataFrame if necessary
    # import pandas as pd
    # dataset = pd.read_table("output/sample.txt", delimiter=",")
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
        of = "output/correlation_" + str(f) + ".pdf"
        # Data
        y, data = dmatrices(formulas[f], data=dataset,
                            return_type="dataframe")
        # Plots
        dfp.plot.correlation(y=y, data=data,
                             plots_per_page=3,
                             figsize=(7, 8),
                             dpi=100,
                             output_file=of)

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
    f = open("output/summary_hSDM.txt", "w")
    f.write(str(mod_binomial_iCAR))
    f.close()

    # Plot
    mod_binomial_iCAR.plot(output_file="output/mcmc.pdf",
                           plots_per_page=3,
                           figsize=(9, 6),
                           dpi=100)

    # ========================================================
    # Resampling spatial random effects
    # ========================================================

    # Spatial random effects
    rho = mod_binomial_iCAR.rho

    # Resample
    dfp.resample_rho(rho=rho, input_raster="data/fcc12.tif",
                     output_file="output/rho.tif",
                     csize_orig=10, csize_new=1,
                     figsize=(5, 5),
                     dpi=150)

    # ========================================================
    # Predicting spatial probability of deforestation
    # ========================================================

    # Compute predictions
    dfp.predict(mod_binomial_iCAR, var_dir="data",
                input_cell_raster="output/rho.tif",
                input_forest_raster="data/fcc12.tif",
                output_file="output/pred_binomial_iCAR.tif",
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
    f = open("output/forest_cover.txt", "w")
    for i in fc:
        f.write(str(i) + "\n")
    f.close()

    # Annual deforestation
    annual_defor = (fc[0] - fc[3]) / 14.0
    # Amount of deforestation (ha) for 40 years
    defor_40yr = np.rint(annual_defor * 40)

    # ========================================================
    # Predicting forest cover change
    # ========================================================

    # Compute future forest cover
    stats = dfp.deforest(input_raster="output/pred_binomial_iCAR.tif",
                         hectares=defor_40yr,
                         output_file="output/fcc_40yr.tif",
                         blk_rows=128)

    # Save stats to disk with pickle
    pickle.dump(stats, open("output/stats.pickle", "wb"))

    # Plot histograms of probabilities
    dfp.plot.freq_prob(stats,
                       output_file="output/freq_prob.png")

    # ========================================================
    # Additional figures
    # ========================================================

    # Forest in 2010
    dfp.plot.forest("data/forest/forest_t2.tif",
                    borders="data/ctry_PROJ.shp",
                    output_file="output/forest_t2.png")

    # Forest-cover change 2005-2010
    dfp.plot.fcc("data/fcc12.tif",
                 borders="data/ctry_PROJ.shp",
                 output_file="output/fcc12.png")

    # Original spatial random effects
    dfp.plot.rho("output/rho_orig.tif",
                 borders="data/ctry_PROJ.shp",
                 output_file="output/rho_orig.png")

    # Interpolated spatial random effects
    dfp.plot.rho("output/rho.tif",
                 borders="data/ctry_PROJ.shp",
                 output_file="output/rho.png")

    # Spatial probability of deforestation
    dfp.plot.prob("output/pred_binomial_iCAR.tif",
                  borders="data/ctry_PROJ.shp",
                  output_file="output/prob.png")

    # Forest-cover change 2010-2050
    dfp.plot.fcc("output/fcc_40yr.tif",
                 borders="data/ctry_PROJ.shp",
                 output_file="output/fcc_40yr.png")

# End
