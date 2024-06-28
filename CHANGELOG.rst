Changelog
=========

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
  
