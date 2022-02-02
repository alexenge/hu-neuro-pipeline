# hu-neuro-pipeline

![PyPI](https://img.shields.io/pypi/v/hu-neuro-pipeline)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hu-neuro-pipeline)
![GitHub](https://img.shields.io/github/license/alexenge/hu-neuro-pipeline)

Single trial EEG pipeline at the [Neurocognitive Psychology lab](https://www.psychology.hu-berlin.de/en/profship/nk), Humboldt-Universität zu Berlin

Based on Frömer, R., Maier, M., & Abdel Rahman, R. (2018).
Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models.
*Frontiers in Neuroscience*, *12*, 48. <https://doi.org/10.3389/fnins.2018.00048>

## 1. Installation

### 1.1 For Python users

Install the pipeline via `pip` from the [Python Package Index](https://pypi.org/project/hu-neuro-pipeline/) (PyPI):

```bash
python3 -m pip install hu-neuro-pipeline
```

### 1.2 For R users

First install [reticulate](https://rstudio.github.io/reticulate/) and [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for being able to import Python packages into R:

```r
install.packages("reticulate")
reticulate::install_miniconda()
```

Then install the pipeline via `pip` from the [Python Package Index](https://pypi.org/project/hu-neuro-pipeline/) (PyPI):

```r
reticulate::py_install("hu-neuro-pipeline", pip = TRUE, python_version = "3.8")
```

## 2. Usage

[**Pipeline inputs**](docs/inputs.md)

[**Pipeline outputs**](docs/outputs.md)

## 3. Examples

### 3.1 For Python users

This is a fairly minimal example for a (fictional) N400/P600 experiment with two experimental factors: `semantics` (e.g., `'related'` vs. `'unrelated'`) and emotional `Context` (e.g., `'negative'` vs. `'neutral'`).
We need to specify the paths to the raw EEG data, the behavioral log files, the output directory, and the BESA files for ocular correction (though we could also choose an ICA method like `'fastica'`).
Four different EEG `triggers` correspond to each of the four different cells in the 2 × 2 design.
The log files might contain additional rows (i.e., trials) from a `'filler'` condition which we want to skip because they don't have corresponding EEG triggers.
We want to compute mean ERP amplitudes for pre-specified time windows and regions of interest corresponding to the N400 and P600 `components`.
In addition, we want to obtain by-participant averages for each condition (for the main effects) and each combination of conditions (for the interaction effect), as specified with `average_by`.

```python
from pipeline import group_pipeline

trials, evokeds = group_pipeline(
    vhdr_files='Results/EEG/raw',
    log_files='Results/RT',
    output_dir='Results/EEG/export',
    ocular_correction='Results/EEG/cali',
    triggers=[201, 202, 211, 212],
    skip_log_conditions={'semantics': 'filler'},
    components={'name': ['N400', 'P600'],
                'tmin': [0.3, 0.5],
                'tmax': [0.5, 0.9],
                'roi': [['C1', 'Cz', 'C2', 'CP1', 'CPz', 'CP2'],
                        ['Fz', 'FC1', 'FC2', 'C1', 'Cz', 'C2']]},
    average_by=['semantics', 'Context', 'semantics/Context'])
```

### 3.2 For R users

Here's the same example as above but for using the pipeline from R:

```R
# Import Python module
pipeline <- reticulate::import("pipeline")

# Run the group level pipeline
res <- pipeline$group_pipeline(
    vhdr_files = "Results/EEG/raw",
    log_files = "Results/RT",
    output_dir = "Results/EEG/export",
    ocular_correction = "Results/EEG/cali",
    triggers = c(201, 202, 211, 212),
    skip_log_conditions = list("semantics" = "filler"),
    components = list(
        "name" = c("N400", "P600"),
        "tmin" = c(0.3, 0.5),
        "tmax" = c(0.5, 0.9),
        "roi" = list(
            c("C1", "Cz", "C2", "CP1", "CPz", "CP2"),
            c("Fz", "FC1", "FC2", "C1", "Cz", "C2")
        )
    ),
    average_by = c("semantics", "Context", "semantics/Context")
)

# Extract results
trials <- res[[1]]
evokeds <- res[[2]]
```
