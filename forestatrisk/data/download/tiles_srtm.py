"""Get lat/long 5 degree tiles from an extent."""

import numpy as np


def tiles_srtm(extent_latlong):
    """Compute lat/long tiles from an extent for SRTM data.

    This function computes lat/long tiles for SRTM data from an extent
    in lat/long. See `<http://dwtkns.com/srtm/>`_. SRTM tiles are 5x5
    degrees. x: -180/+180, y: +60/-60.

    :param extent_latlong: Extent in lat/long: (xmin, ymin, xmax, ymax).

    :return: A tuple of two strings indicating tile numbers for lat and long.

    """

    # Tiles for SRTM data
    xmin_latlong = np.floor(extent_latlong[0])
    ymin_latlong = np.floor(extent_latlong[1])
    xmax_latlong = np.ceil(extent_latlong[2])
    ymax_latlong = np.ceil(extent_latlong[3])
    # Compute SRTM tile numbers
    tile_left = int(np.ceil((xmin_latlong + 180.0) / 5.0))
    tile_right = int(np.ceil((xmax_latlong + 180.0) / 5.0))
    if tile_right == tile_left:
        # Trick to make curl globbing works
        tile_right = tile_left + 1
    tile_top = int(np.ceil((-ymax_latlong + 60.0) / 5.0))
    tile_bottom = int(np.ceil((-ymin_latlong + 60.0) / 5.0))
    if tile_bottom == tile_top:
        tile_bottom = tile_top + 1
    # Format variables, zfill is for having 01 and not 1
    tiles_long = str(tile_left).zfill(2) + "-" + str(tile_right).zfill(2)
    tiles_lat = str(tile_top).zfill(2) + "-" + str(tile_bottom).zfill(2)

    return (tiles_long, tiles_lat)


# End
