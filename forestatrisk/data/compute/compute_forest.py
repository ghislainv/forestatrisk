"""Processing forest data."""

import subprocess

from osgeo import gdal

from .compute_distance import compute_distance


def compute_forest(proj, extent, verbose=False):
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
    copts = ["COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"]

    # Reproject
    param = gdal.WarpOptions(
        warpOptions=["overwrite"],
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

    # Number of bands (or years)
    with gdal.Open("forest_src.tif") as ds:
        nbands = ds.RasterCount

    # Index offset if band == 3
    k = 1 if nbands == 3 else 0

    # Separate bands
    for i in range(nbands):
        gdal.Translate(f"forest_t{i + k}_src.tif", "forest_src.tif",
                       maskBand=None,
                       bandList=[i + 1], creationOptions=copts,
                       callback=cback)

    # Rasterize country border
    # (by default: zero outside, without nodata value)
    gdal.Rasterize("aoi_proj.tif", "aoi_proj.gpkg",
                   layers="aoi",
                   outputBounds=extent,
                   xRes=30, yRes=30, targetAlignedPixels=True,
                   burnValues=[1], outputType=gdal.GDT_Byte,
                   creationOptions=copts, callback=cback)

    # Compute distance to forest edge at t1, t2, and t3
    # for modelling, validating, and forecasting, respectively
    for i in range(3):
        compute_distance(f"forest_t{i + 1}_src.tif",
                         f"dist_edge_t{i + 1}.tif",
                         values=0, nodata=0,
                         input_nodata=True,
                         verbose=verbose)

    # Compute fcc
    # Command to compute fcc
    cmd_str = (
        'gdal_calc.py --overwrite '
        '-A {0} -B {1} '
        '--outfile={2} --type=Byte '
        '--calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" '
        '--co "COMPRESS=DEFLATE" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=255 --quiet')
    # Loop on bands
    for i in range(nbands - 1):
        # Compute fcc{i}{i + 1}_src.tif
        rast_a = f"forest_t{i + k}_src.tif"
        rast_b = f"forest_t{i + 1 + k}_src.tif"
        fcc_out = f"fcc{i + k}{i + 1 + k}_src.tif"
        cmd = cmd_str.format(rast_a, rast_b, fcc_out)
        subprocess.run(cmd, shell=True, check=True,
                       capture_output=False)

    # Compute distance to past deforestation only if 4 bands
    if nbands == 4:
        for i in range(nbands - 1):
            # Compute distance to past deforestation at t1, t2, and t3
            fcc_in = f"fcc{i + k}{i + 1 + k}_src.tif"
            dist_out = f"dist_defor_t{i + 1}.tif"
            compute_distance(fcc_in, dist_out,
                             values=0, nodata=0,
                             input_nodata=True,
                             verbose=verbose)

    # Mask forest rasters with country border
    rast_in = [f"forest_t{i + k}_src.tif" for i in range(nbands)]
    rast_out = [f"forest_t{i + k}.tif" for i in range(nbands)]
    cmd_str = (
        'gdal_calc.py --overwrite '
        '-A {0} -B aoi_proj.tif '
        '--outfile={1} --type=Byte '
        '--calc="A*B" '
        '--co "COMPRESS=DEFLATE" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--quiet'
    )
    for (i, j) in zip(rast_in, rast_out):
        cmd = cmd_str.format(i, j)
        subprocess.run(cmd, shell=True, check=True,
                       capture_output=False)

    # Mask fcc with country border
    rast_in = [f"fcc{i + k}{i + k + 1}_src.tif" for i in range(nbands - 1)]
    rast_out = [f"fcc{i + k}{i + k + 1}.tif" for i in range(nbands - 1)]
    cmd_str = (
        'gdal_calc.py --overwrite '
        '-A {0} -B aoi_proj.tif '
        '--outfile={1} --type=Byte '
        '--calc={2} '
        '--co "COMPRESS=DEFLATE" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=255 --quiet'
    )
    calc_expr = '"255-254*(A==1)*(B==1)-255*(A==0)*(B==1)"'
    for (i, j) in zip(rast_in, rast_out):
        cmd = cmd_str.format(i, j, calc_expr)
        subprocess.run(cmd, shell=True, check=True,
                       capture_output=False)

    # Compute raster fcc13.tif for forecast (no need to crop with borders)
    cmd_str = (
        'gdal_calc.py --overwrite '
        '-A {0} -B {1} '
        '--outfile={2} --type=Byte '
        '--calc="255-254*(A==1)*(B==1)-255*(A==1)*(B==0)" '
        '--co "COMPRESS=DEFLATE" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=255 --quiet')
    rast_a = "forest_t1.tif"
    rast_b = "forest_t3.tif"
    fcc_out = "fcc13.tif"
    cmd = cmd_str.format(rast_a, rast_b, fcc_out)
    subprocess.run(cmd, shell=True, check=True,
                   capture_output=False)

    # Compute raster fcc123.tif
    # (0: nodata, 1: t1, 2: t2, 3: t3)
    cmd = (
        'gdal_calc.py --overwrite '
        '-A forest_t1.tif -B forest_t2.tif -C forest_t3.tif '
        '--outfile=fcc123.tif --type=Byte '
        '--calc="A+B+C" '
        '--co "COMPRESS=DEFLATE" --co "PREDICTOR=2" --co "BIGTIFF=YES" '
        '--NoDataValue=0 --quiet'
    )
    subprocess.run(cmd, shell=True, check=True,
                   capture_output=False)

# End
