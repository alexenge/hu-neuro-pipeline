# Pipieline outputs

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
