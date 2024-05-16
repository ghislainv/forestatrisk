"""Get the extent of a shapefile."""

from osgeo import ogr


def get_vector_extent(input_file):
    """Compute the extent of a vector file.

    This function computes the extent (xmin, ymin, xmax, ymax) of a
    shapefile.

    :param input_file: Path to the input vector file.

    :return: The extent as a tuple (xmin, ymin, xmax, ymax).

    """

    in_data_dource = ogr.Open(input_file)
    in_layer = in_data_dource.GetLayer()
    extent = in_layer.GetExtent()
    extent = (extent[0], extent[2], extent[1], extent[3])

    return extent  # (xmin, ymin, xmax, ymax)


# Function alias for compatibility with old versions of forestatrisk.
extent_shp = get_vector_extent

# End
