"""
forestatrisk: modelling and forecasting deforestation in the tropics.
https://ecology.ghislainv.fr/forestatrisk/
"""

# Standard library imports
from __future__ import division, print_function  # Python 3 compatibility

# Define double undescore variables
# https://peps.python.org/pep-0008/#module-level-dunder-names
__author__ = "Ghislain Vieilledent"
__email__ = "ghislain.vieilledent@cirad.fr"
__version__ = "1.2.1"

# GDAL exceptions
from osgeo import gdal

# Local imports
# Data
from .data import sample, get_vector_extent
from .data import extent_shp, create_symbolic_links

# Model
from .model import cellneigh, cellneigh_ctry
from .model import model_binomial_iCAR
from .model import model_random_forest
from .model import icarModelPred

# Predict
from .predict import interpolate_rho, wrast_rho
from .predict import predict_raster, predict_raster_binomial_iCAR
from .predict import defrate_per_cat

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
from .validate import validation_udef_arp

# Plot
from .plot import plot

# Misc
from .misc import countpix, invlogit, make_dir

# GDAL exceptions
gdal.UseExceptions()

# EOF
