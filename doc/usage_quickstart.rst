Quickstart
==========

.. contents::
    :depth: 2
    :backlinks: none

For Python users
----------------

The pipeline provides a single high-level function, ``group_pipeline()``, to carry out a full EEG analysis on a group of participants.

Here is a fairly minimal example for a (fictional) N400/P600 experiment with two experimental factors: ``semantics`` (e.g., related versus unrelated words) and emotional ``context`` (e.g., emotionally negative versus neutral).

.. code-block:: python

    from pipeline import group_pipeline

    trials, evokeds, config = group_pipeline(
        raw_files='Results/EEG/raw',
        log_files='Results/RT',
        output_dir='Results/EEG/export',
        besa_files='Results/EEG/cali',
        triggers=[201, 202, 211, 212],
        skip_log_conditions={'semantics': 'filler'},
        components={
            'name': ['N400', 'P600'],
            'tmin': [0.3, 0.5],
            'tmax': [0.5, 0.9],
            'roi': [['C1', 'Cz', 'C2', 'CP1', 'CPz', 'CP2'],
                    ['Fz', 'FC1', 'FC2', 'C1', 'Cz', 'C2']]},
        average_by={
            'related_negative': 'semantics == "related" and context == "negative"',
            'related_neutral': 'semantics == "related" and context == "neutral"',
            'unrelated_negative': 'semantics == "unrelated" and context == "negative"',
            'unrelated_neutral': 'semantics == "unrelated" and context == "neutral"'}})

In this example we have specified:

- ``raw_files``, ``log_files``, ``output_dir``, ``besa_files``: The paths to the raw EEG data, to the behavioral log files, to the desired output directory, and to the BESA files for ocular correction

- ``triggers``: The four different numerical EEG trigger codes corresponding to each of the four cells in the 2 × 2 design

- ``skip_log_conditions``: Our log files may contain additional trials from a "filler" condition without corresponding EEG trials/triggers. These filler trials are marked with the condition label ``'filler'`` in the log file column ``semantics``

- ``components``: The *a priori* defined time windows and regions of interest for the relevant ERP components (N400 and P600)

- ``average_by``: The relevant groupings of trials for which by-participant averaged waveforms should be created. The keys (e.g., ``'related_negative'``) are custom labels of our choice; the values are the corresponding logical conditions that must be met for a trial to be included in the average.

For (way) more options, see the Python API reference.

For R users
-----------

Here is the same example as above but for using the pipeline from R:

.. code-block:: r

    pipeline <- reticulate::import("pipeline")

    res <- pipeline$group_pipeline(
        raw_files = "Results/EEG/raw",
        log_files = "Results/RT",
        output_dir = "Results/EEG/export",
        besa_files = "Results/EEG/cali",
        triggers = c(201, 202, 211, 212),
        skip_log_conditions = list("semantics" = "filler"),
        components = list(
            "name" = list("N400", "P600"),
            "tmin" = list(0.3, 0.5),
            "tmax" = list(0.5, 0.9),
            "roi" = list(
                c("C1", "Cz", "C2", "CP1", "CPz", "CP2"),
                c("Fz", "FC1", "FC2", "C1", "Cz", "C2")
            )
        ),
        average_by = list(
            "related_negative" = "semantics == 'related' & context == 'negative'",
            "related_neutral" = "semantics == 'related' & context == 'neutral'",
            "unrelated_negative" = "semantics == 'unrelated' & context == 'negative'",
            "unrelated_neutral" = "semantics == 'unrelated' & context == 'neutral'"
        )
    )

    trials <- res[[1]]
    evokeds <- res[[2]]
    config <- res[[3]]
