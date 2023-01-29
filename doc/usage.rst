Usage
=====

For Python users
----------------

Here is a fairly minimal example for a (fictional) N400/P600 experiment with two experimental factors: ``semantics`` (e.g., related versus unrelated words) and emotional ``context`` (e.g., emotionally negative versus neutral).

.. code-block:: python

    from pipeline import group_pipeline

    trials, evokeds, config = group_pipeline(
        vhdr_files='Results/EEG/raw',
        log_files='Results/RT',
        output_dir='Results/EEG/export',
        besa_files='Results/EEG/cali',
        triggers=[201, 202, 211, 212],
        skip_log_conditions={'semantics': 'filler'},
        components={'name': ['N400', 'P600'],
                    'tmin': [0.3, 0.5],
                    'tmax': [0.5, 0.9],
                    'roi': [['C1', 'Cz', 'C2', 'CP1', 'CPz', 'CP2'],
                            ['Fz', 'FC1', 'FC2', 'C1', 'Cz', 'C2']]},
        average_by=['semantics', 'context', 'semantics/context'])

In this example we have specified:

- The paths to the raw EEG data, to the behavioral log files, to the desired output directory, and to the BESA files for ocular correction

- Four different EEG ``triggers`` corresponding to each of the four cells in the 2 × 2 design

- The fact that log files contain additional trials from a semantic ``'filler'`` condition (which we want to skip because they don't have corresponding EEG triggers)

- The *a priori* defined time windows and regions of interest for the relevant ERP ``components`` (N400 and P600)

- The log file columns (``average_by``) for which we want to obtain by-participant averaged waveforms (i.e., for all main and interaction effects)

For R users
-----------

Here is the same example as above but for using the pipeline from R:

.. code-block:: r

    pipeline <- reticulate::import("pipeline")

    res <- pipeline$group_pipeline(
        vhdr_files = "Results/EEG/raw",
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
        average_by = c("semantics", "context", "semantics/context")
    )

    trials <- res[[1]]
    evokeds <- res[[2]]
    config <- res[[3]]
