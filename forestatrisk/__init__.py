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

# EOF
