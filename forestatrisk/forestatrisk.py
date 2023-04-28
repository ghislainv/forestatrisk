#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ecology.ghislainv.fr
# python_version  :>=2.7
# license         :GPLv3
# ==============================================================================

from __future__ import print_function  # Python 3 compatibility

import forestatrisk as far


def main():
    """forestatrisk.forestatrisk: provides entry point main().

    Running ``forestatrisk`` in the terminal prints ``forestatrisk``
    description and version. Can be used to check that the
    ``forestatrisk`` Python package has been correctly imported.

    """

    print(far.__doc__)
    print("version {}.".format(far.__version__))


# End
