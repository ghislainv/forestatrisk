#!/usr/bin/env python
# -*- coding: utf-8 -*-

# =====================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# =====================================================================

from osgeo import gdal


def compute_distance(input_file, dist_file, values=0, verbose=True):
    """Computing the shortest distance to pixels with given values in
    a raster file.

    This function computes the shortest distance to pixels with given
    values in a raster file. Distances generated are in georeferenced
    coordinates.

    :param input_file: Input raster file.

    :param dist_file: Path to the distance raster file that is
        created.

    :param values: Values of the raster to compute the distance to. If
        several values, they must be separated with a comma in a
        string (eg. '0,1'). Default to 0.

    :param verbose: Logical. Whether to print messages or not. Default
        to ``True``.

    :return: None. A distance raster file is created (see
        ``dist_file``). Raster data type is UInt32 ([0,
        4294967295]). NoData is set to 4294967295.

    """

    # Read input file
    src_ds = gdal.Open(input_file)
    srcband = src_ds.GetRasterBand(1)

    # Create raster of distance
    drv = gdal.GetDriverByName("GTiff")
    dst_ds = drv.Create(
        dist_file,
        src_ds.RasterXSize,
        src_ds.RasterYSize,
        1,
        gdal.GDT_UInt32,
        ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"],
    )
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())
    dst_ds.SetProjection(src_ds.GetProjectionRef())
    dstband = dst_ds.GetRasterBand(1)

    # Compute distance
    val = "VALUES=" + str(values)
    cb = gdal.TermProgress if verbose else 0
    gdal.ComputeProximity(srcband, dstband, [val, "DISTUNITS=GEO"], callback=cb)

    # Set nodata value
    dstband.SetNoDataValue(4294967295)

    # Delete objects
    srcband = None
    dstband = None
    del src_ds, dst_ds


# End
