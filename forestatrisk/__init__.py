#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Standard library imports
from __future__ import division, print_function  # Python 3 compatibility
import os

# Third party imports
import matplotlib
# Use Agg if no display found
if os.environ.get("DISPLAY", "") == "":
    print("no display found. Using non-interactive Agg backend")
    matplotlib.use("Agg")

# Local imports
# Data
from .build_data import data, sample
# Misc
from .misc import countpix, invlogit, make_dir
# Model
from .model import cellneigh, cellneigh_ctry
from .model import model_binomial_iCAR
from .model import model_random_forest
# Plot
from .plot import plot
# Predict
from .predict import interpolate_rho, wrast_rho
from .predict import predict_raster, predict_raster_binomial_iCAR
# Project
from .project import deforest_diffusion, deforest_diffusion_t_nofor
from .project import deforest, emissions
# Validate
from .validate import computeAUC, accuracy_indices, cross_validation
from .validate import map_validation
from .validate import map_confmat, map_accuracy
from .validate import r_diffproj, mat_diffproj
from .validate import resample_sum
from .validate import validation_npix

# Welcome message
print("# forestatrisk: modelling and forecasting deforestation in the tropics.")
print("# https://ecology.ghislainv.fr/forestatrisk/")

# EOF
