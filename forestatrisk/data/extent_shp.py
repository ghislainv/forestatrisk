"""Get the extent of a shapefile."""

from osgeo import ogr


def extent_shp(shape_file):
    """Compute the extent of a shapefile.

    This function computes the extent (xmin, xmax, ymin, ymax) of a
    shapefile.

    :param inShapefile: Path to the input shapefile.

    :return: The extent as a tuple (xmin, ymin, xmax, ymax).

    """

    in_driver = ogr.GetDriverByName("ESRI Shapefile")
    in_data_dource = in_driver.Open(shape_file, 0)
    in_layer = in_data_dource.GetLayer()
    extent = in_layer.GetExtent()
    extent = (extent[0], extent[2], extent[1], extent[3])

    return extent  # (xmin, ymin, xmax, ymax)


# End
