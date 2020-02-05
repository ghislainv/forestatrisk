#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Import
from setuptools import setup
from distutils.core import Extension
import numpy.distutils.misc_util

# Markdown README file
with open("README.md", "r") as fh:
    long_description = fh.read()

# Informations to compile internal hsdm module
hSDM_module = Extension("forestatrisk.hsdm",
                        sources=["C/hSDMmodule.c", "C/useful.c"])
                        #extra_compile_args=['-std=c99'])

# Setup
setup(name="forestatrisk",
      version="0.1.1",
      author="Ghislain Vieilledent",
      author_email="ghislain.vieilledent@cirad.fr",
      url="https://github.com/ghislainv/forestatrisk",
      license="GPLv3",
      description="This is the Python 'forestatrisk' package",
      long_description=long_description,
      long_description_content_type="text/markdown",
      classifiers=["Development Status :: 4 - Beta",
                   "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 3",
                   "Operating System :: OS Independent",
                   "Topic :: Scientific/Engineering :: Bio-Informatics"],
      keywords="deforestation hsdm hierarchical logistic model probability risk Bayesian spatial autocorrelation",
      python_requires=">=2.7",
      ext_modules=[hSDM_module],
      packages=["forestatrisk"],
      package_dir={"forestatrisk": "forestatrisk"},
      package_data={"forestatrisk": ["data/*.csv", "shell/data_country.sh",
                                     "shell/forest_country.sh"]},
      install_requires=["earthengine-api", "gdal", "numpy", "matplotlib",
                        "pandas", "patsy", "pywdpa", "sklearn"],
      include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs(),
      zip_safe=False)

# End
