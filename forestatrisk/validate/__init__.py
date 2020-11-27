#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ===================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ===================================================================

from .diffproj import r_diffproj, mat_diffproj
from .model_validation import computeAUC, accuracy_indices, cross_validation
from .map_validation import map_validation
from .map_accuracy import map_confmat, map_accuracy
from .resample_sum import resample_sum
from .validation_npix import validation_npix  # Deprecated function

# EOF
