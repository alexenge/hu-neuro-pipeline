# STEP-MNE

Single trial EEG pipeline using [MNE-Python](https://mne.tools)

Based on Frömer, R., Maier, M., & Abdel Rahman, R. (2018).
Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models.
*Frontiers in Neuroscience*, *12*, 48. https://doi.org/10.3389/fnins.2018.00048

## Usage

### For R users

#### 1. Install reticulate and miniconda

[Reticulate](https://rstudio.github.io/reticulate/) is an R package for calling Python code from R.
Miniconda is a minimal version of [conda](https://docs.conda.io/en/latest/), which is a Python distribution and package management system for scientific computing.
To install reticulate and miniconda, use:

```r
install.packages("reticulate")
reticulate::install_miniconda()
```

#### 2. Install STEP-MNE

You can install the STEP-MNE Python package from [PyPI](https://pypi.org/project/step-mne/) using reticulate.

```r
py_install("step_mne", pip = TRUE, python_version = "3.8")
```

#### 3. Run the pipeline from R

Once installed, you can import the STEP-MNE module and use it's `pipeline()` function directly from R. Here is an example for an N400/P600 experiment with two experimental factors, `Semantics` (related vs. unrelated) and emotinal `Context` (negative vs. neutral).

```R
step_mne <- import("step_mne")
res <- step_mne$pipeline(
    vhdr_files = "Results/EEG/raw",
    log_files = "Results/RT",
    ocular_correction = "Results/EEG/cali",
    triggers = c(
        "related/negative" = 201,
        "related/neutral" = 202,
        "unrelated/negative" = 211,
        "unrelated/neutral" = 212
    ),
    components_df = list(
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

#### 4. Use the results

The `pipeline()` functions returns as its first output a data frame that contains the single trial behavioral and ERP component data.
This can be used, e.g., to fit a linear mixed model to predict reaction times or mean ERP amplitudes for the components in `components_df`:

```r
library(lme4)
trials <- res[[1]]  # First output is the trials data frame
mod <- lmer(N400 ~ semantics * context + (semantics * context|participant_id))
summary(mod)
```

The second and third output of the `pipeline()` are the evokeds, i.e., the time-resolved by-participant averages for each condition (or combination of conditions) in `condition_cols`.
They are outputted in MNE (`.fif`) and text (`.csv`) format.
Only the latter can be read by R and is useful, e.g., the grand average and its confidence interval across participants as a time course:

```r
evokeds <- res[[3]]  # Third output is the evokeds data frame
evokeds %>%
    ggplot(aes(x = time, y = N400)) +
    stat_summary("line")
```

The [eegUtils](https://craddm.github.io/eegUtils) package can be used to plot the `evokeds` as scalp topographies.
An example for this will follow soon.
