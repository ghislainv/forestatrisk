---
title: "forestatrisk: a Python package for modelling and forecasting deforestation in the tropics"
tags:
  - Python
  - land use change
  - spatial modelling
  - spatial analysis
  - forecasting
  - spatial autocorrelation
  - tropical forests
  - roads
  - protected areas
  - biodiversity scenario
  - ipbes
  - co2 emissions
  - ipcc
authors:
  - name: Ghislain Vieilledent
    orcid: 0000-0002-1685-4997
    affiliation: "1, 2, 3, 4"
affiliations:
  - name: CIRAD, UMR AMAP, F--34398 Montpellier, France
    index: 1
  - name: CIRAD, Forêts et Sociétés, F--34398 Montpellier, France.
    index: 2
  - name: AMAP, Univ Montpellier, CIRAD, CNRS, INRAE, IRD, Montpellier, France.
    index: 3
  - name: European Commission, Joint Research Centre (JRC), I--21027 Ispra (VA), Italy.
    index: 4
date: 6 December 2020
output:
  bookdown::pdf_document2:
    keep_md: yes
    keep_tex: yes
    citation_package: "natbib"
bibliography: paper.bib
#bibliography: /home/ghislain/Documents/Bibliography/biblio.bib
link-citations: yes
---

# Summary

The `forestatrisk` Python package can be used to model the spatial probability of deforestation and predict future forest cover in the tropics. The spatial data used to model deforestation comes from georeferenced raster files, which can be very large (several gigabytes). The functions available in the `forestatrisk` package process large rasters by blocks of data, making calculations fast and efficient. This allows deforestation to be modeled over large geographic areas (e.g. at the scale of a country) and at high spatial resolution (eg. $\leq$ 30 m). The `forestatrisk` package offers the possibility of using logistic regression with auto-correlated spatial random effects to model the deforestation process. The spatial random effects make possible to structure the residual spatial variability of the deforestation process, not explained by the variables of the model and often very large. In addition to these new features, the `forestatrisk` Python package is open source (GPLv3 license), cross-platform, scriptable (via Python), user-friendly (functions provided with full documentation and examples) and easily extendable (with statistical models for example). The Python package `forestatrisk` was recently used to model deforestation and predict future forest cover by 2100 across the humid tropics.

<!-- The JOSS paper should only include:

- A list of the authors of the software and their affiliations.
- A summary describing the high-level functionality and purpose of the software for a diverse, non-specialist audience.
- A clear statement of need that illustrates the purpose of the software.
- A description of how this software compares to other commonly-used packages in this research area.
- Mentions (if applicable) of any ongoing research projects using the software or recent scholarly publications enabled by it.
- A list of key references including a link to the software archive.

Compile with the following command:
docker run --rm \
    --volume $PWD/paper:/data \
    --user $(id -u):$(id -g) \
    --env JOURNAL=joss \
    openjournals/paperdraft

-->

# Statement of Need

Commonly called the "Jewels of the Earth", tropical forests shelter 30 million species of plants and animals representing half of the Earth's wildlife and at least two-thirds of its plant species [@Gibson2011]. Through photosynthesis and carbon sequestration, tropical forests play an important role in the global carbon cycle, and in regulating the global climate [@Baccini2017]. Despite the many ecosystem services they provide, tropical forests are disappearing at an alarming rate [@Keenan2015; @Vancutsem2020], mostly because of human activities. Currently, around 8 Mha (twice the size of Switzerland) of tropical forest are disappearing each year [@Keenan2015]. Spatial modelling of the deforestation allows identifying the main factors determining the spatial risk of deforestation and quantifying their relative effects. Forecasting forest cover change is paramount as it allows anticipating the consequences of deforestation (in terms of carbon emissions or biodiversity loss) under various technological, political and socio-economic scenarios, and informs decision makers accordingly [@Clark2001]. Because both biodiversity and carbon vary greatly in space [@Allnutt2008; @Baccini2017], it is necessary to provide spatial forecasts of forest cover change to properly quantify biodiversity loss and carbon emissions associated with future deforestation.

