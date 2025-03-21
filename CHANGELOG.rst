Changelog
=========

forestatrisk 1.3.2
++++++++++++++++++

* Adding Nepal and Mongolia to list of countries.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.3.1...v1.3.2

forestatrisk 1.3.1
++++++++++++++++++

* Upgrading tests with Python 3.13.
* Checking installation setup.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.3...v1.3.1

forestatrisk 1.3
++++++++++++++++

* Adding the possibility to obtain a deforestation density map in ``allocate_deforestation()``.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.9...v1.3

forestatrisk 1.2.9
++++++++++++++++++

* Adding ``check_aoi()`` function.
* Adding internal function ``get_iso_wdpa()``.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.8...v1.2.9

forestatrisk 1.2.8
++++++++++++++++++

* Bug corrections.
* Rasterize the aoi based on forest resolution and extent.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.7...v1.2.8

forestatrisk 1.2.7
++++++++++++++++++

* Copy files if symbolic links cannot be created.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.6...v1.2.7

forestatrisk 1.2.6
++++++++++++++++++

* Adding function `check_fcc()` to check multiband forest cover change raster.
* Compatibility with gcc 14.
* Bug correction when there is only one explicative variable with GLM and RF models.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.5...v1.2.6

forestatrisk 1.2.5
++++++++++++++++++

* Allow computing forest rasters (``forest_t1.tif``, ``fcc12.tif``, etc.) and variables (``dist_edge_t1``, etc.) if the user provides a ``forest_src.tif`` file.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.4...v1.2.5

forestatrisk 1.2.4
++++++++++++++++++

* Bug correction when downloading protected areas from WDPA at state level.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.3...v1.2.4

forestatrisk 1.2.3
++++++++++++++++++

* Adding function to allocate deforestation.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.2...v1.2.3

forestatrisk 1.2.2
++++++++++++++++++

* Replacing ``gdal.TermProgress`` with ``gdal.TermProgress_nocb``.
* Changes: https://github.com/ghislainv/forestatrisk/compare/v1.2.1...v1.2.2

forestatrisk 1.2.1
++++++++++++++++++

* Compatibility with Python 3.12
* Bug corrections.
* List of changes: https://github.com/ghislainv/forestatrisk/compare/v1.2...v1.2.1

forestatrisk 1.2
++++++++++++++++++

* Removing dependencies to Earth Engine API and RClone which were used to interact with Google Earth Engine and Google Drive to compute and download forest and WHRC biomass data.
* Removing functions ``run_gee_forest()`` (and alias ``country_forest_run()``), ``download_forest()``, and dependencies.
* Removing functions ``run_gee_biomass_whrc()``, ``download_biomass_whrc()``, and dependencies.
* Package `geefcc <https://ecology.ghislainv.fr/geefcc/>`_ can now be used to compute and download forest from GEE.
* Adding dependency to ``geefcc``.
* Upgrading GADM to v4.1.
* New Python API doc on website.
* Modifying random forest to accept number of trees and max depth.
* Update progress bar to mimic gdal progress.
* Compatibility with Python >= 3.12 and Numpy >= 1.23
* Several other improvements and bug corrections: https://github.com/ghislainv/forestatrisk/compare/v1.1.3...v1.2
  
forestatrisk 1.1.3
++++++++++++++++++

* Improve usage on multiple operating systems.

forestatrisk 1.1.2
++++++++++++++++++

* New wheels for Python 3.9 to 3.11.

forestatrisk 1.1.1
++++++++++++++++++

* Adding biomass from WHRC.
* Let the user select the Agg display for matpotlib.

forestatrisk 1.1
++++++++++++++++

* Bug correction and optimization of function ``.deforest()``.
* New tutorial for New Caledonia.

forestatrisk 1.0
++++++++++++++++

* Version associated to the publication in `JOSS <https://doi.org/10.21105/joss.02975>`_\ .
* Adding a Contributing section.
* Adding Community guidelines and a Code of conduct.
  
forestatrisk 0.2
++++++++++++++++

* New module organization.
* Adding a logo for the package.
* Package website at `<https://ecology.ghislainv.fr/forestatrisk/>`_\ .
* Update docstring in Python functions.
* New documentation with Sphinx.
* Continuous Integration with GitHub Actions.
* CI: Automated tests with pytest
* CI: Wheel build for PyPI.
  
forestatrisk 0.1.1
++++++++++++++++++

* New ``ee_jrc`` function to compute forest cover with GEE.
* Use of ``rclone`` to interact with GoogleDrive.
* Updated dependencies.
* Use of ``pywdpa`` to download protected areas.
* New tutorials.
* Tests have been added.

forestatrisk 0.1
++++++++++++++++

* First release of the package (previously called ``deforestprob``).
  
