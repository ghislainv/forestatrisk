---
title: "ForestAtRisk: A Python package for spatial modelling and forecasting of tropical deforestation"
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
  - name: European Commission, Joint Research Centre, I--21027 Ispra (VA), Italy.
    index: 4
date: 30 November 2020
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

The `ForestAtRisk` Python package can be used to model the tropical deforestation spatially and forecast the future forest cover in the tropics. It includes functions to (i) sample the forest cover change observations and retrieve the information on potential spatial explanatory variables for each observation, (ii) estimate the parameters of various spatial deforestation models, (iii) predict the spatial probability of deforestation, (iv) forecast the likely forest cover in the future, (v) validate the models and the projected maps of forest cover change, and (vi) plot the results. Spatial information is provided through georeferenced raster files which can be very large (several gigabytes). Functions in the `ForestAtRisk` package treat large rasters by blocks of data, making computations fast and efficient. This allows analysis on large geographical extent (e.g. country scale), and at high resolution (e.g. 30 m). The `ForestAtRisk` package offers the possibility to use a logistic regression model with auto-correlated spatial random effects to model the deforestation process. Spatial random effects allow to structure the residual spatial variability (which is often large) within the model. They account for unmeasured or unmeasurable variables that explain a part of the residual spatial variation in the deforestation process that is not explained by the model's explanatory variables. In addition to bringing new features, the `ForestAtRisk` Python package is open source (license GPLv3), cross-platform and scriptable (through Python), user-friendly (functions provided with full documentation and examples), and easily extendable (with additional statistical models for example). The `ForestAtRisk` Python package has been recently used to model the deforestation and forecast the future forest cover by 2100 in the whole humid tropics.

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

The `ForestAtRisk` Python package can be used to model the tropical deforestation spatially and forecast the future forest cover in the tropics (\autoref{fig:prob}).

Functions in the `ForestAtRisk` package treat large rasters by blocks of data, making computation fast and efficient (with low memory usage).

Using functions from the `ForestAtRisk` Python package makes computation fast and efficient (with low memory usage) by treating large raster data by blocks. Numerical computations on blocks of data are performed with the NumPy (<https://numpy.org>) Python module whose core is mostly made of optimized and compiled C code which runs fast [@Harris2020].

Using simple "glm" model is a commonly proposed approach for spatial modelling of deforestation [@Verburg2002; @Mas2007; @Rosa2014; @Ludeke1990; @Soares-Filho2002; @Mertens1997; @Soares-Filho2001; @Eastman2017]. The random forest model [@Breiman2001] is a machine learning approach using an ensemble of random classification trees (where both observations and features are chosen at random to build the classification trees) to predict the deforestation probability for a forest pixel. Random forest has been intensively used for species distribution modelling [@Thuiller2009] and is now also commonly used for spatial modelling of deforestation [@Grinand2020; @Zanella2017; @Santos2019]. The "glm" and "rf" models were fitted using functions `LinearRegression` and `RandomForestClassifier` respectively, both available in the `scikit-learn` Python package [@Pedregosa2011].

Using observations of forest cover change in the period 2010--2020, we modelled the spatial probability of deforestation as a function of the $n$ explanatory variables using a logistic regression. We considered the random variable $y_i$ which takes value 1 if the forest pixel $i$ was deforested in the period 2010--2020 and 0 if it was not. We assumed that $y_i$ follows a Bernoulli distribution of parameter $\theta_i$ (Eq. \@ref(eq:icar)). In our model, $\theta_i$ represents the spatial relative probability of deforestation for pixel $i$. We assumed that $\theta_i$ is linked, through a logit function, to a linear combination of the explanatory variables $X_i \beta$, where $X_i$ is the vector of explanatory variables for pixel $i$, and $\beta$ is the vector of effects $[\beta_1, \ldots, \beta_n]$ associated to the $n$ variables. All the continuous explanatory variables were normalized before fitting the model. The model includes an intercept $\alpha$. To account for the residual spatial variation in the deforestation process, we included an additional random effect $\rho_{j(i)}$ for each spatial cell $j$ of a 10 $\times$ 10 km grid covering each study-area. This grid resolution was chosen in order to have a reasonable balance between a good representation of the spatial variability of the deforestation process and a limited number of parameters to estimate. A sampled forest pixel $i$ was associated to one cell $j$ and one random effect $\rho_{j(i)}$. We assumed that random effects were spatially autocorrelated through an intrinsic conditional autoregressive (iCAR) model [@Besag1991; @Banerjee2014]. This model is denoted "icar" in subsequent sections and results. In an iCAR model, the random effect $\rho_j$ associated to cell $j$ depends on the values of the random effects $\rho_{j^{\prime}}$ associated to neighbouring cells $j^{\prime}$. In our case, the neighbouring cells are connected to the target cell $j$ through a common border or corner (cells defined by the "king move" in chess). The variance of the spatial random effects $\rho_j$ was denoted $V_{\rho}$. The number of neighbouring cells for cell $j$, which might vary, was denoted $n_j$. Spatial random effects $\rho_j$ account for unmeasured or unmeasurable variables [@Clark2005] that explain a part of the residual spatial variation in the deforestation process that is not explained by the fixed spatial explanatory variables ($X_i$).

\begin{equation}
\begin{split}
  y_i \sim \mathcal{B}ernoulli(\theta_i)\\
  \text{logit}(\theta_i) = \alpha + X_i \beta + \rho_{j(i)}\\
  \rho_{j(i)} \sim \mathcal{N}ormal(\sum_{j^{\prime}} \rho_{j^{\prime}} / n_j,V_{\rho} / n_j)
\end{split}
\end{equation}

Parameter inference is done in a hierarchical Bayesian framework. Function `model_binomial_iCAR()` from the `forestatrisk` Python package was used for parameter inference. This function calls an adaptive Metropolis-within-Gibbs algorithm [@Rosenthal2011] written in C for maximum computation speed.

# Figures

![**Map of the spatial probability of deforestation in the Guadeloupe archipelago.** Colored pixels represent the extent of the natural old-growth tropical moist forest in 2020. A relative spatial probability of deforestation is computed for each forest pixel. The original map has a 30 m resolution. Probability of deforestation is a function of several explanatory variables describing: topography (altitude and slope), accessibility (distances to nearest road, town, and river), forest landscape (distance to forest edge), deforestation history (distance to past deforestation), and land conservation status (presence of a protected area). This map can be reproduced following the Get Started tutorial at <https://ecology.ghislainv.fr/forestatrisk>.\label{fig:prob}](prob.png)

# Acknowledgements

I am grateful to Clovis Grinand, Romuald Vaudry and Matthieu Tiberghien who gave me the opportunity to work on deforestation modeling when we were leading forest conservation projects in Madagascar. I also warmly thank Frédéric Achard and all the members of the IFORCE group for their invaluable support during the first phase of development of the package, while I was seconded to the JRC in Ispra. This work benefited from funding by FRB-FFEM (BioSceneMada project, AAP-SCEN-2013 I), the European Commission (Roadless Forest project), and CNRT (RELIQUES project).

# References
