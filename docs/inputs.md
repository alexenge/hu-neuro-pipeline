# Pipeline inputs

## 1. Input options

### **`vhdr_files` (required)**

Input BrainVision EEG header files.
Either a list of `.vhdr` file paths or a single path pointing to their parent directory.

| Python examples                      | R examples                            |
| ------------------------------------ | ------------------------------------- |
| `['Results/EEG/raw/Vp01.vhdr', ...]` | `c("Results/EEG/raw/Vp01.vhdr", ...)` |
| `'Results/EEG/raw'`                  | `"Results/EEG/raw"`                   |

### **`log_files` (required)**

Either a list of `.csv`, `.tsv`, or `.txt` (tab-separated) file paths or a single path pointing to their parent directory.
Can also be a list of data frames, which can be useful when the log files need some cleaning before they can be matched to the EEG data (but see also `skip_log_rows` and `skip_log_conditions`).
Either way, each log file must have the same number of rows (trials) as there are epochs (defined via `triggers`) in the corresponding EEG file.

| Python examples                | R examples                      |
| ------------------------------ | ------------------------------- |
| `['Results/RT/Vp01.txt', ...]` | `c("Results/RT/Vp01.txt", ...)` |
| `'Results/RT'`                 | `"Results/RT"`                  |
| `[pd.DataFrame({...}), ...]`   | `list(data.frame(...), ...)`    |

## 2. Output options

### **`export_dir` (required)**

Main output directory.
All group level outputs are saved there including, e.g., the single trial data frame (`all_trials.csv`) and the by-participant condition averages (`all_ave.csv`/`.fif`).

| Python examples        | R examples             |
| ---------------------- | ---------------------- |
| `'Results/EEG/export'` | `"Results/EEG/export"` |

### **`clean_dir` (optional, default `None`)**

Cleaned data directory.
Each participant's continuous EEG data is saved there after downsampling, bad channel interpolation, re-referencing, ocular correction, and frequency domain filtering.
It is usually not necessary to save these intermediary files.

| Python examples       | R examples            |
| --------------------- | --------------------- |
| `'Results/EEG/clean'` | `"Results/EEG/clean"` |

### **`epochs_dir` (optional, default `None`)**

