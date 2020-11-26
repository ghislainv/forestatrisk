..
   # ==============================================================================
   # author          :Ghislain Vieilledent
   # email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
   # web             :https://ecology.ghislainv.fr
   # license         :GPLv3
   # ==============================================================================

.. image:: https://ecology.ghislainv.fr/forestatrisk/_images/logo-far.svg
   :align: right
   :target: https://ecology.ghislainv.fr/forestatrisk
   :alt: Logo forestatrisk
   :width: 140px

``forestatrisk`` Python package
*******************************

.. image:: https://badge.fury.io/py/forestatrisk.svg
   :target: https://badge.fury.io/py/forestatrisk
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/forestatrisk.svg
   :target: https://pypi.org/project/forestatrisk
   :alt: Python version

.. image:: https://api.travis-ci.org/ghislainv/forestatrisk.svg?branch=master
   :target: https://travis-ci.org/ghislainv/forestatrisk
   :alt: Travis CI
	 
.. image:: https://img.shields.io/badge/licence-GPLv3-8f10cb.svg
   :target: https://www.gnu.org/licenses/gpl-3.0.html
   :alt: License GPLv3	 

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.996337.svg
   :target: https://doi.org/10.5281/zenodo.996337
   :alt: Zenodo
	 
Overview
========

The ``forestatrisk`` Python package can be used to model and forecast
deforestation in the tropics. It provides functions to estimate the
spatial probability of deforestation in the tropics depending on
various spatial explanatory variables.

Spatial explanatory variables can be derived from topography
(altitude, slope, and aspect), accessibility (distance to roads,
towns, and forest edge), deforestation history (distance to previous
deforestation) or land conservation status (eg. protected area) for
example.

.. image:: https://ecology.ghislainv.fr/forestatrisk/_images/forestatrisk.png
   :width: 500px
   :align: center
   :target: https://ecology.ghislainv.fr/forestatrisk/_images/forestatrisk.png
   :alt: prob_AFR

Installation
============

You will need several dependencies to run the ``forestatrisk`` Python
package. The best way to install the package is to create a Python
virtual environment, either through ``virtualenv`` or ``conda``.

Using ``virtualenv``
--------------------

You first need to have the ``virtualenv`` package installed (see `here <https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/>`__).

Then, create a virtual environment and install the ``forestatrisk`` package with the following commands:

.. code-block:: shell

   cd ~
   mkdir venvs # Directory for virtual environments
   cd venvs
   virtualenv --python=/usr/bin/python3 venv-far
   source ~/venvs/venv-far/bin/activate
   pip install numpy # Install numpy first
   # pip install forestatrisk # For PyPI version, this will install all other dependencies
   pip install https://github.com/ghislainv/forestatrisk/archive/master.zip # For GitHub dev version
   pip install statsmodels # Optional additional packages

To deactivate and delete the virtual environment:

.. code-block:: shell
		
   deactivate
   rm -R ~/venvs/venv-far # Just remove the repository

Using ``conda``
---------------

You first need to have ``miniconda3`` installed (see `here <https://docs.conda.io/en/latest/miniconda.html>`__).

Then, create a conda environment (details `here <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`__) and install the ``forestatrisk`` package with the following commands:

.. code-block:: shell
		
   conda create --name conda-far python gdal numpy matplotlib pandas patsy pip statsmodels --yes
   conda activate conda-far
   conda install -c conda-forge earthengine-api --yes
   pip install pywdpa sklearn # Packages not available with conda
   # pip install forestatrisk # For PyPI version
   pip install https://github.com/ghislainv/forestatrisk/archive/master.zip # For GitHub dev version
   # conda install -c conda-forge python-dotenv rclone --yes  # Potentially interesting libraries

To deactivate and delete the conda environment:

.. code-block:: shell
		
   conda deactivate
   conda env remove --name conda-far

Main functionalities
====================

Sample
------

Function ``.sample()`` allows the random sampling of observations points
considering historical deforestation maps. The sampling is balanced
and stratified considering remaining forest and deforested areas after
a given period of time. The function also retrieves information from
environmental variables for each sampled point. The sampling is done
by block to allow the computation on large study areas (e.g. country
or continental scale) with a high spatial resolution (e.g. 30m).

Model
-----

Function ``.model_binomial_iCAR()`` can be used to fit the deforestation
model from the data. A linear Binomial logistic regression model is
used to estimate the parameters of the deforestation model. The model
includes an intrinsic Conditional Autoregressive (iCAR) process to
account for the spatial autocorrelation of the observations
(Vieilledent et al. 2014). Parameter inference is done in a
hierarchical Bayesian framework. The function calls a Gibbs sampler
with a Metropolis algorithm written in pure C code to reduce
computation time.

Predict and project
-------------------

Function ``.predict()`` allows predicting the deforestation probability
on the whole study area using the deforestation model fitted with the
``.model()`` function. The prediction is done by block to allow the
computation on large study areas (e.g. country or continental scale)
with a high spatial resolution (e.g. 30m).

Function ``.deforest()`` predicts the future forest cover map based on a
raster of probability of deforestation (rescaled from 1 to 65535),
which is obtained from function ``.predict()``, and an area (in
hectares) to be deforested.

