"""Compute distance to pixel."""

from osgeo import gdal


def compute_distance(input_file, dist_file, values=0,
                     nodata=4294967295, input_nodata=False,
                     verbose=True):
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
        string (eg. '0,1'). Default is 0.

    :param nodata: NoData value for the output raster. Default is
        4294967295 for UInt32.

    :param input_nodata: Whether nodata pixels in the input
        raster should be nodata in the output raster (default to False).

    :param verbose: Logical. Whether to print messages or not. Default
        to ``True``.

    :return: None. A distance raster file is created (see
        ``dist_file``). Raster data type is UInt32 ([0,
        4294967295]).

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
        ["COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"],
    )
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())
    dst_ds.SetProjection(src_ds.GetProjectionRef())
    dstband = dst_ds.GetRasterBand(1)

    # Use_input_nodata
    ui_nodata = "YES" if input_nodata else "NO"

    # Compute distance
    val = "VALUES=" + str(values)
    use_input_nodata = "USE_INPUT_NODATA=" + ui_nodata
    cb = gdal.TermProgress if verbose else 0
    gdal.ComputeProximity(
        srcband,
        dstband,
        [val, use_input_nodata, "DISTUNITS=GEO"],
        callback=cb
    )

    # Set nodata value
    dstband.SetNoDataValue(nodata)

    # Delete objects
    srcband = None
    dstband = None
    del src_ds, dst_ds


# # Test
# import os
# os.chdir("/home/ghislain/deforisk/MTQ_2000_2010_2020_jrc_7221/data_raw/")
# compute_distance(
#     input_file="forest_t1.tif",
#     dist_file="dist_edge_t1_test.tif",
#     values=0,
#     nodata=4294967295,
#     input_nodata=False,
#     verbose=True)

# End
