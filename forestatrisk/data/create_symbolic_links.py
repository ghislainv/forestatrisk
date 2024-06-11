"""Create symbolic links."""

import os

from ..misc import make_dir

opj = os.path.join


def create_symlinks(data_dir, new_dir, iforest, oforest):
    """Create symlinks."""
    make_dir(new_dir)
    variables = ["dist_river.tif", "dist_road.tif", "dist_town.tif",
                 "pa.tif", "altitude.tif", "slope.tif"]
    irasters = variables + iforest
    orasters = variables + oforest
    for (ri, ro) in zip(irasters, orasters):
        src_file = os.path.abspath(opj(data_dir, ri))
        if os.path.isfile(src_file):
            dst_file = opj(new_dir, ro)
            if os.path.isfile(dst_file):
                os.remove(dst_file)
            os.symlink(src_file, dst_file)


def create_symbolic_links(data_dir):
    """Create symbolic links.

    The following four folders will be created and only include
    symlinks to avoid duplicating data:

    1. ``data_calibration``: data used for model calibration on the
       calibration period (t1--t2)
    2. ``data_validation``: data used to predict the deforestation risk at
       t2 and validate models on the validation period (t2--t3)
    3. ``data_historical``: data used for model calibration on the
       historical period (t1--t3)
    4. ``data_forecast``: data used to predict the deforestation risk at
       t3 and forecast deforestation beyond t3.

    :param data_dir: Path to data directory.

    """
    # Data calibration
    iforest = ["fcc12.tif", "dist_edge_t1.tif", "dist_defor_t1.tif"]
    oforest = ["fcc.tif", "dist_edge.tif", "dist_defor.tif"]
    create_symlinks(data_dir, "data_calibration", iforest, oforest)
    # Data validation
    iforest = ["dist_edge_t2.tif", "dist_defor_t2.tif"]
    oforest = ["dist_edge.tif", "dist_defor.tif"]
    create_symlinks(data_dir, "data_validation", iforest, oforest)
    # Data historical
    iforest = ["fcc13.tif", "dist_edge_t1.tif", "dist_defor_t1.tif"]
    oforest = ["fcc.tif", "dist_edge.tif", "dist_defor.tif"]
    create_symlinks(data_dir, "data_historical", iforest, oforest)
    # Data forecast
    iforest = ["dist_edge_t3.tif", "dist_defor_t3.tif"]
    oforest = ["dist_edge.tif", "dist_defor.tif"]
    create_symlinks(data_dir, "data_forecast", iforest, oforest)


# End
