Group level
=================

.. contents::
    :depth: 2
    :backlinks: none

Combine trials
--------------

The single trial amplitude dataframes from all participants, containing the log file data plus the computed single trial mean amplitudes for the ERP components of interest, are concatenated and saved in ``.csv`` format.
This dataframe can be viewed with a spreadsheed software and/or directly be used as the input into a statistical model (e.g., an LMM in R with lme4).

Combine evokeds
---------------

The by-participant condition averages (evokeds) from all participants are concatenated across participants and saved as a dataframe in ``.csv`` format and/or as an MNE-Python evoked object in ``.fif`` format.
This dataframe can be used for plotting time courses and scalp topographies.

Compute grand averages
----------------------

The evokeds for each condition are averaged across participants and saved as a dataframe in ``.csv`` format and/or as an MNE-Python evoked object in ``.fif`` format.
This dataframe can be used for plotting time courses and scalp topographies. 

Cluster-based permutation tests
-------------------------------

*Work in progress*
