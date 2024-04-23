"""Processing forest data."""

import subprocess
from glob import glob

from osgeo import gdal

from .compute_distance import compute_distance


def compute_forest(iso, proj, extent, verbose=False):
    """Processing forest data.

    :param iso: Country iso code.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Used for reprojecting data.

    :param extent: Extent (xmin, ymin, xmax, ymax) of output rasters.

    :param verbose: Logical. Whether to print messages or not. Default
        to ``False``.
    """

    # Callback
    cback = gdal.TermProgress if verbose else 0

    # Creation options
    copts = ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"]

    # Build vrt file
    tif_forest_files = glob("forest_" + iso + "*.tif")
    gdal.BuildVRT("forest.vrt", tif_forest_files, callback=cback)

    # Reproject
    param = gdal.WarpOptions(
        options=["overwrite"],
        srcSRS="EPSG:4326",
        dstSRS=proj,
        outputBounds=extent,
        targetAlignedPixels=True,
        resampleAlg=gdal.GRA_NearestNeighbour,
        xRes=30,
        yRes=30,
        creationOptions=copts,
        callback=cback,
    )
    gdal.Warp("forest_src.tif", "forest.vrt", options=param)

    # Separate bands
    gdal.Translate("forest_t1_src.tif", "forest_src.tif",
                   maskBand=None,
                   bandList=[1], creationOptions=copts,
                   callback=cback)
    gdal.Translate("forest_t2_src.tif", "forest_src.tif",
                   maskBand=None,
                   bandList=[3], creationOptions=copts,
                   callback=cback)
    gdal.Translate("forest_t3_src.tif", "forest_src.tif",
                   maskBand=None,
                   bandList=[5], creationOptions=copts,
                   callback=cback)
    gdal.Translate("forest_2005_src.tif", "forest_src.tif",
                   maskBand=None,
                   bandList=[2], creationOptions=copts,
                   callback=cback)
    gdal.Translate("forest_2015_src.tif", "forest_src.tif",
                   maskBand=None,
                   bandList=[4], creationOptions=copts,
                   callback=cback)

    # Rasterize country border
    # (by default: zero outside, without nodata value)
    gdal.Rasterize("ctry_PROJ.tif", "ctry_PROJ.shp",
                   outputBounds=extent,
                   xRes=30, yRes=30, targetAlignedPixels=True,
                   burnValues=[1], outputType=gdal.GDT_Byte,
                   creationOptions=copts, callback=cback)

    # Compute distance to forest edge at t1 for modelling
    compute_distance("forest_t1_src.tif", "dist_edge_t1.tif",
                     values=0, nodata=0, verbose=verbose)

    # Compute distance to forest edge at t2 for validating
    compute_distance("forest_t2_src.tif", "dist_edge_t2.tif",
                     values=0, nodata=0, verbose=verbose)

    # Compute distance to forest edge at t3 for forecasting
    compute_distance("forest_t3_src.tif", "dist_edge_t3.tif",
                     values=0, nodata=0, verbose=verbose)

    # Compute fcc12_src.tif
    cmd_str = (
        'gdal_calc.py --overwrite '
        '-A {0} -B {1} '
        '--outfile={2} --type=Byte '
        '--calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" '
        '--co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=255 --quiet')
    rast_a = "forest_t1_src.tif"
    rast_b = "forest_t2_src.tif"
    rast_out = "fcc12_src.tif"
    cmd = cmd_str.format(rast_a, rast_b, rast_out)
    subprocess.run(cmd, shell=True, check=True,
                   capture_output=False)

    # Compute distance to past deforestation at t2 for modelling
    compute_distance("fcc12_src.tif", "dist_defor_t2.tif",
                     values=0, nodata=0, input_nodata=True,
                     verbose=verbose)

    # Compute fcc23_src.tif
    rast_a = "forest_t2_src.tif"
    rast_b = "forest_t3_src.tif"
    rast_out = "fcc23_src.tif"
    cmd = cmd_str.format(rast_a, rast_b, rast_out)
    subprocess.run(cmd, shell=True, check=True,
                   capture_output=False)

    # Compute distance to past deforestation at t3 for forecasting
    compute_distance("fcc23_src.tif", "dist_defor_t3.tif",
                     values=0, nodata=0, input_nodata=True,
                     verbose=verbose)

    # Mask forest rasters with country border
    rast_in = [
        "forest_t1_src.tif", "forest_t2_src.tif",
        "forest_t3_src.tif", "forest_2005_src.tif",
        "forest_2015_src.tif"
    ]
    rast_out = [
        "forest_t1.tif", "forest_t2.tif",
        "forest_t3.tif", "forest_2005.tif",
        "forest_2015.tif"
    ]
    cmd_str = (
        'gdal_calc.py --overwrite '
        '-A {0} -B ctry_PROJ.tif '
        '--outfile={1} --type=Byte '
        '--calc="A*B" '
        '--co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--quiet'
    )
    for (i, j) in zip(rast_in, rast_out):
        cmd = cmd_str.format(i, j)
        subprocess.run(cmd, shell=True, check=True,
                       capture_output=False)

    # Mask fcc12 and fcc23 with country border
    rast_in = ["fcc12_src.tif", "fcc23_src.tif"]
    rast_out = ["fcc12.tif", "fcc23.tif"]
    cmd_str = (
        'gdal_calc.py --overwrite '
        '-A {0} -B ctry_PROJ.tif '
        '--outfile={1} --type=Byte '
        '--calc={2} '
        '--co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=255 --quiet'
    )
    calc_expr = '"255-254*(A==1)*(B==1)-255*(A==0)*(B==1)"'
    for (i, j) in zip(rast_in, rast_out):
        cmd = cmd_str.format(i, j, calc_expr)
        subprocess.run(cmd, shell=True, check=True,
                       capture_output=False)

    # Create raster fcc123.tif
    # (0: nodata, 1: for2000, 2: for2010, 3: for2020)
    cmd = (
        'gdal_calc.py --overwrite '
        '-A forest_t1.tif -B forest_t2.tif -C forest_t3.tif '
        '--outfile=fcc123.tif --type=Byte '
        '--calc="A+B+C" '
        '--co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=0 --quiet'
    )
    subprocess.run(cmd, shell=True, check=True,
                   capture_output=False)

    # Create raster fcc12345.tif
    # (0: nodata, 1: for2000, 2: for2005,
    # 3: for2010, 4: for2015, 5: for2020)
    cmd = (
        'gdal_calc.py --overwrite '
        '-A forest_t1.tif -B forest_2005.tif -C forest_t2.tif '
        '-D forest_2015.tif -E forest_t3.tif '
        '--outfile=fcc12345.tif --type=Byte '
        '--calc="A+B+C+D+E" '
        '--co "COMPRESS=LZW" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=0 --quiet'
    )
    subprocess.run(cmd, shell=True, check=True,
                   capture_output=False)


# End
