# hu-neuro-pipeline

![PyPI](https://img.shields.io/pypi/v/hu-neuro-pipeline)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hu-neuro-pipeline)
![GitHub](https://img.shields.io/github/license/alexenge/hu-neuro-pipeline)

Single trial EEG pipeline at the Neurocognitive Psychology lab, Humboldt-Universität zu Berlin

Based on Frömer, R., Maier, M., & Abdel Rahman, R. (2018).
Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models.
*Frontiers in Neuroscience*, *12*, 48. <https://doi.org/10.3389/fnins.2018.00048>

## 1. Installation

### 1.1 For Python users

Via `pip` from the [Python Package Index](https://pypi.org/project/hu-neuro-pipeline/) (PyPI):

```bash
python3 -m pip install hu-neuro-pipeline
```

### 1.2 For R users

Install [reticulate](https://rstudio.github.io/reticulate/) and [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for being able to import Python packages into R:

```r
install.packages("reticulate")
reticulate::install_miniconda()
```

Install the pipeline:

```r
py_install("hu-neuro-pipeline", pip = TRUE, python_version = "3.8")
```

## 2. Usage

### 2.1 For Python users

Minimal example for a (fictional) N400/P600 experiment with two experimental factors: `Semantics` (`"related"` vs. `"unrelated"`) and emotional `Context` (`"negative"` vs. `"neutral"`).

```python
from pipeline import group_pipeline

trials, evokeds_df, config = group_pipeline(
    vhdr_files='Results/EEG/raw',
    log_files='Results/RT',
    ocular_correction='Results/EEG/cali',
    triggers={'related/negative': 201,
               'related/neutral': 202,
              'unrelated/negative': 211,
              'unrelated/neutral': 212},
    skip_log_conditions={'Semantics': 'filler'},
    components={'name': ['N400', 'P600'],
                'tmin': [0.3, 0.5],
                'tmax': [0.5, 0.9],
                'roi': [['C1', 'Cz', 'C2', 'CP1', 'CPz', 'CP2'],
                        ['Fz', 'FC1', 'FC2', 'C1', 'Cz', 'C2']]},
    condition_cols=['Semantics', 'Context'],
    export_dir='Results/EEG/export')
```

### 2.2 For R users

Same example as above:

```R
# Import Python module
pipeline <- reticulate::import("pipeline")

# Run the group level pipeline
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

# Extract results
trials <- res[[1]]
evokeds_df <- res[[2]]
config <- res[[3]]
```

### 2.3 Pipeline options

| Argument            | Possible values                                  | Python example                          | R example                                |
| ------------------- | ------------------------------------------------ | --------------------------------------- | ---------------------------------------- |
| `vhdr_files`        | A list of `.vhdr` file name paths                | `['Results/EEG/raw/Vp01.vhdr', ...]`    | `c("Results/EEG/raw/Vp01.vhdr", ...)`    |
|                     | A parent directory of `.vhdr` files              | `'Results/EEG/raw'`                     | `"Results/EEG/raw"`                      |
| `log_files`         | A list of `.csv`/`.tsv`/`.txt` file paths        | `['Results/RT/Vp01.txt', ...]`          | `c("Results/RT/Vp01.txt", ...)`          |
|                     | A parent directory of `.csv`/`.tsv`/`.txt` files | `'Results/RT'`                          | `"Results/RT"`                           |
|                     | A list of data frames                            | `[pd.DataFrame({...}), ...]`            | `list(data.frame(...), ...)`             |
| `ocular_correction` | An ICA method (`fastica`, `picard`, or `picard`) | `'fastica'` (default)                   | `"fastica` (default)                     |
|                     | A list of BESA/MSEC `.matrix` file paths         | `['Results/EEG/cali/Vp01.matrix', ...]` | `c("Results/EEG/cali/Vp01.matrix", ...)` |
|                     | A parent directory of BESA/MSEC `.matrix` files  | `'Results/EEG/cali'`                    | `"Results/EEG/cali"`                     |
|                     | Skip ocular correction                           | `None`                                  | `NULL`                                   |
| `bad_channels`      | Don't interpolate any channels                   | `None` (default)                        | `NULL` (default)                         |
|                     | A list of bad channels for each participant      | `[['Fp1', 'TP9'], ...]`                 | `list(c("Fp1", "TP9"), ...)`             |
|                     | A dictionary of participant IDs and bad channels | `{Vp05: ['Cz', 'T7'], ...}`             | `list(Vp05 = c('Cz', 'T7'), ...)`        |
|                     | Automatic detection based on `reject_*` (> 5 %)  | `'auto'`                                | `"auto"`                                 |
| `skip_log_rows`     | Use all rows from the `log_files`                | `None` (default)                        | `NULL` (default)                         |
|                     | A list of row indices for each participant       | `[[5, 123, 124], ...]`                  | `list(c(5, 123, 124), ...)`              |
|                     | A list of row indices for all participants       | `[1, 2, 3]`                             | `c(1, 2, 3)`                             |

## 3. Output

The `group_pipeline()` function returns three elements.
These can be used, e.g., for further analysis and plotting in R:

* `trials`: A data frame with the single trial behavioral and ERP component data.
Can be used, e.g., to fit a linear mixed model (LMM) predicting the mean amplitude of the N400 component:

```r
library(lme4)
form <- N400 ~ semantics * context + (semantics * context | participant_id)
mod <- lmer(form, trials)
summary(mod)
```

* `evokeds`: The by-participant averages for each condition (or combination of conditions) in `condition_cols`.
Unlike `trials`, these are averaged over trials, but not averaged over EEG channels or time points.
Can be used, e.g., for plotting the time course for the `Semantics * Context` interaction (incl. standard errors). The [eegUtils](https://craddm.github.io/eegUtils) package could be used to plot the corresponding scalp topographies (example to be added).

```r
library(dplyr)
library(ggplot2)
evokeds_df %>%
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
num_bad_chans <- lengths(config$bad_channels)
print(mean(num_bad_chans))
```
