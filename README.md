# hu-neuro-pipeline

![PyPI](https://img.shields.io/pypi/v/hu-neuro-pipeline)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hu-neuro-pipeline)
![GitHub](https://img.shields.io/github/license/alexenge/hu-neuro-pipeline)

Single trial EEG pipeline at the [Abdel Rahman Lab for Neurocognitive Psychology](https://abdelrahmanlab.com), Humboldt-Universität zu Berlin

Based on Frömer, R., Maier, M., & Abdel Rahman, R. (2018).
Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models.
*Frontiers in Neuroscience*, *12*, 48. <https://doi.org/10.3389/fnins.2018.00048>

## 1. Installation

### 1.1 For Python users

Install the pipeline via `pip` from the [Python Package Index (PyPI)](https://pypi.org/project/hu-neuro-pipeline/):

```bash
pip install hu-neuro-pipeline
```

Alternatively, you can install the latest development version from [GitHub](https://github.com/alexenge/hu-neuro-pipeline.git):

```bash
pip install git+https://github.com/alexenge/hu-neuro-pipeline.git
```

### 1.2 For R users

First install and load [reticulate](https://rstudio.github.io/reticulate/) (an R package for accessing Python functionality from within R):

```r
install.packages("reticulate")
library("reticulate")
```

Check if you already have [conda](https://docs.conda.io/en/latest/) (a scientific Python distribution) installed on your system:

```r
conda_exe()
```

If this shows you the path to a conda executable, you can skip the next step.
If instead it shows you an error, you need to install conda:

```r
install_miniconda()
```

Then install the pipeline from the [Python Package Index (PyPI)](https://pypi.org/project/hu-neuro-pipeline/):

```r
py_install("hu-neuro-pipeline", pip = TRUE)
```

Alternatively, you can install the latest development version from [GitHub](https://github.com/alexenge/hu-neuro-pipeline.git):

```r
py_install("git+https://github.com/alexenge/hu-neuro-pipeline.git", pip = TRUE)
```

## 2. Usage

### 2.1 For Python users

Here is a fairly minimal example for a (fictional) N400/P600 experiment with two experimental factors: `semantics` (e.g., related versus unrelated words) and emotional `context` (e.g., emotionally negative versus neutral).

```python
from pipeline import group_pipeline

trials, evokeds, config = group_pipeline(
    raw_files='Results/EEG/raw',
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
    average_by={'related': 'semantics == "related"',
                'unrelated': 'semantics == "unrelated"'})
```

In this example we have specified:

* The paths to the raw EEG data, to the behavioral log files, to the desired output directory, and to the BESA files for ocular correction

* Four different EEG `triggers` corresponding to each of the four cells in the 2 × 2 design

* The fact that log files contain additional trials from a semantic `'filler'` condition (which we want to skip because they don't have corresponding EEG triggers)

* The *a priori* defined time windows and regions of interest for the N400 and P600 `components`

* The log file columns (`average_by`) for which we want to obtain by-participant averaged waveforms (i.e., for all main and interaction effects)

### 2.2 For R users

Here is the same example as above but for using the pipeline from R:

```R
# Import Python module
pipeline <- reticulate::import("pipeline")

# Run the group level pipeline
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
        related = "semantics == 'related'",
        unrelated = "semantics == 'unrelated'"
    )
)

# Extract results
trials <- res[[1]]
evokeds <- res[[2]]
config <- res[[3]]
```

## 3. Processing details

<img src="https://github.com/alexenge/hu-neuro-pipeline/blob/main/doc/source/_static/flowchart.svg" width="400">

See the [documentation](https://hu-neuro-pipeline.readthedocs.io/en/latest/) for more details about how to use the pipeline and how it works under the hood.
