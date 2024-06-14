#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=3
# license         :GPLv3
# ==============================================================================

# Standard library imports
import os

# Third party imports
import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal
import pandas as pd

# Local application imports
from ..misc import progress_bar, make_square


# validation_udef_arp
def validation_udef_arp(
        fcc_file,
        time_interval,
        riskmap_file, tab_file_defor,
        period="calibration",
        csize_coarse_grid=300,
        indices_file_pred="indices.csv",
        tab_file_pred="pred_obs.csv",
        fig_file_pred="pred_obs.png",
        figsize=(6.4, 6.4),
        dpi=100, verbose=True):
    """Validation of the deforestation risk map.

    This function computes the observed and predicted deforestion (in
    ha) for either the calibration or validation period. Deforestation
    density estimates (in ha/pixel/yr) obtained with the
    ``defrate_per_cat`` function are used to compute the predicted
    deforestation in each grid cell. The function creates both a
    ``.csv`` file with the validation data and a plot comparing
    predictions vs. observations. The function returns two indices,
    the weighted Root Mean Squared Error (wRMSE, in hectares) and the
    MedAE (Median Absolute Error, in hectares) associated with the
    deforestation predictions.

    :param fcc_file: Input raster file of forest cover change at three
        dates (123). 1: first period deforestation, 2: second period
        deforestation, 3: remaining forest at the end of the second
        period. No data value must be 0 (zero).

    :param period: Either "calibration" (from t1 to t2), "validation"
        (from t2 to t3), or "historical" (from t1 to t3).

    :param time_interval: Duration (in years) of the period.

    :param riskmap_file: Input raster file with categories of
        spatial deforestation risk at the beginning of the period.

    :param tab_file_defor: Path to the ``.csv`` input file with
        estimates of deforestation density (in ha/pixel/yr) for each
        category of deforestation risk.

    :param csize_coarse_grid: Spatial cell size in number of pixels. Must
        correspond to a distance < 10 km. Default to 300 corresponding
        to 9 km for a 30 m resolution raster.

    :param tab_file_pred: Path to the ``.csv`` output file with validation
        data.

    :param fig_file_pred: Path to the ``.png`` output file for the
        predictions vs. observations plot.

    :param figsize: Figure size.

    :param dpi: Resolution for output image.

    :param verbose: Logical. Whether to print messages or not. Default
        to ``True``.

    :return: A dictionary. With ``wRMSE``, ``MedAE``, and ``R2``:
        weighted root mean squared error (in ha), median absolute
        error (in ha), and R-square respectively for the deforestation
        predictions, ``ncell``: the number of grid cells with forest
        cover > 0 at the beginning of the validation period,
        ``csize_coarse_grid``: the coarse grid cell size in number of
        pixels, ``csize_coarse_grid_ha``: the coarse grid cell size in ha.

    """

    # ==============================================================
    # Input data
    # ==============================================================

    # Get fcc raster data
    fcc_ds = gdal.Open(fcc_file)
    fcc_band = fcc_ds.GetRasterBand(1)

    # Get defor_cat raster data
    defor_cat_ds = gdal.Open(riskmap_file)
    defor_cat_band = defor_cat_ds.GetRasterBand(1)

    # Get defor_dens per cat
    defor_dens_per_cat = pd.read_csv(tab_file_defor)
    cat = defor_dens_per_cat["cat"].values

    # Pixel area (in unit square, eg. meter square)
    gt = fcc_ds.GetGeoTransform()
    pix_area = gt[1] * (-gt[5])

    # Make square
    squareinfo = make_square(fcc_file, csize_coarse_grid)
    nsquare = squareinfo[0]
    nsquare_x = squareinfo[1]
    x = squareinfo[3]
    y = squareinfo[4]
    nx = squareinfo[5]
    ny = squareinfo[6]

    # Cell size in ha
    csize_coarse_grid_ha = round(csize_coarse_grid *
                                 csize_coarse_grid *
                                 pix_area / 10000, 2)

    # Create a table to save the results
    data = {"cell": list(range(nsquare)), "nfor_obs": 0,
            "ndefor_obs": 0, "nfor_obs_ha": 0.0,
            "ndefor_obs_ha": 0.0, "ndefor_pred_ha": 0.0}
    df = pd.DataFrame(data)

    # ==============================================================
    # Loop on grid cells
    # ==============================================================

    # Loop on squares
    for s in range(nsquare):
        # Progress bar
        if verbose:
            progress_bar(nsquare, s + 1)
        # Position in 1D-arrays
        px = s % nsquare_x
        py = s // nsquare_x
        # Observed forest cover and deforestation
        fcc_data = fcc_band.ReadAsArray(x[px], y[py], nx[px], ny[py])
        if period == "calibration":
            df.loc[s, "nfor_obs"] = np.sum(fcc_data > 0)
            df.loc[s, "ndefor_obs"] = np.sum(fcc_data == 1)
        elif period == "validation":
            df.loc[s, "nfor_obs"] = np.sum(fcc_data > 1)
            df.loc[s, "ndefor_obs"] = np.sum(fcc_data == 2)
        else:  # historical
            df.loc[s, "nfor_obs"] = np.sum(fcc_data > 0)
            df.loc[s, "ndefor_obs"] = np.sum(np.isin(fcc_data, [1, 2]))

        # Predicted deforestation
        defor_cat_data = defor_cat_band.ReadAsArray(
            x[px], y[py], nx[px], ny[py])
        defor_cat = pd.Categorical(defor_cat_data.flatten(), categories=cat)
        defor_cat_count = defor_cat.value_counts().values

        # Deforestation on period
        defor_dens = defor_dens_per_cat["defor_dens"].values
        defor_dens_period = defor_dens * time_interval
        # Predicted deforestation (area)
        df.loc[s, "ndefor_pred_ha"] = np.nansum(defor_cat_count *
                                                defor_dens_period)
        # Note: np.nansum is used here as some cat might not exist and
        # have nan for defrate.

    # Dereference drivers
    del fcc_ds, defor_cat_ds

    # ==============================================================
    # Indices and plot
    # ==============================================================

    # Select cells with forest cover > 0
    df = df[df["nfor_obs"] > 0]
    ncell = df.shape[0]
    # if ncell < 1000:
    #     msg = ("Number of cells with forest cover > 0 ha is < 1000. "
    #            "Please decrease the spatial cell size 'csize_coarse_grid' "
    #            "to get more cells.")
    #     raise ValueError(msg)

    # Compute areas in ha
    df["nfor_obs_ha"] = df["nfor_obs"] * pix_area / 10000
    df["ndefor_obs_ha"] = df["ndefor_obs"] * pix_area / 10000

    # Export the table of results
    df.to_csv(tab_file_pred, sep=",", header=True,
              index=False, index_label=False)

    # Prediction error
    error_pred = df["ndefor_pred_ha"] - df["ndefor_obs_ha"]

    # Compute RMSE
    squared_error = (error_pred) ** 2
    RMSE = round(np.sqrt(np.mean(squared_error)), 2)

    # Compute wRMSE
    w = df["nfor_obs_ha"] / df["nfor_obs_ha"].sum()
    wRMSE = round(np.sqrt(sum(squared_error * w)), 2)

    # Compute MedAE
    MedAE = round(np.median(np.absolute(error_pred)), 2)

    # Calculate R square
    # Get the correlation coefficient
    r = np.corrcoef(df["ndefor_pred_ha"], df["ndefor_obs_ha"])[0, 1]
    # Square the correlation coefficient
    r_square = round(r ** 2, 2)

    # Identify model from file
    model_basename = os.path.basename(riskmap_file)
    model_name = model_basename[5:-7]

    # Plot title
    title = (
        "{0} model, {1} period\n"
        "Predicted vs. observed deforestation "
        "in {2} ha grid cells."
    )
    title = title.format(model_name, period, csize_coarse_grid_ha)

    # Points for identity line
    p = [df[["ndefor_obs_ha", "ndefor_pred_ha"]].min(axis=None),
         df[["ndefor_obs_ha", "ndefor_pred_ha"]].max(axis=None)]

    # Plot predictions vs. observations
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = plt.subplot(111)
    ax.set_box_aspect(1)
    plt.scatter(df["ndefor_obs_ha"], df["ndefor_pred_ha"],
                color=None, marker="o", edgecolor="k")
    plt.plot(p, p, "r--")
    plt.title(title)
    plt.xlabel("Observed deforestation (ha)")
    plt.ylabel("Predicted deforestation (ha)")
    # Text indices and ncell
    t = ("MedAE = {0:.2f} ha\n"
         "R2 = {1:.2f}\n"
         "n = {2:d}")
    t = t.format(MedAE, r_square, ncell)
    x_text = 0
    y_text = df[["ndefor_obs_ha", "ndefor_pred_ha"]].max(axis=None)
    plt.text(x_text, y_text, t, ha="left", va="top")
    fig.savefig(fig_file_pred)
    plt.close(fig)

    # Results
    indices = {"RMSE": RMSE, "wRMSE": wRMSE, "MedAE": MedAE, "R2":
               r_square, "ncell": ncell, "csize_coarse_grid":
               csize_coarse_grid, "csize_coarse_grid_ha":
               csize_coarse_grid_ha}
    indices_df = pd.DataFrame([indices])
    indices_df.to_csv(indices_file_pred, sep=",", header=True,
                      index=False, index_label=False)

# End
