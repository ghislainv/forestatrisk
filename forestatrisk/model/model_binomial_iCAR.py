#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ===================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ===================================================================

# Standard library imports
from __future__ import division, print_function  # Python 3 compatibility

# Third party imports
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import numpy as np
from patsy import dmatrices, build_design_matrices, EvalEnvironment
from sklearn.linear_model import LogisticRegression

# Local application imports
from ..misc import invlogit
from .. import hbm


# model_binomial_iCAR
class model_binomial_iCAR(object):

    """model_binomial_iCAR class.

    model_binomial_iCAR class to estimates the parameters of a Binomial
    model with iCAR process for spatial autocorrelation in a
    hierarchical Bayesian framework.

    :param suitability_formula: A formula-like object that can be
        used to construct a design matrix (see ``patsy.dmatrices``).

    :param data: A dict-like object that can be used to look up
        variables referenced in ``suitability_formula``.

    :param n_neighbors: A vector of integers that indicates the
        number of neighbors (adjacent entities) of each spatial
        entity. length(n.neighbors) indicates the total number of
        spatial entities.

    :param neighbors: A vector of integers indicating the
        neighbors (adjacent entities) of each spatial entity. Must be
        of the form c(neighbors of entity 1, neighbors of entity 2,
        ... , neighbors of the last entity). Length of the neighbors
        vector should be equal to sum(n.neighbors).

    :param NA_action: What to do with rows that contain missing
        values (see ``patsy.dmatrices``).

    :param data_pred: Optional dataset for predictions.

    :param eval_env: Environment used to look up any variables
        referenced in suitability_formula that cannot be found in data
        (see ``patsy.dmatrices``).

    :param burnin: Number of iterations for the burnin phase.

    :param mcmc: The number of Gibbs iterations for the
        sampler. Total number of Gibbs iterations is equal to
        burnin+mcmc. burnin+mcmc must be divisible by 10 and superior
        or equal to 100 so that the progress bar can be displayed.

    :param thin: The thinning interval used in the simulation. The
        number of mcmc iterations must be divisible by this value.

    :param beta_start: Starting values for beta parameters. This
        can either be a scalar or a p-length vector.

    :param Vrho_start: Positive scalar indicating the starting
        value for the variance of the spatial random effects.

    :param mubeta: Means of the priors for the beta parameters of the
        suitability process. mubeta must be either a scalar or a
        p-length vector. If mubeta takes a scalar value, then that
        value will serve as the prior mean for all of the betas. The
        default value is set to 0 for an uninformative prior.

    :param Vbeta: Variances of the Normal priors for the beta
        parameters of the suitability process. Vbeta must be either a
        scalar or a p-length vector. If Vbeta takes a scalar value,
        then that value will serve as the prior variance for all of
        the betas. The default variance is large and set to 1000 for
        an uninformative flat prior.

    :param priorVrho: Type of prior for the variance of the
        spatial random effects. Can be set to a fixed positive scalar,
        or to an inverse-gamma distribution ("1/Gamma") with
        parameters shape and rate, or to a uniform distribution
        ("Uniform") on the interval [0,Vrho.max]. Default set to
        "1/Gamma".

    :param shape: The shape parameter for the Gamma prior on the
        precision of the spatial random effects. Default value is
        shape=0.5 for uninformative prior.

    :param rate: The rate (1/scale) parameter for the Gamma prior
        on the precision of the spatial random effects. Default value
        is rate=0.0005 for uninformative prior.

    :param Vrho_max: Upper bound for the uniform prior of the
        spatial random effect variance. Default set to 10.

    :param seed: The seed for the random number generator. Default
        set to 1234.

    :param verbose: A switch (0,1) which determines whether or not
        the progress of the sampler is printed to the screen. Default
        is 1: a progress bar is printed, indicating the step (in %)
        reached by the Gibbs sampler.

    :param save_rho: A switch (0,1) which determines whether or
        not the sampled values for rhos are saved. Default is 0: the
        posterior mean is computed and returned in the rho.pred
        vector. Be careful, setting save.rho to 1 might require a
        large amount of memory.

    :param save_p: A switch (0,1) which determines whether or not
        the sampled values for predictions are saved. Default is 0:
        the posterior mean is computed and returned in the theta.pred
        vector. Be careful, setting save.p to 1 might require a large
        amount of memory.

    :return: An object of class model_binomial_iCAR.

    """

    def __init__(self,  # Observations
                 suitability_formula, data,
                 # Spatial structure
                 n_neighbors, neighbors,
                 # NA action
                 NA_action="drop",
                 # Predictions
                 data_pred=None,
                 # Environment
                 eval_env=0,
                 # Chains
                 burnin=1000, mcmc=1000, thin=1,
                 # Starting values
                 beta_start=0,
                 Vrho_start=1,
                 # Priors
                 mubeta=0, Vbeta=1000,
                 priorVrho=-1.0,  # -1="1/Gamma"
                 shape=0.5, rate=0.0005,
                 Vrho_max=10,
                 # Various
                 seed=1234, verbose=1,
                 save_rho=0, save_p=0):
        """Function to fit a model_binomial_iCAR model.

        The function model_binomial_iCAR estimates the parameters of a
        Binomial model with iCAR process for spatial autocorrelation
        in a hierarchical Bayesian framework.

        :param suitability_formula: A formula-like object that can be
        used to construct a design matrix (see ``patsy.dmatrices``).

        :param data: A dict-like object that can be used to look up
        variables referenced in ``suitability_formula``.

        :param n_neighbors: A vector of integers that indicates the
        number of neighbors (adjacent entities) of each spatial
        entity. length(n.neighbors) indicates the total number of
        spatial entities.

        :param neighbors: A vector of integers indicating the
        neighbors (adjacent entities) of each spatial entity. Must be
        of the form c(neighbors of entity 1, neighbors of entity 2,
        ... , neighbors of the last entity). Length of the neighbors
        vector should be equal to sum(n.neighbors).

        :param NA_action: What to do with rows that contain missing
        values (see ``patsy.dmatrices``).

        :param data_pred: Optional dataset for predictions.

        :param eval_env: Environment used to look up any variables
        referenced in suitability_formula that cannot be found in data
        (see ``patsy.dmatrices``).

        :param burnin: Number of iterations for the burnin phase.

        :param mcmc: The number of Gibbs iterations for the
        sampler. Total number of Gibbs iterations is equal to
        burnin+mcmc. burnin+mcmc must be divisible by 10 and superior
        or equal to 100 so that the progress bar can be displayed.

        :param thin: The thinning interval used in the simulation. The
        number of mcmc iterations must be divisible by this value.

        :param beta_start: Starting values for beta parameters. This
        can either be a scalar or a p-length vector.

        :param Vrho_start: Positive scalar indicating the starting
        value for the variance of the spatial random effects.

        :param mubeta: Means of the priors for the beta parameters of the
        suitability process. mubeta must be either a scalar or a
        p-length vector. If mubeta takes a scalar value, then that
        value will serve as the prior mean for all of the betas. The
        default value is set to 0 for an uninformative prior.

        :param Vbeta: Variances of the Normal priors for the beta
        parameters of the suitability process. Vbeta must be either a
        scalar or a p-length vector. If Vbeta takes a scalar value,
        then that value will serve as the prior variance for all of
        the betas. The default variance is large and set to 1000 for
        an uninformative flat prior.

        :param priorVrho: Type of prior for the variance of the
        spatial random effects. Can be set to a fixed positive scalar,
        or to an inverse-gamma distribution ("1/Gamma") with
        parameters shape and rate, or to a uniform distribution
        ("Uniform") on the interval [0,Vrho.max]. Default set to
        "1/Gamma".

        :param shape: The shape parameter for the Gamma prior on the
        precision of the spatial random effects. Default value is
        shape=0.5 for uninformative prior.

        :param rate: The rate (1/scale) parameter for the Gamma prior
        on the precision of the spatial random effects. Default value
        is rate=0.0005 for uninformative prior.

        :param Vrho_max: Upper bound for the uniform prior of the
        spatial random effect variance. Default set to 10.

        :param seed: The seed for the random number generator. Default
        set to 1234.

        :param verbose: A switch (0,1) which determines whether or not
        the progress of the sampler is printed to the screen. Default
        is 1: a progress bar is printed, indicating the step (in %)
        reached by the Gibbs sampler.

        :param save_rho: A switch (0,1) which determines whether or
        not the sampled values for rhos are saved. Default is 0: the
        posterior mean is computed and returned in the rho.pred
        vector. Be careful, setting save.rho to 1 might require a
        large amount of memory.

        :param save_p: A switch (0,1) which determines whether or not
        the sampled values for predictions are saved. Default is 0:
        the posterior mean is computed and returned in the theta.pred
        vector. Be careful, setting save.p to 1 might require a large
        amount of memory.

        :return: An object of class model_binomial_iCAR.

        """

        # ====================
        # Model specifications
        # ====================

        self.model_type = "binomial_iCAR"
        self.suitability_formula = suitability_formula
        self.data = data
        self.n_neighbors = n_neighbors
        self.neighbors = neighbors
        self.NA_action = NA_action
        self.data_pred = data_pred
        self.eval_env = eval_env
        self.burnin = burnin
        self.mcmc = mcmc
        self.thin = thin
        self.beta_start = beta_start
        self.Vrho_start = Vrho_start
        self.mubeta = mubeta
        self.Vbeta = Vbeta
        self.priorVrho = priorVrho
        self.shape = shape
        self.rate = rate
        self.Vrho_max = Vrho_max
        self.seed = seed
        self.verbose = verbose
        self.save_rho = save_rho
        self.save_p = save_p

        # ========
        # Form response, covariate matrices and model parameters
        # ========

        # Patsy
        eval_env = EvalEnvironment.capture(eval_env, reference=1)
        y, x = dmatrices(suitability_formula, data,
                         eval_env, NA_action)
        self._y_design_info = y.design_info
        self._x_design_info = x.design_info

        # Response
        Y = y[:, 0]
        nobs = len(Y)
        T = y[:, 1]
        # Suitability
        X_arr = x[:, :-1]  # We remove the last column (cells)
        ncol_X = X_arr.shape[1]
        X = X_arr.flatten("F")  # Flatten X by column (R/Fortran style)
        # Spatial correlation
        ncell = len(n_neighbors)
        cells = x[:, -1]  # Last column of x
        # Predictions
        if (data_pred is None):
            X_pred = X
            cells_pred = cells
            npred = nobs
        if (data_pred is not None):
            (x_pred,) = build_design_matrices([self._x_design_info],
                                              data_pred)
            X_pred = x_pred[:, :-1]
            X_pred = X_pred.flatten("F")  # Flatten X_pred
            cells_pred = x_pred[:, -1]
            npred = len(cells_pred)
        # Model parameters
        npar = ncol_X
        ngibbs = mcmc + burnin
        nthin = thin
        nburn = burnin
        nsamp = mcmc // thin

        # ========
        # Initial starting values for M-H
        # ========

        if (np.size(beta_start) == 1 and beta_start == -99):
            # Use starting coefficient from logistic regression
            print("Using estimates from classic logistic regression as"
                  " starting values for betas")
            mod_LR = LogisticRegression(solver="lbfgs")
            mod_LR = mod_LR.fit(X_arr, Y)
            beta_start = np.ravel(mod_LR.coef_)
        if (np.size(beta_start) == 1 and beta_start != -99):
            beta_start = np.ones(npar) * beta_start
        else:
            beta_start = beta_start
        rho_start = np.zeros(ncell)  # Set to zero
        Vrho_start = Vrho_start

        # ========
        # Form and check priors
        # ========
        if (np.size(mubeta) == 1):
            mubeta = np.ones(npar) * mubeta
        else:
            mubeta = mubeta
        if (np.size(Vbeta) == 1):
            Vbeta = np.ones(npar) * Vbeta
        else:
            Vbeta = Vbeta
        shape = shape
        rate = rate
        Vrho_max = Vrho_max
        priorVrho = priorVrho

        # ========
        # call C code to draw sample
        # ========

        Sample = hbm.binomial_iCAR(
            # Constants and data
            ngibbs=int(ngibbs),
            nthin=int(nthin),
            nburn=int(nburn),
            nobs=int(nobs),
            ncell=int(ncell),
            np=int(npar),
            Y_obj=Y.astype(np.int32),
            T_obj=T.astype(np.int32),
            X_obj=X.astype(np.float64),  # X must be flattened.
            # Spatial correlation
            C_obj=cells.astype(np.int32),  # Must start at 0 for C.
            nNeigh_obj=n_neighbors.astype(np.int32),
            Neigh_obj=neighbors.astype(np.int32),  # Must start at 0 for C.
            # Predictions
            npred=int(npred),
            X_pred_obj=X_pred.astype(np.float64),
            C_pred_obj=cells_pred.astype(np.int32),
            # Starting values for M-H
            beta_start_obj=beta_start.astype(np.float64),
            rho_start_obj=rho_start.astype(np.float64),
            Vrho_start=float(Vrho_start),
            # Defining priors
            mubeta_obj=mubeta.astype(np.float64),
            Vbeta_obj=Vbeta.astype(np.float64),
            priorVrho=float(priorVrho),
            shape=float(shape),
            rate=float(rate),
            Vrho_max=float(Vrho_max),
            # Seed
            seed=int(seed),
            # Verbose
            verbose=int(verbose),
            # Save rho and p
            save_rho=int(save_rho),
            save_p=int(save_p))

        # Array of MCMC samples
        MCMC = np.zeros(shape=(nsamp, npar + 2))
        MCMC[:, :npar] = np.array(Sample[0]).reshape(npar, nsamp).transpose()
        MCMC[:, npar] = Sample[2]
        MCMC[:, npar + 1] = Sample[3]
        self.mcmc = MCMC
        posterior_means = np.mean(MCMC, axis=0)
        self.betas = posterior_means[:-2]
        self.Vrho = posterior_means[-2]
        self.deviance = posterior_means[-1]

        # Save rho
        if (save_rho == 0):
            self.rho = np.array(Sample[1])
        if (save_rho == 1):
            self.rho = np.array(Sample[1]).reshape(ncell, nsamp).transpose()

        # Save pred
        if (save_p == 0):
            self.theta_pred = np.array(Sample[5])
        if (save_p == 1):
            self.theta_pred = np.array(
                Sample[5]).reshape(npred, nsamp).transpose()

        # theta_latent
        self.theta_latent = np.array(Sample[4])

    def __repr__(self):
        """Summary of model_binomial_iCAR model.

        This function returns a summary of a model_binomial_iCAR model
        with posterior mean parameter estimates, standard-deviation
        and credible intervals at 95%. It also provides the deviance
        estimate for model comparison.
        """

        summary = ("Binomial logistic regression with iCAR process\n"
                   "  Model: %s ~ %s\n"
                   "  Posteriors:\n"
                   % (self._y_design_info.describe(),
                      self._x_design_info.describe()))
        # Varnames
        varnames = self._x_design_info.column_names[:-1]
        varnames = np.concatenate((varnames, ["Vrho", "Deviance"]))
        nvar = len(varnames)
        name_width = max(len(x) for x in varnames)
        # Posteriors
        MCMC = self.mcmc
        post_mean = np.mean(MCMC, axis=0)
        post_std = np.std(MCMC, axis=0)
        CI_low = np.percentile(MCMC, 2.5, axis=0)
        CI_high = np.percentile(MCMC, 97.5, axis=0)
        # Titles
        summary += ("%" + str(name_width) +
                    "s %10s %10s %10s %10s\n") % ("", "Mean", "Std",
                                                  "CI_low", "CI_high")
        # Loop on varnames
        for i in range(nvar):
            summary += ("%" + str(name_width) +
                        "s %10.3g %10.3g %10.3g %10.3g\n") % (varnames[i],
                                                              post_mean[i],
                                                              post_std[i],
                                                              CI_low[i],
                                                              CI_high[i])
        return summary

    def predict(self, new_data=None):
        """Function returning the predictions of a model_binomial_iCAR model.

        Function to return the predictions of a model_binomial_iCAR model
        for a new data-set.

        :param model: model_binomial_iCAR to predict from.
        :param new_data: A dict-like object which will be used to look \
        up data (including explicative variables and cell values).

        :return: Predictions (probabilities).

        """

        # Data
        if (new_data is None):
            (new_x,) = build_design_matrices([self._x_design_info],
                                             self.data)
        else:
            (new_x,) = build_design_matrices([self._x_design_info],
                                             new_data)
        X = new_x[:, :-1]
        cell = new_x[:, -1].astype(np.int)

        # Rho
        if (len(self.rho.shape) == 1):
            rho = self.rho[cell]
        else:
            rho = np.mean(self.rho, axis=0)[cell]
        return invlogit(np.dot(X, self.betas) + rho)

    def plot(self, output_file="mcmc.pdf", plots_per_page=5,
             figsize=(8.27, 11.69), dpi=100):
        """Plot traces and posterior distributions.

        This function plots the traces and posterior distributions of
        the parameters of a model_binomial_iCAR model.

        :param output_file: Name of the plot file.
        :param plots_per_page: Number of plots (lines) per page.
        :param figsize: Figure size in inches.
        :param dpi: Resolution for output image.

        :return: List of Matplotlib figures.

        """

        # Message
        print("Traces and posteriors will be plotted in " + output_file)
        # Varnames
        varnames = self._x_design_info.column_names[:-1]
        varnames = np.concatenate((varnames, ["Vrho", "Deviance"]))
        # Posterior means
        MCMC = self.mcmc
        posterior_means = np.mean(MCMC, axis=0)
        # The PDF document
        pdf_pages = PdfPages(output_file)
        # Generate the pages
        nb_plots = len(varnames)
        grid_size = (plots_per_page, 2)
        # List of figures to be returned
        figures = []
        # Loop on parameters
        for i in range(nb_plots):
            # Create a figure instance (ie. a new page) if needed
            if i % plots_per_page == 0:
                fig = plt.figure(figsize=figsize, dpi=dpi)
            # Trace
            ax = plt.subplot2grid(grid_size, (i % plots_per_page, 0))
            plt.axhline(y=posterior_means[i], linewidth=1, color="r")
            plt.plot(MCMC[:, i], color="#000000")
            plt.text(0, 1, varnames[i],
                     horizontalalignment="left",
                     verticalalignment="bottom", fontsize=11,
                     transform=ax.transAxes)
            # Posterior distribution
            plt.subplot2grid(grid_size, (i % plots_per_page, 1))
            plt.hist(MCMC[:, i], density=1, bins=20, color="#808080")
            plt.axvline(x=posterior_means[i], linewidth=1, color="r")
            # Close the page if needed
            if (i + 1) % plots_per_page == 0 or (i + 1) == nb_plots:
                plt.tight_layout()
                figures.append(fig)
                pdf_pages.savefig(fig)
        # Write the PDF document to the disk
        pdf_pages.close()
        return figures

# End
