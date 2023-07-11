Installation
============

.. contents::
    :depth: 2
    :backlinks: none

For Python users
----------------

The pipeline can be installed from the `Python Package Index (PyPI) <https://pypi.org/project/hu-neuro-pipeline>`_ via the command line:

.. code-block:: bash

    pip install hu-neuro-pipeline

Alternatively, to install the latest development version directly from `GitHub <https://github.com/alexenge/hu-neuro-pipeline>`_:

.. code-block:: bash

    pip install git+https://github.com/alexenge/hu-neuro-pipeline.git

The pipeline requires Python Version ≥ 3.8 and a number of `dependency packages <https://github.com/alexenge/hu-neuro-pipeline/blob/doc/add-sphinx/setup.py#L47-L55>`_, which will get installed automatically when running the commands above.

For R users
-----------

First install `reticulate <https://rstudio.github.io/reticulate>`_ and `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ for being able to import Python packages into R:

.. code-block:: r

    install.packages("reticulate")
    reticulate::install_miniconda()

Then install the pipeline from the `Python Package Index (PyPI) <https://pypi.org/project/hu-neuro-pipeline>`_:

.. code-block:: r

    reticulate::py_install("hu-neuro-pipeline", pip = TRUE)

Alternatively, to install the latest development version directly from `GitHub`_:

.. code-block:: r

    reticulate::py_install("git+https://github.com/alexenge/hu-neuro-pipeline.git", pip = TRUE)

What next?
----------

To jump right into how to use the pipeline, see :doc:`Usage <usage>`.

To learn about the different steps that the pipeline is carrying out, see :doc:`Processing details <processing>`.

If you have questions or need help with using the pipeline, please `create an issue on GitHub <https://github.com/alexenge/hu-neuro-pipeline/issues/new>`_.
