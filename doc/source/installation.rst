Installation
============

For Python users
----------------

The pipeline can be installed from the `Python Package Index (PyPI) <https://pypi.org/project/hu-neuro-pipeline>`_ via the command line:

.. code-block:: bash

    pip install hu-neuro-pipeline

Alternatively, to install the latest development version directly from `GitHub <https://github.com/alexenge/hu-neuro-pipeline>`_:

.. code-block:: bash

    pip install git+https://github.com/alexenge/hu-neuro-pipeline.git

The pipeline requires Python Version ≥ 3.8 and a number of `dependency packages <https://github.com/alexenge/hu-neuro-pipeline/blob/main/setup.py#L49-L57>`_, which will get installed automatically when running the commands above.

For R users
-----------

First install and load `reticulate <https://rstudio.github.io/reticulate>`_ (an R package for accessing Python functionality from within R):

.. code-block:: r

    install.packages("reticulate")
    library("reticulate")

Check if you already have `conda <https://docs.conda.io/en/latest/>`_ (a scientific Python distribution) installed on your system:

.. code-block:: r

    conda_exe()

If this shows you the path to a conda executable, you can skip the next step.
If instead it shows you an error, you need to install conda:

.. code-block:: r

    install_miniconda()

Then install the pipeline from the `Python Package Index (PyPI) <https://pypi.org/project/hu-neuro-pipeline>`_:

.. code-block:: r

    py_install("hu-neuro-pipeline", pip = TRUE)

Alternatively, you can install the latest development version from `GitHub`_:

.. code-block:: r

    py_install("git+https://github.com/alexenge/hu-neuro-pipeline.git", pip = TRUE)

What next?
----------

To jump right into how to use the pipeline, see :doc:`Usage <usage>`.

To learn about the different steps that the pipeline is carrying out, see :doc:`Processing details <processing>`.

If you have questions or need help with using the pipeline, please `create an issue on GitHub <https://github.com/alexenge/hu-neuro-pipeline/issues/new>`_.
