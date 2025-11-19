==============
Georastertools
==============

This project provides a command line named **georastertools** that enables various calculation tools:


- the calculation of radiometric indices on satellite images
- the calculation of the Compute the Sky View Factor (SVF) of a Digital Elevation Model (DHM).
- the calculation of the hillshades of a Digital Elevation / Surface / Height Model
- the calculation of the speed of evolution of radiometry from images between two dates
- the calculation of zonal statistics of the bands of a raster, that is to say statistics such as min, max, average, etc.
  on subareas (defined by a vector file) of the area of interest.
  
The **georastertools** project also aims to make the handling of the following image products transparent:

- Sentinel-2 L1C PEPS (https://peps.cnes.fr/rocket/#/search)
- Sentinel-2 L2A PEPS (https://peps.cnes.fr/rocket/#/search)
- Sentinel-2 L2A THEIA (https://theia.cnes.fr/atdistrib/rocket/#/search?collection=SENTINEL2)
- Sentinel-2 L3A THEIA (https://theia.cnes.fr/atdistrib/rocket/#/search?collection=SENTINEL2)
- SPOT 6/7 Ortho de GEOSUD (http://ids.equipex-geosud.fr/web/guest/catalog)

It is thus possible to input files in the command line in any of the formats above. 
It is also possible to specify your own product types by providing a JSON file as a parameter of the command line (cf. docs/usage.rst)

Finally, **georastertools** offers an API for calling these different tools in Python and for extending its capabilities, for example by defining new radiometric indices.


Documentation
=============

The official documentation of Georastertools is available `here <https://georastertools.readthedocs.io/en/latest/index.html>`_

Installation
============

Create a conda environment by typing the following:

.. code-block:: bash

  conda env create -n georastertools
  conda activate
  conda install python=3.12 libgdal=3.9
  pip install georastertools --no-binary rasterio

For more details, including installation as a Docker or Singularity image, please refer to the documentation. : docs/install.rst

Usage
=====

georastertools
^^^^^^^^^^^^^^
The georastertools command line is the high-level command for activating the various tools.

.. code-block:: console

  $ rio georastertools --help
  Usage: rio georastertools [OPTIONS] COMMAND [ARGS]...

  Main entry point for the `georastertools` Command Line Interface.

  The `georastertools` CLI provides tools for raster processing and analysis
  and allows configurable data handling, parallel processing, and debugging
  support.

  Logging:

      - INFO level (`-v`) gives detailed step information.

      - DEBUG level (`-vv`) offers full debug-level tracing.

  Environment Variables:

      - `RASTERTOOLS_NOTQDM`: If the log level is above INFO, sets this to
      disable progress bars.

      - `RASTERTOOLS_MAXWORKERS`: If `max_workers` is set, it defines the max
      workers for georastertools.

    Options:
      -t, --rastertype PATH  JSON file defining additional raster types of input
                             files
      --max_workers INTEGER  Maximum number of workers for parallel processing. If
                             not given, it will default to the number of
                             processors on the machine. When all processors are
                             not allocated to run georastertools, it is thus
                             recommended to set this option.
      --debug                Store to disk the intermediate VRT images that are
                             generated when handling the input files which can be
                             complex raster product composed of several band
                             files.
      -v, --verbose          set loglevel to INFO
      -vv, --very-verbose    set loglevel to DEBUG
      --version              Show the version and exit.
      -h, --help             Show this message and exit.

    Commands:
      fi           Apply a filter to a set of images.
      filter       Apply a filter to a set of images.
      hillshade    Execute the hillshade subcommand on a Digital Elevation Model...
      hs           Execute the hillshade subcommand on a Digital Elevation Model...
      radioindice  Compute the requested radio indices on raster data.
      ri           Compute the requested radio indices on raster data.
      sp           Compute the speed of radiometric values for multiple...
      speed        Compute the speed of radiometric values for multiple...
      svf          Compute the Sky View Factor (SVF) of a Digital Elevation...
      ti           Generate tiles of an input raster image following the...
      tiling       Generate tiles of an input raster image following the...
      timeseries   Generate a timeseries of images (without gaps) from a set...
      ts           Generate a timeseries of images (without gaps) from a set...
      zonalstats   Compute zonal statistics of a raster image.
      zs           Compute zonal statistics of a raster image.

Calling georastertools returns the following exit codes:

.. code-block:: console

    0: everything went well
    1: processing error
    2: incorrect invocation parameters

Details of the various subcommands are presented in the documentation : docs/cli.rst

Tests
^^^^^

The project comes with a suite of unit and functional tests. To run them, 
launch the command ``pytest tests``. To run specific tests, execute ``pytest tests -k "<test_name>"``.

The tests may perform comparisons between generated files and reference files. 
In this case, the tests depend on the numerical precision of the platforms. 
To enable these comparisons, you need to add the option. "--compare" for instance ``pytest tests --compare``.

The execution of the tests includes a coverage analysis via pycov.

Documentation generation
^^^^^^^^^^^^^^^^^^^^^^^^

To generate the documentation, run: 

.. code-block:: console

  cd docs
  sphinx-quickstart
  make html

The documentation is generated using the theme "readthedocs".

Note
====

This project has been set up using PyScaffold. For details and usage
information on PyScaffold see https://pyscaffold.org/.
