# -*- coding: utf-8 -*-

# ================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3.6
# license         :GPLv3
# ================================================================

"""
Short icar model class for predictions.
"""


class icarModelPred():
    """Short icar model class for predictions."""

    def __init__(
            self,
            formula,
            _y_design_info,
            _x_design_info,
            betas,
            rho
    ):
        """Create the model object using the model's main characteristics.

        :param formula: formula used to fit the model.
        :param _y_design_info: Design info for response variable y.
        :param _x_design_info: Design info for X matrix.
        :param beta: beta parameter values.
        :param rho: rho parameter values.

        """

        self.formula = formula
        self._y_design_info = _y_design_info
        self._x_design_info = _x_design_info
        self.betas = betas
        self.rho = rho

    def __repr__(self):
        """Summary of model_binomial_iCAR model."""
        summary = (
            "Binomial logistic regression with iCAR process\n"
            "  Model: %s ~ %s\n"
            % (self._y_design_info.describe(), self._x_design_info.describe())
        )
        return summary


# End
