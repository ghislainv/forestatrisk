"""Check forest cover change raster file."""

import numpy as np
from osgeo import gdal, osr

from ..misc import makeblock, progress_bar


def check_fcc(fcc_file, proj, nbands_min=3, blk_rows=0, verbose=True):
    """Check forest cover change file.

    The forest cover change file should have the following
    characteristics:

    1. It must be a multiple band raster file with each band
       representing the forest cover at one date.
    2. Bands must be ordered (first band for t, second band for t+1,
       etc.).
    3. Raster should only have two values: 1 for forest pixels and 0
       for non-forest pixels (the raster can thus be of type Byte).
    4. The raster file should be projected in the coordinate reference
       system of the project.
    5. The raster must cover at least all the area of the
       jurisdiction.

    We check here conditions 1, 3, and 4. Other conditions must be
    checked by the user.

    :param fcc_file: Forest cover change file.

    :param proj: Project's projection.

    :param nbands_min: Minimal number of bands.

    :param blk_rows: If > 0, number of lines per block.

    :param verbose: Toogle progress bar.

    :return: A dictionary with ``err``: a number (0 if OK, 1 if error)
       and ``err_smg``: an error message.

    """

    # Initialize variables
    err = 0
    err_msg = ("No error detected regarding the "
               "forest cover change file.")

    # Open file
    fcc = gdal.Open(fcc_file)

    # ===========================
    # Check that the file is a raster that can be opened with gdal
    if fcc is None:
        err = 1
        err_msg = ("Forest cover change file is not a raster "
                   "file that can be opened with gdal.")

    # ===========================
    # Check that the file is a multiple band raster file
    nbands = fcc.RasterCount
    if nbands < nbands_min:
        err = 1
        err_msg = ("Forest cover change file must be a "
                   "multiple band raster file with at "
                   f"least {nbands_min} bands.")

    # ===========================
    # Check projection
    proj_fcc = osr.SpatialReference(wkt=fcc.GetProjection())
    proj_fcc = proj_fcc.GetAttrValue("AUTHORITY", 1)
    proj_fcc = f"EPSG:{proj_fcc}"
    if proj_fcc != proj:
        err = 1
        err_msg = ("Forest cover change file projection "
                   f"({proj_fcc}) must be the same "
                   f"as the project ({proj}).")

    # ===========================
    # Check that raster values are in {0, 1}
    # Make blocks
    blockinfo = makeblock(fcc_file, blk_rows=blk_rows)
    nblock = blockinfo[0]
    nblock_x = blockinfo[1]
    x = blockinfo[3]
    y = blockinfo[4]
    nx = blockinfo[5]
    ny = blockinfo[6]
    if verbose:
        text = "Divide region in {} blocks"
        print(text.format(nblock))

    # min and max values
    min_blocks = np.zeros(nblock)
    max_blocks = np.zeros(nblock)

    # Loop on blocks of data
    for b in range(nblock):
        # Progress bar
        if verbose:
            progress_bar(nblock, b + 1)
        # Position in 1D-arrays
        px = b % nblock_x
        py = b // nblock_x
        # Read the data
        forest = fcc.ReadAsArray(x[px], y[py], nx[px], ny[py])
        # Min/max block values
        min_blocks[b] = np.min(forest)
        max_blocks[b] = np.max(forest)

    # Min/max raster values
    min_fcc = np.min(min_blocks)
    max_fcc = np.max(max_blocks)

    # Evaluation
    if (min_fcc not in [0, 1] or max_fcc not in [0, 1]):
        err = 1
        err_msg = ("Forest cover change raster must "
                   "have only two values: 1 for forest "
                   "pixels and 0 for non-forest pixels.")

    # Close
    fcc = None

    # Return
    return {"err": err, "err_msg": err_msg}

# End of file
