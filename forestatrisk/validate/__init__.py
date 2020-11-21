#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ===================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ===================================================================

from .accuracy import confmat, accuracy
from .diffproj import r_diffproj, mat_diffproj
from .resample_sum import resample_sum
from .validation_npix import validation_npix
from .validation import computeAUC, accuracy_indices
from .validation import cross_validation, validation

# EOF
