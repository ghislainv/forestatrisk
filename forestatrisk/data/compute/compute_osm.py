"""Processing OpenStreetMap data"""

import subprocess

from osgeo import gdal

from .compute_distance import compute_distance


def compute_osm(proj, extent, verbose=False):
    """Compute distance to road, town, and river.

    :param proj: Projection definition (EPSG, PROJ.4, WKT) as in
        GDAL/OGR. Used for reprojecting data.

    :param extent: Extent (xmin, ymin, xmax, ymax) of output rasters.

    :param verbose: Logical. Whether to print messages or not. Default
        to ``False``.

    """

    # Convert osm.pbf to o5m
    cmd = "osmconvert country.osm.pbf -o=country.o5m"
    rtn = subprocess.run(cmd, shell=True,
                         check=True,
                         capture_output=True,
                         text=True)
    if verbose:
        print(rtn.stdout)

    # Filter data
    # Roads
    cmd = ('osmfilter country.o5m '
           '--keep="highway=motorway '
           'or highway=trunk or highway=*ary" '
           '-o=roads.osm')
    rtn = subprocess.run(cmd, shell=True,
                         check=True,
                         capture_output=True,
                         text=True)
    if verbose:
        print(rtn.stdout)
    # Towns
    cmd = ('osmfilter country.o5m '
           '--keep="place=city or '
           'place=town or place=village" '
           '-o=towns.osm')
    rtn = subprocess.run(cmd, shell=True,
                         check=True,
                         capture_output=True,
                         text=True)
    if verbose:
        print(rtn.stdout)
    # Rivers
    cmd = ('osmfilter country.o5m '
           '--keep="waterway=river or '
           'waterway=canal" '
           '-o=rivers.osm')
    rtn = subprocess.run(cmd, shell=True,
                         check=True,
                         capture_output=True,
                         text=True)
    if verbose:
        print(rtn.stdout)

    # Callback
    cback = gdal.TermProgress if verbose else 0

    # Creation options
    copts = ["COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"]

    # Useful lists
    line_cat = ["roads", "towns", "rivers"]
    sql_statement = [
        ("SELECT osm_id, name, highway FROM lines "
         "WHERE highway IS NOT NULL"),
        ("SELECT osm_id, name, place FROM points "
         "WHERE place IS NOT NULL"),
        ("SELECT osm_id, name, waterway FROM lines "
         "WHERE waterway IS NOT NULL"),
    ]

    # Loop on line categories
    for (i, cat) in enumerate(line_cat):
        # Convert to shapefile
        param = gdal.VectorTranslateOptions(
            accessMode="overwrite",
            skipFailures=True,
            format="ESRI Shapefile",
            layerCreationOptions=["ENCODING=UTF-8"],
            SQLStatement=sql_statement[i],
            callback=cback,
        )
        gdal.VectorTranslate(cat + ".shp", cat + ".osm", options=param)
        # Reproject
        param = gdal.VectorTranslateOptions(
            accessMode="overwrite",
            format="ESRI Shapefile",
            layerCreationOptions=["ENCODING=UTF-8"],
            srcSRS="EPSG:4326",
            dstSRS=proj,
            callback=cback,
        )
        gdal.VectorTranslate(cat + "_proj.shp", cat + ".shp", options=param)
        # Rasterize
        param = gdal.RasterizeOptions(
            outputBounds=extent,
            targetAlignedPixels=True,
            burnValues=[1],
            outputSRS=proj,
            noData=255,
            xRes=150,
            yRes=150,
            layers=[cat + "_proj"],
            outputType=gdal.GDT_Byte,
            creationOptions=copts,
            callback=cback,
        )
        gdal.Rasterize(cat + ".tif", cat + "_proj.shp", options=param)
        # Compute distances
        compute_distance(
            input_file=cat + ".tif",
            dist_file="dist_" + cat[:-1] + ".tif",
            values=1,
            verbose=verbose,
        )


# End
