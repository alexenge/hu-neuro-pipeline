.. hu-neuro-pipeline documentation master file, created by
   sphinx-quickstart on Fri Jan 27 11:23:58 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

hu-neuro-pipeline
=================

.. image:: https://img.shields.io/pypi/v/hu-neuro-pipeline
   :target: https://pypi.org/project/hu-neuro-pipeline
   :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/hu-neuro-pipeline.svg
   :target: https://img.shields.io/pypi/pyversions/hu-neuro-pipeline
   :alt: PyPI - Python Version

.. image:: https://img.shields.io/github/license/alexenge/hu-neuro-pipeline
   :target: https://github.com/alexenge/hu-neuro-pipeline/blob/main/LICENSE
   :alt: License

|

Single trial EEG pipeline at the `Abdel Rahman Lab for Neurocognitive Psychology <https://abdelrahmanlab.com>`_, Humboldt-Universität zu Berlin

Based on Frömer, R., Maier, M., & Abdel Rahman, R. (2018).
Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models.
*Frontiers in Neuroscience*, *12*, 48. `https://doi.org/10.3389/fnins.2018.00048 <https://doi.org/10.3389/fnins.2018.00048>`_

.. toctree::
   :maxdepth: 1
   :caption: For Python users

   installation_py
   quickstart_py
   inputs_py
   outputs_py
   examples/n400
   reference_py

.. toctree::
   :maxdepth: 1
   :caption: For R users

   installation_r
   quickstart_r
   inputs_r
   outputs_r
   examples/ucap

.. toctree::
   :maxdepth: 1
   :caption: Processing details

   processing_overview
   processing_participant
   processing_group
   processing_tfr
