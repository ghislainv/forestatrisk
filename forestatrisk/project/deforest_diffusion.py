#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

# Third party imports
import numpy as np


# deforest_diffusion
def deforest_diffusion(forest_t0, t0, annual_defor, t):

    """Diffusion of the deforestation between states of a country.

    Diffusion of the deforestation between states of a country. We
    suppose that the deforestation is constant at the country
    level. When a state has no more forest, its deforestation (annual
    area of deforestation) is attributed to the other states of the
    country still having forest. This function can be useful for
    Brazil for example.

    :param forest_t0: Forest area at t0 for each state. Numpy array.
    :param t0: Year at t0.
    :param annual_defor: Annual deforestation for each state. Numpy array.
    :param t: Year at the end of the deforestation period.

    :return: A dictionnary with forest at t0 ("forest_t0"), forest at
        time t ("forest_t") and deforestation between t0 and t
        ("defor_t0_t").

    """

    # Variables
    nctry = len(forest_t0)
    ctry_for = 1 * (forest_t0 > 0)  # Transform in 0,1
    ti = t - t0  # time-interval
    # Defor as np.float (because nfor is of type np.float)
    defor = (annual_defor * ti).astype(np.float)
    nfor = forest_t0

    # While a country has defor > nfor
    while (not np.all(nfor >= defor)):
        excess = 0
        for i in range(nctry):
            # We need to have nfor > defor for each ctry
            if (defor[i] > nfor[i]):  # if nfor[i]=0 and defor[i]=0: nothing
                ctry_for[i] = 0
                # Compute excess of deforestation
                excess = excess + (defor[i] - nfor[i])
                # Set defor to nfor to remove all the forest
                defor[i] = nfor[i]  # Both must be as type np.float
        # Number of countries with forest
        ncf = np.sum(ctry_for == 1)
        # We split the excess of deforestation among countries with forest
        # This can make defor > nfor, thus implying the while loop
        defor[ctry_for == 1] = defor[ctry_for == 1] + excess / ncf

    # Compute new forest cover
    nfor = nfor - defor
    return {"forest_t0": forest_t0, "forest_t": nfor, "defor_t0_t": defor}


# deforest_diffusion_t_nofor
def deforest_diffusion_t_nofor(forest_t0, t0, annual_defor):

    """Compute the number of years until there is no forest in each state
    for of a deforestation with diffusion.

    Compute the number of years until there is no forest in each state
    for of a deforestation with diffusion. When a state has no more
    forest, its deforestation (annual area of deforestation) is
    attributed to the other states of the country still having
    forest. This function can be useful for Brazil for example.

    :param forest_t0: Forest area at t0 for each state. Numpy array.
    :param t0: Year at t0.
    :param annual_defor: Annual deforestation for each state. Numpy array.

    :return: A dictionnary indicating the number of years ("ny"), for
        each state, after which all the forest will have disappeared, and
        the corresponding year ("y", assuming forest_t0 was estimated at
        the beginning of the year).

    """

    # Variables
    nctry = len(forest_t0)
    ctry_for = 1 * (forest_t0 > 0)  # Transform in 0,1
    defor = annual_defor.astype(np.float)  # Here time step of 1 year
    nfor = forest_t0
    ny = np.array([0] * nctry)
    t = 0

    # Process runs while sum(defor) < sum(for)
    while (np.sum(defor) < np.sum(nfor)):

        # While a country has defor > nfor
        while (not np.all(nfor >= defor)):
            excess = 0
            for i in range(nctry):
                # We need to have nfor > defor for each ctry
                # if nfor[i]=0 and defor[i]=0: nothing
                if (defor[i] > nfor[i]):
                    ny[i] = t
                    ctry_for[i] = 0
                    # Compute excess of deforestation
                    excess = excess + (defor[i] - nfor[i])
                    # Set defor to nfor to remove all the forest
                    defor[i] = nfor[i]
            # Number of countries with forest
            ncf = np.sum(ctry_for == 1)
            # We split the excess of deforestation among countries with forest
            # This can make defor > nfor, thus implying the while loop
            defor[ctry_for == 1] = defor[ctry_for == 1] + excess / ncf

        # Compute new forest cover
        nfor = nfor - defor
        # Increment t
        t += 1

    # Process stops when sum(defor) >= sum(for)
    ny[ctry_for == 1] = t

    return {"ny": ny, "year": ny + t0}

# EOF