Epoched data directory.
Each participant's ERP epochs (defined via `triggers`) are saved there.
It is usually not necessary to save these intermediary files.
One use case for them would be to fit a linear mixed model with `time` as a groupping factor (see [here](https://mne.tools/mne-r/articles/plot_evoked_multilevel_model.html) for an example).
Note that these files contain all samples and channels for all epochs which makes them very large (especially with `to_df=True`).

| Python examples        | R examples             |
| ---------------------- | ---------------------- |
| `'Results/EEG/epochs'` | `"Results/EEG/epochs"` |

### **`to_df` (optional, default `True`)**

How to save MNE-Python objects (epochs and evokeds).
If `True`, save all objects as data frames in `.csv` format, which can easily be imported into other software like R or Excel.
If `False`, save them as `.fif` files, which take up less disk space but can only be opened by MNE-Python and other specialized MEEG software.
You can also save them in `'both'` formats.

| Python examples               | R examples                    |
| ----------------------------- | ----------------------------- |
| `True` or `False` or `'both'` | `TRUE` or `FALSE` or `"both"` |

## 3. Preprocessing options

### **`downsample_sfreq` (optional, default `None`)**

The sampling rate (in Hz) to downsample the EEG data to before doing any preprocessing.
If `None`, retain the original sampling rate.
Moderate downsampling (e.g., to 250 Hz) will significantly speed up the processing and reduce the output file sizes.

| Python examples | R examples |
| --------------- | ---------- |
| `None`          | `NULL`     |
| `250.`          | `250`      |

### **`veog_channels` (optional, default `'auto'`)**

Two EEG or EOG channel labels from which to create a new virtual vertical electrooculography (VEOG) channel.
This virtual channel will then be used during `ocular_correction` (see below, only relevant for independent component analysis [ICA]).
Can also be `'auto'`, in which case the pipeline will check if it can find two channel labels typically used for VEOG (`['F9', 'F10', 'Afp9', 'Afp10']`).
If `None`, don't construct a new VEOG channel, which will work only (a) if BESA/MSEC is used instead for `ocular_correction` instead of ICA or (b) if there already is a channel called `VEOG` present in the raw data.

| Python examples | R examples       |
| --------------- | ---------------- |
| `'auto'`        | `"auto"`         |
| `['F9', 'F10']` | `c("F9", "F10")` |
| `None`          | `NULL`           |

### **`heog_channels` (optional, default `'auto'`)**

Two EEG or EOG channel labels from which to create a new horizontal vertical electrooculography (HEOG) channel.
This virtual channel will then be used during `ocular_correction` (see below, only relevant for independent component analysis [ICA]).
Can also be `'auto'`, in which case the pipeline will check if it can find two channel labels typically used for HEOG (`['Fp1', 'FP1', 'Auge_u', 'IO1']`).
If `None`, don't construct a new HEOG channel, which will work only (a) if BESA/MSEC is used instead for `ocular_correction` instead of ICA or (b) if there already is a channel called `VEOG` present in the raw data.

| Python examples  | R examples        |
| ---------------- | ----------------- |
| `'auto'`         | `"auto"`          |
| `['Fp1', 'IO1']` | `c("Fp1", "IO1")` |
| `None`           | `NULL`            |

### **`montage` (optional, default `'easycap-M1'`)**

The standard or custom montage for reading channel locations.
Can be the name of one of the [standard montages](https://mne.tools/stable/generated/mne.channels.make_standard_montage.html) shipped with MNE-Python (such as [`'easycap-M1'`](https://github.com/mne-tools/mne-python/blob/main/mne/channels/data/montages/easycap-M1.txt) for the standard montage used at the Neuro lab).
Can also be a file path pointing to a file with custom channel locations (see [here](https://mne.tools/stable/generated/mne.channels.read_custom_montage.html) for possible file types).

| Python examples           | R examples                |
| ------------------------- | ------------------------- |
| `'easycap-M1'`            | `"easycap-M1"`            |
| `'EEG/chanlocs_besa.txt'` | `"EEG/chanlocs_besa.txt"` |

### **`bad_channels` (optional, default: `None`)**

Bad EEG channels to repair via interpolation.
If `None`, assume that all channels of all participants are good and do not interpolate anything.
Can be a list of lists, each containing the bad channel labels for one participants.
Can also be a dict where the keys are (a selection of) participant labels and the values are lists of their corresponding bad channel labels.
Finally, there is an (experimental) `'auto'` option that automatically interpolates channel if they would lead to an excessive number (> 5%) of bad epochs per participant (where bad epochs are defined based on `reject_peak_to_peak` and `reject_flat`, see below).

| Python examples                     | R examples                                 |
| ----------------------------------- | ------------------------------------------ |
| `None`                              | `NULL`                                     |
| `[['Fp1', 'TP9'], [], ['Oz'], ...]` | `list(c("Fp1", "TP9"), c(), c("Oz"), ...)` |
| `{'Vp05': ['Cz', 'F10'], ...}`      | `list(Vp05 = c("Cz", "F10"), ...)`         |
| `'auto'`                            | `"auto"`                                   |

### **`ocular_correction` (optional, default: `'fastica'`)**

Method for performing correction of eye movement artifacts (default: `'fastica'`).
Either the name of an algorithm for Independent Component Analysis (`fastica`, `infomax`, or `picard`) or a list (or parent directory) of BESA matrix files for Multiple Source Eye Correction (MSEC).
Can also be `None` to skip ocular correction.

| Python examples                         | R examples                               |
| --------------------------------------- | ---------------------------------------- |
| `'fastica'`                             | `"fastica"`                              |
| `['Results/EEG/cali/Vp01.matrix', ...]` | `c("Results/EEG/cali/Vp01.matrix", ...)` |
| `'Results/EEG/cali'`                    | `"Results/EEG/cali"`                     |
| `None`                                  | `NULL`                                   |

### **`highpass_freq` (optional, default: `0.1`)**

The lower passband edge of the frequency domain filter (in Hz).
Can also be `None` to disable highpass filtering.

| Python examples | R examples |
| --------------- | ---------- |
| `0.1`           | `0.1`      |
| `None`          | `NULL`     |

### **`lowpass_freq` (optional, default: `40.`)**

The upper passband edge of the frequency domain filter (in Hz).
Can also be `None` to disable lowpass filtering.

| Python examples | R examples |
| --------------- | ---------- |
| `40.`           | `40`       |
| `None`          | `NULL`     |

## 4. Epoching options

### **`triggers` (recommended, default: `None`)**

The EEG triggers for creating epochs, usually denoting the onset of stimuli (or responses of interest).
Can be list of numerical triggers or a dict of condition names (keys) and their corresponding triggers. Note that the dict option including the condition names is only usfeul if `condition_cols` is `None`, as otherwise the conditions will be inferred from the log file.
Can also be `None`, in which *all* the triggers present in the experiment are used (so don't this to work).

| Python examples                     | R examples                            |
| ----------------------------------- | ------------------------------------- |
| `[201, 202]`                        | `c(201, 202)`                         |
| `{'negative': 201, 'neutral': 202}` | `list(negative = 201, neutral = 202)` |
| `None`                              | `NULL`                                |

### **`epochs_tmin` (optional, default: `-0.5`)**

Start of the epoching interval relative to stimulus onset (in s).

| Python examples | R examples |
| --------------- | ---------- |
| `-0.5`          | `-0.5`     |

### **`epochs_tmax` (optional, default: `1.5`)**

End of the epoching interval relative to stimulus onset (in s).

| Python examples | R examples |
| --------------- | ---------- |
| `1.5`           | `1.5`      |

## **`baseline` (optional, default: `(-0.2, 0.0)`)**

Time period (in s relative to stimulus onset) for baseline correction.
For each epoch and channel, the average voltage during this interval is subtracting from all time points outside the baseline interval as to correct for shifts in voltage level even before stimulus onset.
Setting either the first or the second of these two values to `None` will use the either the start or the end of epoch, respectively.

| Python examples | R examples     |
| --------------- | -------------- |
| `(-0.2, 0.0)`   | `c(-0.2, 0.0)` |
| `(None, 0.0)`   | `c(NULL, 0.0)` |

## **`skip_log_rows` (optional, default: `None`)**

Row indices to skip from the log file.
In case of `None`, all rows from the file are used (but see also `skip_log_conditions` below).
Can be a list of row indices to exclude the same rows for all subjects (e.g., always skip the first three rows), or a list (or dict) of lists to skip different indices for each subject (e.g., because the EEG was accidently paused for some trials).
All indices are Python style, i.e., starting from `0` (not from `1` as in R).

| Python examples                   | R examples                                |
| --------------------------------- | ----------------------------------------- |
| `None`                            | `NULL`                                    |
| `[0, 1, 2]`                       | `c(0, 1, 2)`                              |
| `[113, 114, 115], [], [12], ...]` | `list(c(113, 114, 115), c(), c(12), ...)` |
| `{'Vp12': [55, 239], ...}`        | `list(Vp12 = c(55, 239), ...)`            |

## **`skip_log_conditions` (optional, default: `None`)**

A convenient alternative to `skip_log_rows` to exclude an entire condition (or conditions) from the log file rather than individual trials.
If `None`, all rows from the file are used (but see also `skip_log_rows` above).
Can be a dict where keys are column names from the log file and values are (lists of) condition labels as they occur in these columns.
This is useful, e.g., to exclude "filler" stimuli that don't have corresponding EEG triggers.

| Python examples                            | R examples                                     |
| ------------------------------------------ | ---------------------------------------------- |
| `None`                                     | `NULL`                                         |
| `{'emotion': 'filler'}`                    | `list(emotion = "filler")`                     |
| `{'emotion': ['filler', 'positive'], ...}` | `list(emotion = c("filler", "positive"), ...)` |

### **`reject_peak_to_peak` (optional, default: `200.`)**

Rejection threshold (in microvolts) for excluding epochs as bad.
If the peak-to-peak amplitude of any channel in the time window (defined by `epochs_tmin` and `epochs_tmax`) exceeds this value, the corresponding epoch (a) will be set to `NaN` for all ERP components in the single trial data frame and (b) not enter into the by-participant condition averages that are used for plotting and permutation testing.

| Python examples | R examples |
| --------------- | ---------- |
| `200.`          | `200`      |
| `None`          | `NULL`     |

### **`reject_flat` (optional, default: `1.`)**

Same as `reject_peak_to_peak` (see above), but excluding epochs for which the peak-to-peak amplitude is *below* (rather than above) the threshold value (a.k.a. epochs with "flat channels").

| Python examples | R examples |
| --------------- | ---------- |
| `1.`            | `1`        |
| `None`          | `NULL`     |

### **`components` (recommended, default: don't compute components)**

Time window and region of interest (ROI) for the ERP component(s) of interest.
Must be a dict with the following entries:

* `'name'`: The name of each component, which will become the column name in the single trial data frame.

* `'tmin'`: The starting time point of each component (relativ to stimulus onset in s).

* `'tmax'`: The ending time point of each component (relativ to stimulus onset in s).
  
* `'roi'`: The channel labels in the ROI for each component.

| Python example                                                                                            |
| --------------------------------------------------------------------------------------------------------- |
| `{'name': ['P1', 'N170'], 'tmin': [0.08, 0.15], 'tmax': [0.13, 0.2], 'roi': [['PO3', ...], ['P7', ...]]}` |

| R example                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------ |
| `list(name = c("P1", "N170"), tmin = c(0.08, 0.15), tmax = c(0.13, 0.2), roi = list(c("PO3", ...), c("P7", ...)))` |

### **`condition_cols` (recommended, default: `None`)**

Column names from the log file for averaging.
Can be one or multiple column names which code for the experimental conditions.
The pipeline will then compute by-participant condition averages (evokeds) for all main effects and interaction effects (if applicable).
These are useful for plotting or for running permutation tests (see the `perm_*` arguments below).
If `None`, the condition labels provided by the `triggers` (see above) will be used.

| Python examples                     | R examples                           |
| ----------------------------------- | ------------------------------------ |
| `'semantic_condition'`              | `"semantic_condition"`               |
| `['semantic_condition', 'context']` | `c("semantic_condition", "context")` |

## 5. Options for time-frequency analysis

### **`perform_tfr` (optional, default: `False`)**

Whether or not to perform time-frequency analysis in addition to ERPs.

| Python examples | R examples |
| --------------- | ---------- |
| `False`         | `FALSE`    |
| `True`          | `TRUE`     |

### **`tfr_freqs` (optional, default: `range(4, 51, 2)`)**

The frequencies for the family of [Morlet wavelets](https://neuroimage.usc.edu/brainstorm/Tutorials/TimeFrequency#Morlet_wavelets).
More frequencies will take longer to compute and need larger amount of disk space.
Note that the time-frequency representation is computed on the *unfiltered* epochs so that frequencies larger than `lowpass_freq` are possible.

| Python examples                       | R examples                             |
| ------------------------------------- | -------------------------------------- |
| `range(4, 51, 2)`                     | `seq(4, 50, 2)`                        |
| `[8, 12, 16, 20, 24, 28, 32, 36, 40]` | `c(8, 12, 16, 20, 24, 28, 32, 36, 40)` |

### **`tfr_cycles` (optional, default: `range(2, 26, 1)`)**

The number of cycles for the family of [Morlet wavelets](https://neuroimage.usc.edu/brainstorm/Tutorials/TimeFrequency#Morlet_wavelets).
Should be increasing as the frequencies of the wavelets are increasing because, at higher frequencies, more cycles will fit into the same time window, thus improving spatial resolution.
The corresponding frequencies divided by the factor 2 seems to be a common choice.

| Python examples                     | R examples                           |
| ----------------------------------- | ------------------------------------ |
| `range(2, 26, 1)`                   | `seq(2, 25, 1)`                      |
| `[4, 6, 8, 10, 12, 14, 16, 18, 20]` | `c(4, 6, 8, 10, 12, 14, 16, 18, 20)` |

### **`tfr_baseline` (optional, default: `range(2, 26, 1)`)**

Time period (in s relative to stimulus onset) for baseline correction of the time-frequency data.
Unlike the `baseline` for EPRs (see above), the baseline correction for TFR will transform the data into percent signal change as to correct for the typical $1/f$ scaling of EEG frequencies.
Furthermore, the baseline window should end *before* stimulus onset so that post-stimulus power at low frequencies doesn't get contaminated by pre-stimulus fluctuations.

| Python examples | R examples      |
| --------------- | --------------- |
| `(-0.3, -0.1)`  | `c(-0.3, -0.1)` |
| `(None, -0.1)`  | `c(NULL, -0.1)` |

### **`tfr_components` (optional, default: no TFR components)**

Similar to `components` for ERPs, i.e., the time windows, frequency bands, and channels for the time-frequency bands of interest.
The structure is the same as for `components`, but adding new dictionary entries for the lower (`'fmin'`) and upper (`'fmax'`) bounds for the frequencies of interest (e.g., 8--13 Hz for alpha band activity).
Note the term "component" is specific to ERPs and is used here solely to highlight the correspondence between the two options.

| Python example                                                                                          |
| ------------------------------------------------------------------------------------------------------- |
| `{'name': ['alpha'], 'tmin': [0.05], 'tmax': [0.25], 'fmin': [8], 'fmax': [13], 'roi': [['PO9', ...]]}` |

| R example                                                                                                       |
| --------------------------------------------------------------------------------------------------------------- |
| `list(name = c("alpha"), tmin = c(0.05), tmax = c(0.25), fmin = c(8), fmax = c(13), roi = list(c("PO9", ...)))` |

## 6. Options for cluster-based permutation tests

### **`perm_contrasts` (optional, default: `None`)**

Contrasts between conditions to test using cluster-based permutation tests (CBPTs).
Must be one or multiple tuples, each containing exactly two condition labels.
Each of these labels must be corresponding to one condition which can be found in one of the `condition_cols`.
Single condition labels can be used to test main effects (e.g., semantically related vs. unrelated) and multiple hierarchical labels (seperated by `/`) can be used to test nested effects (e.g., semantically related vs. unrelated only *within* the emotionally negative context).
In this case, the order must of the levels must correspond to the order of the column names in `condition_cols`.

| Python examples                                  | R examples                                             |
| ------------------------------------------------ | ------------------------------------------------------ |
| `[('related', 'unrelated')]`                     | `list(c("related", "unrelated"))`                      |
| `[('related/negative'), ('unrelated/negative')]` | `list(c("related/negative"), c("unrelated/negative"))` |

### **`perm_tmin` (optional, default: `0.`)**

The starting time point (in s relative to stimulus onset) of the time window to consider for permutation testing.
If `None`, all time points from the beginning of the epoch (including the prestimulus intervall) are used.
Cropping the time window (based on *a priori* knowledge about plausible effects) can increase the sensitivity of the test.

| Python examples | R examples |
| --------------- | ---------- |
| `0.`            | `0`        |
| `None`          | `NULL`     |

### **`perm_tmax` (optional, default: `1.`)**

The ending time point (in s relative to stimulus onset) of the time window to consider for permutation testing.
If `None`, all time points until the end of the epoch are used.
Cropping the time window (based on *a priori* knowledge about plausible effects) can increase the sensitivity of the test.

| Python examples | R examples |
| --------------- | ---------- |
| `1.`            | `1`        |
| `None`          | `NULL`     |

### **`perm_channels` (optional, default: `None`)**

The channel labels to consider for permutation testing.
If `None`, all EEG channels are used.
Reducing the channels to a region of interest (based on *a priori* knowledge about plausible effects) can increase the sensitivity of the test.

| Python examples           | R examples                 |
| ------------------------- | -------------------------- |
| `None`                    | `NULL`                     |
| `['C1', 'Cz', 'C2', ...]` | `c("C1", "Cz", "C2", ...)` |

### **`perm_fmin` (optional, default: `None`)**

The lowest frequency (in Hz) of the time-frequency representation to consider for permutation testing.
Only relevent if `perform_tfr` is `True`.
If `None`, the lowest frequency in the data is used.
Cropping the frequency range (based on *a priori* knowledge about plausible effects) can increase the sensitivity of the test.

| Python examples | R examples |
| --------------- | ---------- |
| `None`          | `NULL`     |
| `8.`            | `8`        |

### **`perm_fmax` (optional, default: `None`)**

The highest frequency (in Hz) of the time-frequency representation to consider for permutation testing.
Only relevent if `perform_tfr` is `True`.
If `None`, the highest frequency in the data is used.
Cropping the frequency range (based on *a priori* knowledge about plausible effects) can increase the sensitivity of the test.

| Python examples | R examples |
| --------------- | ---------- |
| `None`          | `NULL`     |
| `30.`           | `30`       |

## 7. Performance options

### **`n_jobs` (optional, default: `1`)**

Number of jobs to run in parallel.
If `1`, participants will be processed sequentially.
If greater than `1`, multiple participants will be processed in parallel, thus reducing the overall runtime of the pipeline.
Negative values can be used to use all cores (`-1`) or all but a certain number of cores (e.g., `-2` = all but one core) that are available on your machine.
**Options other than `1` are currently not supported on Windows operating systems!**

| Python examples | R examples |
| --------------- | ---------- |
| `1`             | `1`        |
| `4`             | `4`        |
| `-2`            | `-2`       |