The `forestatrisk` Python package we present here can be used to model the tropical deforestation spatially, predict the spatial risk of deforestation, and forecast the future forest cover in the tropics (\autoref{fig:prob}). Several other software allow modelling and forecasting forest cover change [@Mas2014]. Most famous land cover change software include [Dinamica-EGO](https://csr.ufmg.br/dinamica/) [@Soares-Filho2002], [Land Change Modeller](https://clarklabs.org/terrset/land-change-modeler/) [@Eastman2017], and [CLUE](http://www.ivm.vu.nl/en/Organisation/departments/spatial-analysis-decision-support/Clue/) [@Verburg2009]. Despite the many functionalities they provide, these software are not open source and might not all be cross-platform, scriptable, and completely user-friendly. Moreover, the statistical approaches they propose to model the land cover change do not allow to take into account the residual spatial variability in the deforestation process which is not explained by the model's variables, and which is often very large. The more recent sophisticated algorithms they use (genetic algorithms, artificial neural networks, or machine learning algorithms) might also have the tendency to over-fit the data [@Mas2014]. Finally, the possibility to use these software on large spatial scales (e.g. at the country or continental scale) with high resolution data (e.g. $\leq$ 30 m) have not yet been demonstrated (but see @Soares-Filho2006 for a study in the Amazon at 1 km resolution). The `forestatrisk` Python package aims at filling some of these gaps and enlarging the range of software available to model and forecast tropical deforestation.

# Main functionalities

## A set of functions for modelling and forecasting deforestation

The `forestatrisk` Python package includes functions to (i) compute the forest cover change raster and the rasters of explanatory variables for a given country from several global datasets (such as OpenStreetMap or the SRTM Digital Elevation Database v4.1 for example) (ii) sample efficiently the forest cover change observations and retrieve the information on spatial explanatory variables for each observation, (iii) estimate the parameters of various statistical deforestation models, (iv) predict the spatial probability of deforestation, (v) forecast the likely forest cover in the future, (vi) validate the models and the projected maps of forest cover change, (vii) estimate the carbon emissions associated to future deforestation, and (viii) plot the results. The `forestatrisk` package includes a hierarchical Bayesian logistic regression model with autocorrelated spatial random effects which is well suited for modelling deforestation (see below). Any statistical model class with a `.predict()` method can potentially be used together with the function `forestatrisk.predict_raster()` to predict the spatial risk of deforestation. This allows a wide variety of additional statistical models from other Python packages to be used, such as `scikit-learn` [@Pedregosa2011] for example, for deforestation modeling and forecasting.

## Ability to process large raster data

Data for forest cover change and spatial explanatory variables are commonly available as georeferenced raster data. Raster data consist of rows and columns of cells (or pixels), with each cell storing a single value. The resolution of the raster dataset is its pixel width in ground units. Depending on the number of pixels (which is a function of the raster's geographical extent and resolution), raster files might occupy a space of several gigabytes on the hard drive. Processing such large rasters in memory can be prohibitively intensive. Functions in the `forestatrisk` package process large rasters by blocks of pixels representing subsets of the raster data. This makes computation efficient, with low memory usage. Reading and writing subsets of raster data is done by using two methods from the GDAL Python bindings [@GDAL2020]: `gdal.Dataset.ReadAsArray()` and `gdal.Band.WriteArray()`. Numerical computations on arrays are performed with the `NumPy` Python module whose core is mostly made of optimized and compiled C code which runs fast [@Harris2020]. This allows the `forestatrisk` Python package to model and forecast forest cover change on large spatial scales (eg. at the country or continental scale) using high resolution data (eg. $\leq$ 30 m), even on personal computers with average performance hardware. For example, the `forestatrisk` Python package has been used on a personal computer to model and forecast the forest cover change at 30 m resolution for the Democratic Republic of the Congo (total area of 2,345 million km$^2$), processing large raster files of 71,205 $\times$ 70,280 cells without issues.

## Statistical model with autocorrelated spatial random effects
The `forestatrisk` Python package includes a method called `forestatrisk.model_binomial_iCAR()` to estimate the parameters of a logistic regression model including auto-correlated spatial random effects. The model considers the random variable $y_i$ which takes value 1 if a forest pixel $i$ is deforested in a given period of time, and 0 if it is not. The model assumes that $y_i$ follows a Bernoulli distribution of parameter $\theta_i$ (\autoref{eq:icar}). $\theta_i$ represents the spatial relative probability of deforestation for pixel $i$ and is linked, through a logit function, to a linear combination of the explanatory variables $X_i \beta$, where $X_i$ is the vector of explanatory variables for pixel $i$, and $\beta$ is the vector of effects $[\beta_1, \ldots, \beta_n]$ associated to the $n$ variables. The model can include (or not) an intercept $\alpha$. To account for the residual spatial variation in the deforestation process, the model includes additional random effects $\rho_{j(i)}$ for the cells of a spatial grid covering the study-area. The spatial grid resolution has to be chosen in order to have a reasonable balance between a good representation of the spatial variability and a limited number of parameters to estimate. Each observation $i$ is associated to one spatial cell $j(i)$. Random effects $\rho_j$ are assumed to be spatially autocorrelated through an intrinsic conditional autoregressive (iCAR) model [@Besag1991]. In an iCAR model, the random effect $\rho_j$ associated to cell $j$ depends on the values of the random effects $\rho_{j^{\prime}}$ associated to neighbouring cells $j^{\prime}$. The variance of the spatial random effects $\rho_j$ is denoted by $V_{\rho}$. The number of neighbouring cells for cell $j$ (which might vary) is denoted $n_j$. Spatial random effects $\rho_j$ account for unmeasured or unmeasurable variables [@Clark2005] which explain a part of the residual spatial variation in the deforestation process that is not explained by the fixed (i.e. explanatory) variables ($X_i$). The parameter inference is done in a hierarchical Bayesian framework. The `far.model_binomial_iCAR()` method calls an adaptive Metropolis-within-Gibbs algorithm [@Rosenthal2011] written in C for maximum computation speed.

\begin{equation}
\begin{split}
  y_i \sim \mathcal{B}ernoulli(\theta_i)\\
  \text{logit}(\theta_i) = \alpha + X_i \beta + \rho_{j(i)}\\
  \rho_{j(i)} \sim \mathcal{N}ormal(\sum_{j^{\prime}} \rho_{j^{\prime}} / n_j,V_{\rho} / n_j)
\end{split}
\label{eq:icar}
\end{equation}

# Applications and perspectives

The Python package `forestatrisk` was recently used to model the spatial probability of deforestation and to predict the forest cover change in the year 2100 across the humid tropics (<https://forestatrisk.cirad.fr/tropics>). Future developments of the package will focus on expanding documentation, case studies, statistical models and validation tools. We are convinced that the `forestatrisk` package could be of great help in obtaining estimates of carbon emissions and biodiversity loss under various scenarios of deforestation in the tropics. Such scenarios should help decision-makers take initiatives to tackle climate change and the biodiversity crisis. The results from the `forestatrisk` package could contribute to future IPCC and IPBES reports [@IPCC2014; @IPBES2019] or help implement the REDD$+$ mechanism of the [Paris Agreement](https://unfccc.int/process-and-meetings/the-paris-agreement/the-paris-agreement).

# Figures

![**Map of the spatial probability of deforestation in the Guadeloupe archipelago.** This map has been produced with the `forestatrisk` Python package. Colored pixels represent the extent of the natural old-growth tropical moist forest in 2020. The original map has a 30 m resolution. A relative spatial probability of deforestation was computed for each forest pixel. Probability of deforestation is a function of several explanatory variables describing: topography (altitude and slope), accessibility (distances to nearest road, town, and river), forest landscape (distance to forest edge), deforestation history (distance to past deforestation), and land conservation status (presence of a protected area). This map can be reproduced following the /Get Started/ tutorial at <https://ecology.ghislainv.fr/forestatrisk>.\label{fig:prob}](prob.png)

# Acknowledgements

I am grateful to Clovis Grinand, Romuald Vaudry and Matthieu Tiberghien who gave me the opportunity to work on deforestation modelling when we were leading forest conservation projects in Madagascar. I also warmly thank Frédéric Achard and all the members of the IFORCE group for their invaluable support during the first phase of development of the package, while I was seconded to the JRC in Ispra. I would also like to thank Chris Garrard for writing the book _"Geoprocessing with Python"_ [@Garrard2016] which has been of great help in the development of the `forestatrisk` package. This work benefited from funding by FRB-FFEM (BioSceneMada project, AAP-SCEN-2013 I), the European Commission (Roadless Forest project), and CNRT (RELIQUES project).

# References
