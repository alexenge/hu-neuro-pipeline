Participant level
=================

Read raw data
-------------

Reads the raw data (currently assumed to be in BrainVision format) into MNE-Python.

Downsample
----------

Optionally reduces the sampling rate of the data.
No downsampling is performed by default but moderate downsampling (e.g., from 500 to 250 Hz) will make subsequent computations faster and reduce the amount of disc space needed (especially relevant for time-frequency analysis).

Read channel locations
----------------------

Reads the 2D and/or 3D positions of the EEG sensors based on a known standard montage or based on a custom channel location file.
The channel locations are written into an output file (``channel_locations.csv``) in such a format that they can easily be used for plotting using the R package `eegUtils <https://craddm.github.io/eegUtils>`_.

Interpolate bad channels
------------------------

Optionally replaces the data from EEG channels known to be "bad" (e.g., noisy or flat) with an interpolated value based on their neighboring channels.
The interpolation is done using spherical splines, the default in MNE-Python [#]_.

Re-reference to average
-----------------------

The EEG channels are re-referenced from the online reference (e.g., M1, the left mastoid) to a different channel or set of channels.
The most common choice is to re-reference to an average reference, meaning that at each time point, the average of all EEG channels is subtracted from each channel.
This is done to reduce the impact of any noise or spatial bias that may be present in the online reference electrode.
It has the effect that the average of all EEG channels is zero at each time point but preserves any relative difference between channels at different areas of the scalp.

Ocular correction
-----------------

Optionally performs a correction of eye blink and eye movement artifacts using multiple source eye correction (MSEC/BESA) or independent component analysis (ICA).

* **MSEC/BESA** requires one custom correction matrix file for each participant, created using the commercial BESA software based on calibration data. This is a channels × channels matrix with correction weights that gets multiplied with the continous EEG data to correct for eye blinks and eye movements.

* **ICA** is computed based on an initial principal component analysis (PCA) of a high-pass filtered (cutoff = 1 Hz) copy of the continous EEG data. A fixed or adaptive number of principal components will be used and the flavor of the ICA algorithm can be selected (``'fastica'`` seems to be a reasonable default). The pipeline then automatically detects and removes independent components (ICs) that are likely to reflect eye blinks or eye movements, indicated by a significant correlation between the time course of the IC and either of two virtual EOG channels (VEOG or HEOG). The quality of the ICA and the selected components can be inspected in the quality control HTML reports that are optionally generated for each participant when setting the ``report_dir`` argument.

Frequency filter
----------------

By default applies a band-pass filter between 0.1 and 40 Hz to the data.
This removes low-frequency noise (e.g., electrode drifts due to sweat) and high-frequency noise (e.g., line noise and muscle artifacts).
Either or both of the cutoff frequencies can be changed or disabled so that data will only be low-pass filtered, high-pass filtered, or not filtered at all.
The default filter from MNE-Python is used which, at the time of writing, is a one-pass, zero-phase, non-causal finite impulse response (FIR) filter with a Hamming window [#]_.
More information about the filter (e.g., the transition bandwidth and filter length) is also printed to the console while the pipeline is running.
Note that excessive filtering (esp. high-pass filtering > 0.1 Hz) can introduce artifactual "bumps" in the ERP [#]_.

Segment to epochs
-----------------

The continous EEG data is segmented into discontinous epochs around the events (typically stimuli or responses) of interest.
Each event of interest needs to have a numerical EEG trigger value associated with it.
Epochs should typically be one to two seconds long and include a couple of hundreds of milliseconds before event onset (default: -0.5 s to 1.5 s).
An interval before stimulus onset (default: -0.2 to 0.0 s) is typically used for baseline correction to remove any voltage offset between trials.
At each channel and for each epoch, the average voltage during this time window is subtracted from all time points in the epoch.

Read + match log file
---------------------

The pipeline assumes that there is a text file (called the "log file") that contains tabular information about each EEG trials, containing information such as the stimulus that was presented, the experimental condition(s) to which it belonged, and the reaction time of the participant.
Such files are typically written automatically by the software that was used to display the experiment, such as Presentation or PsychoPy.
**It is super important that there are the same number of trials (rows) in the log file as there are triggers (epochs) in the EEG data.**
If this is not the case, the log file can be manipulated (e.g., in R or pandas) to exclude any trials or entire conditions without corresponding triggers.
It is also possible to let the pipeline search for and delete behavioral log file trials with missing EEG data automatically, as long as you have a log file column with the (expected) EEG trigger for every trial.

Reject bad epochs
-----------------

The pipeline will declare epochs as "bad" if the peak-to-peak amplitude (i.e., the difference between the highest voltage and the lowest voltage) at any channel exceeds a certain threshold (default: 200 µV).
Declaring epochs as "bad" means that their single trial mean ERP amplitude will be set to ``NaN`` for all components in the single trial data frame, and that these epochs will not enter the computation of the by-participant condition averages (evokeds).

Compute single trial amplitudes
-------------------------------

For each ERP component of interest, the pipeline computes one value per trial.
This value reflects the mean ERP amplitude for this component (in µV) averaged across (a) the time window of interest (e.g., 300--500 ms for the N400 component) and (b) the channels in the region of interest (e.g., channels C1, Cz, C2, CP1, CPz, and CP2 for the N400 component).
Performing this step on the single trial level is the main advantage of the Frömer et al. (2018) [#]_ pipeline compared to more traditional ERP analysis approach, where the amplitudes are additionally averaged across trials from the same condition, thereby losing any information available on the single trial level (e.g., item-level confounds or random effects).

Compute by-participant condition averages
-----------------------------------------

In addition to the single trial amplitudes (usually used for statistical modeling), the pipeline computes average waveforms for each participant and experimental condition.
Unlike the single trial amplitudes, these averages are computed by averaging across trials from the same condition, but they retain the temporal information (all time points in the epoch) and spatial information (all channels) of the epoched data.
These averages are typically used for visualization as time course plots or scalp topographies or for cluster-based permutation tests.
They could also be used for "traditional" statistical modeling such as repeated measures ANOVAs, but this is not recommended because it discards the single trial information and makes more questionable assumptions than the single trial mixed modeling approach.

Create quality control reports
------------------------------

Optionally, the pipeline creates one quality control (QC) report file in HTML format for each participant.
This contains plots of the data before and after preprocessing as well as some summary statistics and metadata.
It is especially recommended to check these reports when using ICA for artifact correction, to confirm that the automatic component detection algorithm has indeed indentified plausible eye blink and eye movement components.

Notes
-----

.. [#] https://mne.tools/stable/generated/mne.io.Raw.html#mne.io.Raw.interpolate_bads
.. [#] https://mne.tools/stable/auto_tutorials/preprocessing/25_background_filtering.html
.. [#] Tanner, D., Morgan-Short, K., & Luck, S. J. (2015). How inappropriate high-pass filters can produce artifactual effects and incorrect conclusions in ERP studies of language and cognition. *Psychophysiology*, 52(8), 997–1009. https://doi.org/10.1111/psyp.12437
.. [#] Frömer, R., Maier, M., & Abdel Rahman, R. (2018). Group-level EEG-processing pipeline for flexible single trial-based analyses including linear mixed models. *Frontiers in Neuroscience*, 12, 48. https://doi.org/10.3389/fnins.2018.00048
