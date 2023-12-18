#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Installation setup.
"""

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Import
import io
import re
from distutils.core import Extension
from setuptools import setup, find_packages
import numpy.distutils.misc_util


# find_version
def find_version():
    """Finding package version."""
    with open("forestatrisk/__init__.py", encoding="utf-8") as init_file:
        init_text = init_file.read()
    far_version = re.search('^__version__\\s*=\\s*"(.*)"', init_text, re.M).group(1)
    return far_version


version = find_version()

# reStructuredText README file
with io.open("README.rst", encoding="utf-8") as f:
    long_description = f.read()

# Project URLs
project_urls = {
    "Documentation": "https://ecology.ghislainv.fr/forestatrisk",
    "Source": "https://github.com/ghislainv/forestatrisk/",
    "Traker": "https://github.com/ghislainv/pywdpa/forestatrisk",
}

# Informations to compile internal hbm module (hierarchical bayesian model)
hbm_module = Extension("forestatrisk.hbm", sources=["C/binomial_iCAR.c", "C/useful.c"])

# Setup
setup(
    name="forestatrisk",
    version=version,
    author="Ghislain Vieilledent",
    author_email="ghislain.vieilledent@cirad.fr",
    url="https://github.com/ghislainv/forestatrisk",
    license="GPLv3",
    description="Modelling and forecasting deforestation in the tropics",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    keywords="deforestation hbm hierarchical logistic model probability "
    "risk Bayesian spatial autocorrelation",
    python_requires=">=2.7",
    ext_modules=[hbm_module],
    packages=find_packages(),
    package_dir={"forestatrisk": "forestatrisk"},
    package_data={
        "forestatrisk": [
            "data/*.csv",
            "shell/data_country.sh",
            "shell/forest_country.sh",
        ]
    },
    include_package_data=True,
    entry_points={"console_scripts": ["forestatrisk = forestatrisk.forestatrisk:main"]},
    install_requires=[
        "earthengine-api",
        "gdal",
        "numpy",
        "matplotlib",
        "pandas",
        "patsy",
        "pywdpa",
        "scikit-learn",
    ],
    extras_require={
        "interactive": ["jupyter", "python-dotenv", "geopandas", "descartes", "folium"],
        "dev": ["pre-commit"],
    },
    include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs(),
    zip_safe=False,
)
