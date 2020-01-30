#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

from __future__ import division, print_function  # Python 3 compatibility
import os
import matplotlib
if os.environ.get("DISPLAY", "") == "":
    print("no display found. Using non-interactive Agg backend")
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from .data import country, country_forest_gdrive
from .accuracy import confmat, accuracy
from .interpolate_rho import interpolate_rho
from .miscellaneous import invlogit, make_dir
from . import plot
from .model_binomial_iCAR import model_binomial_iCAR
from .model_random_forest import model_random_forest
from .sample import sample
from .cellneigh import cellneigh, cellneigh_ctry
from .predict_raster import predict_raster
from .predict_raster_binomial_iCAR import predict_raster_binomial_iCAR
from .resample_sum import resample_sum
from .deforest import deforest
from .validation import accuracy_indices, validation
from .validation_npix import validation_npix
from .emissions import emissions
from .countpix import countpix
from .diffproj import r_diffproj, mat_diffproj
from .wrast_rho import wrast_rho

# End
