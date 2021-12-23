# hu-neuro-pipeline

![PyPI](https://img.shields.io/pypi/v/hu-neuro-pipeline)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hu-neuro-pipeline)
![GitHub](https://img.shields.io/github/license/alexenge/hu-neuro-pipeline)

Single trial EEG pipeline at the Neurocognitive Psychology lab, Humboldt-Universität zu Berlin

Based on Frömer, R., Maier, M., & Abdel Rahman, R. (2018).
Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models.
*Frontiers in Neuroscience*, *12*, 48. <https://doi.org/10.3389/fnins.2018.00048>

## Usage

### For Python users

#### 1. Install the pipeline

Install as usual from the [Python Package Index](https://pypi.org/project/hu-neuro-pipeline/) (PyPI):

```bash
python3 -m pip install hu-neuro-pipeline
```

#### 2. Run the pipeline

The `group_pipeline()` function is used to process the EEG data for multiple participants in parallel.

```python
from pipeline import group_pipeline

trials, evokeds, config = group_pipeline(
    vhdr_files='Results/EEG/raw',
    log_files='Results/RT',
    ocular_correction='fastica',
    triggers={'standard': 101, 'target': 102},
    components={'name': ['P3'], 'tmin': [0.3], 'tmax': [0.5],
                'roi': [['C1', 'C2', 'Cz', 'CP1', 'CP2', 'CPz']]},
    condition_cols=['Stim_freq'],
    export_dir='Results/EEG/export',
)
```

See `help(group_pipeline)` for documentation of the input and output arguments.

### For R users

#### 1. Install reticulate and Miniconda

Python packages can be installed and used directly from R via the [reticulate](https://rstudio.github.io/reticulate/) package.
You will also need a Python installation for this to work.
Reticulate can help you to get one in the form of the [Miniconda](https://docs.conda.io/en/latest/miniconda.html) distribution.

```r
install.packages("reticulate")
reticulate::install_miniconda()
```

#### 2. Install the pipeline

Reticulate can install the pipeline from the [Python Package Index](https://pypi.org/project/hu-neuro-pipeline/) (PyPI).

```r
py_install("hu-neuro-pipeline", pip = TRUE, python_version = "3.8")
```

#### 3. Run the pipeline from R

You are now ready to import and use the pipeline in your R scripts.
Here is an example for running the group level pipeline on a fictional N400/P600 experiment.
The experiment has two experimental factors: `Semantics` (`"related"` vs. `"unrelated"`) and emotinal `Context` (`"negative"` vs. `"neutral"`).

```R
pipeline <- reticulate::import("pipeline")
res <- pipeline$group_pipeline(
    vhdr_files = "Results/EEG/raw",
    log_files = "Results/RT",
    ocular_correction = "Results/EEG/cali",
    triggers = list(
        "related/negative" = 201,
        "related/neutral" = 202,
        "unrelated/negative" = 211,
        "unrelated/neutral" = 212
    ),
    skip_log_conditions = list("Semantics" = "filler"),
    components = list(
        "name" = c("N400", "P600"),
        "tmin" = c(0.3, 0.5),
        "tmax" = c(0.5, 0.9),
        "roi" = list(
            c("C1", "Cz", "C2", "CP1", "CPz", "CP2"),
            c("Fz", "FC1", "FC2", "C1", "Cz", "C2")
        )
    ),
    condition_cols = c("Semantics", "Context"),
    export_dir = "Results/EEG/export"
)
```

For documentation of the input and output arguments, see the [source code](https://github.com/alexenge/hu-neuro-pipeline/blob/dev/pipeline/group.py) or:

```r
reticulate::py_help(pipeline$group_pipeline)
```

#### 4. Use the results

The `group_pipeline()` function returns three elements as a list (here `res`):

* `trials`: A data frame with the single trial behavioral and ERP component data.
Can be used, e.g., to fit a linear mixed model (LMM) predicting the mean amplitude of the N400 component:

```r
library(lme4)
form <- N400 ~ semantics * context + (semantics * context | participant_id)
trials <- res[[1]]  # First output is the single trial data frame
mod <- lmer(form, trials)
summary(mod)
```

* `evokeds`: The by-participant averages for each condition (or combination of conditions) in `condition_cols`.
Unlike `trials`, these are averaged over trials, but not averaged over EEG channels or time points.
Can be used, e.g., for plotting the time course for the `Semantics * Context` interaction (incl. standard errors). The [eegUtils](https://craddm.github.io/eegUtils) package could be used to plot the corresponding scalp topographies (example to be added).

```r
library(dplyr)
library(ggplot2)
evokeds <- res[[2]]  # Second output is the evokeds data frame
evokeds %>%
    filter(average_by == "Semantics * Context") %>%
    ggplot(aes(x = time, y = N400, color = Semantics) +
    facet_wrap(~ Context) +
    stat_summary(geom = "linerange", fun.data = mean_se, alpha = 0.1) +
    stat_summary(geom = "line", fun = mean)    
```

* `config`: A list of the options that were used by the pipeline.
Can be used to check which default options were used in addition to the inputs that you have provided.
You can also extract the number of channels that were interpolated for each participant (when using `bad_channels = "auto"`):

```r
config <- res[[3]]  # Third output is the pipeline config
num_bad_chans <- lengths(config$bad_channels)
print(mean(num_bad_chans))
```
