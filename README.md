# forestatrisk Python package

## Estimating the risk of deforestation in tropical countries

`forestatrisk` is a Python package for estimating the spatial
probability of deforestation in the tropics depending on various
spatial environmental variables.

Spatial environmental variables can be derived from topography
(altitude, slope, and aspect), accessibility (distance to roads,
towns, and forest edge), deforestation history (distance to previous
deforestation) or landscape management (location inside a protected area)
for example.

### Sampling

Function `.sample()` allows the random sampling of observations points
considering historical deforestation maps. The sampling is balanced
and stratified considering remaining forest and deforested areas after
a given period of time. The function also retrieves information from
environmental variables for each sampled point. The sampling is done
by block to allow the computation on large study areas (e.g. country
or continental scale) with a high spatial resolution (e.g. 30m).

### Modelling

Function `.model_binomial_iCAR()` can be used to fit the deforestation
model from the data. A linear Binomial logistic regression model is
used to estimate the parameters of the deforestation model. The model
includes an intrinsic Conditional Autoregressive (iCAR) process to
account for the spatial autocorrelation of the observations
(Vieilledent et al. 2014). Parameter inference is done in a
hierarchical Bayesian framework. The function calls a Gibbs sampler
with a Metropolis algorithm written in pure C code to reduce
computation time.

### Predicting

Function `.predict()` allows predicting the deforestation probability
on the whole study area using the deforestation model fitted with the
`.model()` function. The prediction is done by block to allow the
computation on large study areas (e.g. country or continental scale)
with a high spatial resolution (e.g. 30m).

Function `.deforest()` predicts the future forest cover map based on a
raster of probability of deforestation (rescaled from 1 to 65535),
which is obtained from function `.predict()`, and an area (in
hectares) to be deforested.

## Tutorial

We wrote a tutorial using a Jupyter/IPython notebook to show how to
use the `forestatrisk` Python package. We took Madagascar as a case
study considering past deforestation on the period 2000-2010,
estimating deforestation probability for the year 2010, and projecting
the future forest cover in 2050. The notebook is available at the
following web adress: https://ecology.ghislainv.fr/forestatrisk

## Reference

**Vieilledent G., C. Merow, J. Guélat, A. M. Latimer, M. Kéry,
A. E. Gelfand, A. M. Wilson, F. Mortier and J. A. Silander
Jr.** 2014. hSDM CRAN release v1.4 for hierarchical Bayesian species
distribution models. _Zenodo_.
doi: [10.5281/zenodo.48470](http://doi.org/10.5281/zenodo.48470)

## Installation

The easiest way to install the `forestatrisk` Python package is via [pip](https://pip.pypa.io/en/stable/):

```
~$ sudo pip install --upgrade https://github.com/ghislainv/forestatrisk/archive/master.zip
```

but you can also install it executing the `setup.py` file:

```
~$ git clone https://github.com/ghislainv/forestatrisk
~$ cd forestatrisk
~/forestatrisk$ sudo python setup.py install
```

## Figure

Map of the probability of deforestation in Madagascar for the year
2010 obtained with `forestatrisk`. Dark red: high probability of
deforestation, Dark green: low probability of deforestation.

<img src="notebook/images/pred_binomial_iCAR.png" width=350>

