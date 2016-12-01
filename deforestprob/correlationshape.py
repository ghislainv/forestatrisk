#!/usr/bin/python

# ============================================================================
#
# correlationshape.py
#
# Function to plot:
# - the histogram of the explicative variables
# - the probability of deforestation by bins of equal number of observations
#   for each explicative variable
#
# Ghislain Vieilledent <ghislain.vieilledent@cirad.fr>
# November 2016
#
# call: correlationshape(y, data, plots_per_page=4, output_dir="output",
#                        output_file="correlationshape.pdf")
# - y: the array of response variable (forest=1, defor=0)
# - data: a pandas DataFrame with column names
# - plots_per_page: number of plots (lines) per page
# - output_dir: relative path of the directory for outputs
# - output_file: name of output file with extension
#
# ============================================================================

# =============================================
# Libraries
# =============================================

import numpy as np
import os
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# =============================================
# Function
# =============================================


# Function to make a directory
def make_dir(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)

# =============================================
# correlationshape
# =============================================


def correlationshape(y, data, plots_per_page=4, output_dir="output",
                     output_file="correlationshape.pdf"):
    # Data
    y = 1-y  # Transform: defor=1, forest=0
    perc = np.arange(0, 110, 10)
    nperc = len(perc)
    colnames = data.columns.values
    # The PDF document
    make_dir(output_dir)
    save_file = os.path.join(output_dir, output_file)
    pdf_pages = PdfPages(save_file)
    # Generate the pages
    nb_plots = len(colnames)
    nb_plots_per_page = plots_per_page
    #  nb_pages = int(np.ceil(nb_plots / float(nb_plots_per_page)))
    grid_size = (nb_plots_per_page, 2)
    # Loop on variables
    for i in range(nb_plots):
        # Create a figure instance (ie. a new page) if needed
        if i % nb_plots_per_page == 0:
            fig = plt.figure(figsize=(8.27, 11.69), dpi=100)
        varname = colnames[i]
        theta = np.zeros(nperc-1)
        se = np.zeros(nperc-1)
        x = np.zeros(nperc-1)
        quantiles = np.nanpercentile(data[varname], q=perc)
        # Compute theta and se by bins
        for j in range(nperc-1):
            inf = quantiles[j]
            sup = quantiles[j+1]
            x[j] = inf+(sup-inf)/2
            y_bin = y[(data[varname] > inf) &
                      (data[varname] <= sup)]
            y_bin = np.array(y_bin)  # Transform into np.array to compute sum
            s = float(sum(y_bin == 1))  # success
            n = len(y_bin)  # trials
            if n is not 0:
                theta[j] = s/n
            else:
                theta[j] = np.nan
            ph = (s+1/2)/(n+1)
            se[j] = np.sqrt(ph*(1-ph)/(n+1))
        # Plots
        # Histogram
        plt.subplot2grid(grid_size, (i % nb_plots_per_page, 0))
        Arr = np.array(data[varname])
        Arr = Arr[~np.isnan(Arr)]
        plt.hist(Arr, facecolor="#808080", alpha=0.75)
        plt.xlabel(varname, fontsize=16)
        plt.ylabel("Nb. of observations", fontsize=16)
        # Corelation
        plt.subplot2grid(grid_size, (i % nb_plots_per_page, 1))
        plt.plot(x, theta, color="#000000", marker='o', linestyle='--')
        plt.xlabel(varname, fontsize=16)
        plt.ylabel("Defor. probability", fontsize=16)
        # Close the page if needed
        if (i + 1) % nb_plots_per_page == 0 or (i + 1) == nb_plots:
            plt.tight_layout()
            pdf_pages.savefig(fig)
    # Write the PDF document to the disk
    pdf_pages.close()
    return None

# ============================================================================
# End of correlationshape.py
# ============================================================================
