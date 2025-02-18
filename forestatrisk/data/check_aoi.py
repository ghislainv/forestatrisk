"""Check forest cover change raster file."""

from osgeo import ogr


def check_aoi(aoi_file, proj="EPSG:4326"):
    """Check AOI file.

    We check here conditions 1, 3, and 4. Other conditions must be
    checked by the user.

    :param aoi_file: AOI file.

    :param proj: Projection.

    """

    # ===========================
    # Check that the file is a vector file that can be opened with gdal
    try:
        aoi = ogr.Open(aoi_file)
    except RuntimeError as exc:
        err_msg = ("AOI file must be a vector "
                   "file that can be opened with gdal/ogr.")
        raise ValueError(err_msg) from exc

    # ===========================
    # Check projection
    proj_aoi = aoi.GetLayer().GetSpatialRef()
    proj_aoi = proj_aoi.GetAttrValue("AUTHORITY", 1)
    proj_aoi = f"EPSG:{proj_aoi}"
    if proj_aoi != proj:
        err_msg = (f"AOI file coordinate reference system must be {proj}. "
                   f"It is currently {proj_aoi}.")
        raise ValueError(err_msg)

    # Close
    aoi = None


# End of file
