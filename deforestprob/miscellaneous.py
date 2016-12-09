#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# ==============================================================================

# Import
import numpy as np
import matplotlib.pyplot as plt


# Invlogit
def invlogit(x):
    """Compute the inverse-logit of a numpy array.

    We differenciate the positive and negative values to avoid
    under/overflow with the use of exp().

    :param x: numpy array.
    :return: return the inverse-logit of the array.

    """

    r = x
    r[x > 0] = 1. / (1. + np.exp(-x[x > 0]))
    r[x <= 0] = np.exp(x[x <= 0]) / (1 + np.exp(x[x <= 0]))
    return (r)


# Rescale
def rescale(value):
    """Rescale probability values to 1-65534.

    This function rescales probability values (float in [0, 1]) to
    integer values in [1, 65534]. Raster data can then be of type
    UInt16 with 0 as nodata value.

    :param value: float value in [0, 1].
    :return: integer value in [1, 65534].

    """

    return (((value - 1) * 65534 / 999999) + 1)


# Saving a matplotlib.pyplot figure as a border-less frame-less image
def figure_as_image(fig, output_file, dpi=300):
    """Remove borders and frames of a Matplotlib figure and save.

    :param fig: Matplotlib figure you want to save as the image.
    :param output_file: path to the output image file.
    :param dpi: dpi of the output image.
    :return: figure without borders and frame.

    """

    fig_size = fig.get_size_inches()
    w, h = fig_size[0], fig_size[1]
    fig.patch.set_alpha(0)
    a = fig.gca()
    a.set_frame_on(False)
    a.set_xticks([])
    a.set_yticks([])
    plt.axis("off")
    plt.xlim(0, h)
    plt.ylim(w, 0)
    fig.savefig(output_file, transparent=True, bbox_inches="tight",
                pad_inches=0, dpi=dpi)
    return(fig)

# End
