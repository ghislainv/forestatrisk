from distutils.core import setup, Extension
import numpy.distutils.misc_util


def readme():
    with open("README.md") as f:
        return f.read()

hSDM_module = Extension("hsdm",
                        sources=["C/hSDMmodule.c", "C/useful.c"],
			extra_compile_args=['-std=c99'])

setup(name="deforestprob",
      version="0.1",
      author="Ghislain Vieilledent",
      author_email="ghislain.vieilledent@cirad.fr",
      url="https://ghislainv.github.io",
      license="GPLv3",
      description="This is the Python 'deforestprob' package",
      long_description=readme(),
      classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 2.7",
          "Topic :: Scientific/Engineering :: Bio-Informatics",
      ],
      keywords="deforestation hsdm hierarchical logistic model probability \
      risk Bayesian spatial autocorrelation",
      ext_modules=[hSDM_module],
      packages=["deforestprob"],
      install_requires=["numpy", "sklearn", "patsy", "matplotlib", "pandas"],
      include_dirs=numpy.distutils.misc_util.get_numpy_include_dirs(),
      zip_safe=False)
