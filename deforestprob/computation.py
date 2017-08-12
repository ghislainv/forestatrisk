#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

import matplotlib
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from patsy import dmatrices
import deforestprob as dfp

# Working directory
# os.chdir("/home/ghislain/Code/deforestprob/test/CIV")
# check with os.getcwd()

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

dataset.head(5)

# Descriptive statistics
# Model formulas
formula_1 = "fcc12 ~ dist_road + dist_town + dist_river + \
dist_defor + dist_edge + altitude + slope + aspect - 1"
# Standardized variables (mean=0, std=1)
formula_2 = "fcc12 ~ scale(dist_road) + scale(dist_town) + \
scale(dist_river) + scale(dist_defor) + scale(dist_edge) + \
scale(altitude) + scale(slope) + scale(aspect) - 1"
formulas = (formula_1, formula_2)

# Remove NA from data-set (otherwise scale() doesn't work)
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

# Remove observations with NA
dataset = dataset.dropna(axis=0)

# Spatial cells for spatial-autocorrelation
nneigh, adj = dfp.cellneigh(raster="data/fcc12.tif", csize=10, rank=1)

# Formula
formula = "I(1-fcc12) + trial ~ C(pa) + scale(altitude) + \
scale(slope) + scale(dist_defor) + np.power(scale(dist_defor),2) + \
scale(dist_edge) + scale(dist_road) + scale(dist_town) + \
scale(dist_river) + cell"

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

# Summary
print(mod_binomial_iCAR)
# Write summary in file
f = open("output/summary_hSDM.txt", "w") 
f.write(str(mod_binomial_iCAR))
f.close()

# Plot
traces_fig = mod_binomial_iCAR.plot(output_file="output/mcmc.pdf",
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
fig_pred = dfp.predict(mod_binomial_iCAR, var_dir="data",
                       input_cell_raster="output/rho.tif",
                       input_forest_raster="data/fcc12.tif",
                       output_file="output/pred_binomial_iCAR.tif",
                       blk_rows=128,
                       dpi=200)

# ========================================================
# Mean annual deforestation rate on 2000-2010
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
annual_defor = (fc[0]-fc[2])/10
# Amount of deforestation (ha) for 40 years
defor_40yr = np.rint(annual_defor * 40)

# ========================================================
# Predicting forest cover
# ========================================================

# Compute future forest cover
dfp.deforest(input_raster="output/pred_binomial_iCAR.tif",
             hectares=defor_40yr,
             output_file="output/forest_cover_2050.tif",
             blk_rows=128)

# Plot future forest cover
dfp.plot.forest(input_forest_raster="output/forest_cover_2050.tif",
                output_file="output/forest_cover_2050.png",
                col=(227, 26, 28, 255),  # rgba color for deforestation
                figsize=(4, 4),
                dpi=200)

# End
