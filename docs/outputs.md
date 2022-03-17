# Pipieline outputs

This page contains information about the objects and files created by the `group_pipeline()` function as well as examples for how they can be used.
Note that all these examples are written in R but many of the same analyses and plots could also be done in Python.

---

* [1. Default outputs](#1-default-outputs)

* [2. Optional outputs](#2-optional-outputs)

---

## 1. Default outputs

### **`trials` (file: `output_dir/trials.csv`)**

The single trial data frame contains all the information from the log file (except for rows specified via `skip_log_rows` or `skip_log_conditions`), together with the corresponding single trial mean ERP amplitudes for each ERP component (specified via `components`).

```r
> trials <- res[[1]]
> head(trials)                                                                            
  participant_id item_id  semantics   RT      P1    N170    N400
1         Vp0001      44    related 1449  1.4548 -1.3999 -0.7654
2         Vp0001      47  unrelated 1725  6.0377  2.0890  0.9265
3         Vp0001      90  unrelated 2271 -2.8285  3.6264 -4.9010
4         Vp0001      25  unrelated 2194  3.5232  4.9644 -3.8442
5         Vp0001      20    related 1860  6.5149  3.8233  0.4319
6         Vp0001      14    related 1160  5.7174  3.3846 -2.3351
```

This data frame can be used, for instance, to fit a linear mixed-effects model predicting the N400 ERP amplitudes:

```r
> library(lme4)
> mod <- lmer(
+   N400 ~ semantics + (semantics | participant_id) + (semantics | item_id),
+   data = trials
+ )
```

### **`evokeds` (file: `output_dir/ave.csv`)**

This data frame contains the by-participant averaged ERPs at each time point, at each channel, and for each experimental condition (or combination of conditions) as specified via the `average_by` option.

```r
> evokeds <- res[[2]]
> head(evokeds)     
  participant_id average_by semantics   time    Fp1    Fpz    Fp2 ...
1         Vp0001  semantics   related -0.500 0.5549 0.9599 1.3789 ...
2         Vp0001  semantics   related -0.496 0.4824 0.7980 1.2616 ...
3         Vp0001  semantics   related -0.492 0.5179 0.6926 1.1960 ...
4         Vp0001  semantics   related -0.488 0.5798 0.6537 1.1883 ...
5         Vp0001  semantics   related -0.484 0.5479 0.6327 1.1621 ...
6         Vp0001  semantics   related -0.480 0.3763 0.5591 1.0230 ...
```

This data frame can be used, for instance, to plot the time course of the different semantic conditions as grand averages (together with their standard errors across participants):

```r
> library(dplyr)
> library(ggplot2)
> evokeds %>%
+    filter(average_by == "semantics") %>%
+    ggplot(aes(x = time, y = N400, color = semantics) +
+    stat_summary(geom = "linerange", fun.data = mean_se, alpha = 0.1) +
+    stat_summary(geom = "line", fun = mean)    
```

### **`config` (file: `output_dir/config.json`)**

This file contains a dictionary-like representation of the input options that were used by the pipeline.
It also lists the automatically detected bad channels (if `bad_channels == 'auto'`) and any rejected epochs (due to `rejected_peak_to_peak`).

```r
> config <- res[[3]]
> rejected_epochs <- lengths(config[["rejected_epochs"]])
> summary(rejected_epochs)  
   Min. 1st Qu.  Median    Mean 3rd Qu.    Max. 
   0.00    7.25   14.00   14.33   22.75   30.00 
```

## 2. Optional outputs

### **`clusters` (file: `output_dir/clusters.csv`)**

Only returned if one or more `perm_contrasts` has been specified.
This data frame contains the statistical results of the cluster-based permutations tests.
These are (a) the (uncorrected) cluster-forming *t* values (`t_obs`), (b) a label for each cluster of connected time points/channels (`cluster`), and (c) the corresponding cluster-level *p* value (`p_val`).
Cluster labels differentiate between positive-going clusters (`'pos_'`) and negative-going (`'neg_'`) clusters, and are sorted by their cluster-level *p* value.

```r
> clusters <- res[[4]]
> head(clusters)  
             contrast time channel   t_obs cluster p_val
1 related - unrelated    0     Fp1 -0.2529      NA     1
2 related - unrelated    0     Fpz  0.3768      NA     1
3 related - unrelated    0     Fp2 -0.5500      NA     1
4 related - unrelated    0     AF7 -0.6792      NA     1
5 related - unrelated    0     AF3  3.0780  pos_12  0.43
6 related - unrelated    0     AFz  3.3211  pos_12  0.43  
```

The data frame can be filtered for significant clusters (based on `p_val`) and, for instance, visualized using `geom_raster()` from `ggplot2`.

### **`tfr_evokeds` (file: `output_dir/tfr_ave.csv`)**

Only returned if `perform_tfr` is set to `True`.
It has the same information as `evokeds` but for the time-frequency representation of the EEG data.
That means (a) that it contains an additional column for the different frequencies (`freqs`) and (b) that the actual values at each channel are not ERP amplitudes but power (in units of percent signal change over baseline).

### **`tfr_clusters` (file: `output_dir/tfr_clusters.csv`)**

Only returned if `perform_tfr` is set to `True` and if one or more `perm_contrasts` has been specified.
It has the same information as `clusters` but for the cluster-based permutation tests of the time-frequency data.
It therefore contains an additional for the different frequencies (`freqs`).
