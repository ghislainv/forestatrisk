#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Import
from distutils.core import setup, Extension
import numpy.distutils.misc_util


# Markdown README file
def readme():
    with open("README.md") as f:
        return f.read()

# Informations to compile internal hsdm module
hSDM_module = Extension("hsdm",
                        sources=["C/hSDMmodule.c", "C/useful.c"],
                        extra_compile_args=['-std=c99'])

# Setup
setup(name="deforestprob",
      version="0.1",
      author="Ghislain Vieilledent",
      author_email="ghislain.vieilledent@cirad.fr",
      url="https://github.com/ghislainv/deforestprob",
      license="GPLv3",
      description="This is the Python 'deforestprob' package",
      long_description=readme(),
      classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
      ],
      keywords="deforestation hsdm hierarchical logistic model probability \
      risk Bayesian spatial autocorrelation",
      ext_modules=[hSDM_module],
      packages=["deforestprob"],
      package_dir={"deforestprob": "deforestprob"},
      package_data={"deforestprob": ["data/*.csv", "data/proj.prj", "shell/data_country.sh", "shell/forest_country_gfc.sh"]},
      install_requires=["numpy", "sklearn", "patsy", "matplotlib", "pandas"],
      include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs(),
      zip_safe=False)
