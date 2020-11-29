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

# Third party imports
import numpy as np
from patsy import dmatrices, build_design_matrices, EvalEnvironment
from sklearn.ensemble import RandomForestClassifier


# model_random_forest
class model_random_forest(object):

    """model_random_forest class.

    Fit a random forest model (see
    ``sklearn.ensemble.RandomForestClassifier``\\ ) using a patsy formula
    for explanatory variables.

    """

    def __init__(self,  # Observations
                 formula, data,
                 # NA action
                 NA_action="drop",
                 # Environment
                 eval_env=0,
                 # Number of cores
                 n_estimators=500,
                 n_jobs=1,
                 **kwargs):
        """Function to fit a random forest model.

        The function fits a random forest model using patsy formula.
        """

        # Model specifications
        self.model_type = "random_forest"
        self.formula = formula
        self.data = data

        # Patsy
        eval_env = EvalEnvironment.capture(eval_env, reference=1)
        y, x = dmatrices(formula, data,
                         eval_env, NA_action)
        self._y_design_info = y.design_info
        self._x_design_info = x.design_info

        # Create and train Random Forest
        rf = RandomForestClassifier(n_estimators=n_estimators,
                                    n_jobs=n_jobs,
                                    **kwargs)
        rf.fit(x, y)
        self.rf = rf

    def predict(self, new_data=None, **kwargs):
        """Function returning the predictions of a model_random_forest model.

        Function to return the predictions of a model_random_forest model
        for a new data-set.

        :param model: model_random_forest to predict from.
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

        # Predictions
        rf_pred = np.array(self.rf.predict_proba(new_x, **kwargs)[:, 1])
        return(rf_pred)

# End
