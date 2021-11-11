# STEP-MNE

Single trial EEG pipeline using [MNE-Python](https://mne.tools)

![PyPI](https://img.shields.io/pypi/v/step-mne)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/step-mne)
![GitHub](https://img.shields.io/github/license/alexenge/step-mne)

Based on Frömer, R., Maier, M., & Abdel Rahman, R. (2018).
Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models.
*Frontiers in Neuroscience*, *12*, 48. <https://doi.org/10.3389/fnins.2018.00048>

## Usage

### For R users

#### 1. Install reticulate and miniconda

You can use Python packages (including STEP-MNE) directly from R with the help of the [reticulate](https://rstudio.github.io/reticulate/) package.
It can also be used to install [Miniconda](https://docs.conda.io/en/latest/miniconda.html), which is a scientific Python distribution and package management system.
You will only need do this once for each machine that you want to use STEP-MNE on.

```r
install.packages("reticulate")
reticulate::install_miniconda()
```

#### 2. Install STEP-MNE

Once you have installed reticulate and Python (with Miniconda), you can install STEP-MNE from the [Python Package Index (PyPI)](https://pypi.org/project/step-mne/).

```r
py_install("step_mne", pip = TRUE, python_version = "3.8")
```

#### 3. Run the pipeline from R

In your scripts for data analysis, you can then import the STEP-MNE module and use it directly from R.
Here is an example for running the pipeline on a fictional N400/P600 experiment.
The experiment has two experimental factors: `Semantics` (`"related"` vs. `"unrelated"`) and emotinal `Context` (`"negative"` vs. `"neutral"`).

```R
step_mne <- reticulate::import("step_mne")
res <- step_mne$pipeline(
    vhdr_files = "Results/EEG/raw",
    log_files = "Results/RT",
    ocular_correction = "Results/EEG/cali",
    triggers = list(
        "related/negative" = 201,
        "related/neutral" = 202,
        "unrelated/negative" = 211,
        "unrelated/neutral" = 212
    ),
    skip_log_rows = list("Semantics" = "filler"),
    components = list(
        "name" = c("N400", "P600"),
        "tmin" = c(300, 500),
        "tmax" = c(500, 900),
        "roi" = list(
            c("C1", "Cz", "C2", "CP1", "CPz", "CP2"),
            c("Fz", "FC1", "FC2", "C1", "Cz", "C2")
        )
    ),
    condition_cols = c("Semantics", "Context"),
    export_dir = "Results/EEG/export"
)
```

Note that the pipeline has further (optional) input options which are documented in the [script](https://github.com/alexenge/step-mne/blob/main/step_mne/pipeline.py).
You can also check them via:

```r
reticulate::py_help(step_mne$pipeline)
```

#### 4. Use the results

The `pipeline()` function returns three elements as its output (here stored in a list called `res`):

* `trials`: A data frame containing the single trial behavioral and ERP component data.
Can be used, for instance, to fit a linear mixed model (LMM) predicting the mean amplitude of the N400 component:

```r
library(lme4)
form <- N400 ~ semantics * context + (semantics * context | participant_id)
trials <- res[[1]]  # The first output is the single trial data frame
mod <- lmer(form, trials)
summary(mod)
```

* `evokeds`: The by-participant averages for each condition (or combination of conditions) in the `condition_cols`.
Unlike the single trial data frame, these are averaged over trials, but not averaged over space (EEG sensors) or time (samples).
Can be used, for example, for plotting time courses or scalp topographies.
Here is an example for plotting the grand averages for the `Semantics * Context` interaction (and their standard error across participants). The [eegUtils](https://craddm.github.io/eegUtils) package could be used to plot the corresponding scalp topographies (an example of this will be added).

```r
library(dplyr)
library(ggplot2)
evokeds <- res[[2]]  # The second output is the evokeds data frame
evokeds %>%
    filter(average_by == "Semantics * Context") %>%
    ggplot(aes(x = time, y = N400, color = Semantics) +
    facet_wrap(~ Context) +
    stat_summary(geom = "linerange", fun.data = mean_se, alpha = 0.1) +
    stat_summary(geom = "line", fun = mean)    
```

* `config`: A list of the input options that were used by the pipeline.
You can check this to see which default options were used in addition to the non-default options that you have provided.
You can also extract the number of channels that were interpolated for each participant (when using `bad_channels = "auto"`):

```r
config <- res[[3]]  # The third output is the pipeline config
n_bads <- lengths(config$bad_channels)
print(mean(n_bads))
```
