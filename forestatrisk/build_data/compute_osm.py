#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Computations on OpenStreetMap data"""

# =====================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# =====================================================================

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
    subprocess.run(cmd, capture_output=True, check=True)

    # Filter data
    cmd = (
        'osmfilter country.o5m --keep="highway=motorway '
        'or highway=trunk or highway=*ary" -o=roads.osm'
    )
    subprocess.run(cmd, capture_output=True, check=True)
    cmd = (
        'osmfilter country.o5m --keep="place=city '
        'or place=town or place=village" -o=towns.osm'
    )
    subprocess.run(cmd, capture_output=True, check=True)
    cmd = (
        'osmfilter country.o5m --keep="waterway=river '
        'or waterway=canal" -o=rivers.osm'
    )
    subprocess.run(cmd, capture_output=True, check=True)

    # Callback
    cback = gdal.TermProgress if verbose else 0

    # Creation options
    copts = ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"]

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
        gdal.VectorTranslate(cat + "_PROJ.shp", cat + ".shp", options=param)
        # Rasterize
        param = gdal.RasterizeOptions(
            outputBounds=extent,
            targetAlignedPixels=True,
            burnValues=[1],
            outputSRS=proj,
            noData=255,
            xRes=150,
            yRes=150,
            layers=[cat + "_PROJ"],
            outputType=gdal.GDT_Byte,
            creationOptions=copts,
            callback=cback,
        )
        gdal.Rasterize(cat + ".tif", cat + "_PROJ.shp", options=param)
        # Compute distances
        compute_distance(
            input_file=cat + ".tif",
            dist_file="_dist_" + cat + ".tif",
            values=1,
            verbose=verbose,
        )


# End
