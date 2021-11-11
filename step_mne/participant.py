from os import path

from mne import Epochs, events_from_annotations
from mne.io import read_raw_brainvision

from .helpers import (add_heog_veog, apply_montage, compute_evokeds,
                      compute_single_trials, correct_besa, correct_ica,
                      get_bads, read_log)
from .savers import (save_clean, save_df, save_epochs, save_evokeds,
                     save_montage)


def participant_pipeline(
    vhdr_file=None,
    log_file=None,
    ocular_correction='fastica',
    bad_channels='auto',
    skip_log_rows=None,
    skip_log_conditions=None,
    downsample_sfreq=None,
    veog_channels='auto',
    heog_channels='auto',
    montage='easycap-M1',
    highpass_freq=0.1,
    lowpass_freq=30.0,
    epochs_tmin=-0.5,
    epochs_tmax=1.5,
    baseline=(-0.2, 0.0),
    triggers=None,
    reject_peak_to_peak=200.0,
    reject_flat=1.0,
    components={'name': [], 'tmin': [], 'tmax': [], 'roi': []},
    condition_cols=None,
    clean_dir=None,
    epochs_dir=None,
    trials_dir=None,
    evokeds_dir=None,
    export_dir=None,
    to_df=True,
):
    """Processes EEG data for a single participant.

    Reads raw data, performs downsampling (optional), loads electrode
    locations, interpolates bad channels (optional), re-references to common
    average, does ocular correction (ICA or MSEC/BESA, optional), does
    filtering (optional), does segmenting into epochs, rejects bad epochs, and
    computes single trial mean ERP amplitudes for components of interest as
    well as condition averages (evokeds).

    For details about the EEG processing pipeline, see Frömer et al. (2018)[1].

    Parameters
    ----------
    vhdr_file : str | Path | list
        Raw EEG header (`.vhdr`) file.
    log_files : str | Path | list of str | list of Path
        Behavioral log (`.txt`, `.log`, or `.csv`) file.
    ocular_correction : str | Path | None, default 'fastica'
        Ocular correction method. Can either be an ICA method (`'fastica'` or
        `'infomax'` or `'picard'`) or the path of a MSEC (BESA) `.matrix` file.
    bad_channels : list of str | 'auto' | None, default 'auto'
        Bad channels that should be replaced via interpolation. If 'auto',
        interpolates channels if they meet the rejection threshold (see
        `reject_peak_to_peak` and `reject_flat`) in more than 5% of all epochs.
    skip_log_rows : list of int | None, default None
        Rows to remove from the log file based on their indices. This is useful
        if the EEG was paused or interrupted at some point. Indices start at 0.
    skip_log_conditions : dict | None, default None
        Rows to remove from the log file based on their condition. This is
        useful to remove filler stimuli for which there are no EEG triggers.
        Dict keys are the column names in the log file, values (str or list of
        str) are the condition(s) that should be removed remove.
    downsample_sfreq : float | None, default None
        Downsampling frequency in Hz. Downsampling (e.g., from 500.0 Hz to
        250.0 Hz) saves computation time and disk space.
    veog_channels : list of str | 'auto' | None, default 'auto'
        Names of two vertical EOG channels (above and below the eye) for
        creating a virtual, bipolar VEOG channel. If 'auto', try different
        common VEOG electrode labels ('Fp1'/'FP1', 'Auge_u'/'IO1').
    heog_channels : list of str | 'auto' | None, default 'auto'
        Names of two vertical EOG channels (left and right of the eye) for
        creating a virtual, bipolar HEOG channel. If 'auto', try different
        common HEOG electrode labels ('F9'/'Afp9', 'F10'/'Afp10').
    montage : str | Path, default 'easycap-M1'
        Montage for looking up channel locations. Can either be the name of a
        standard montage (see [2]) or the path to a custom electrode location
        file (see [3]).
    highpass_freq : float | None, default 0.1
        Pass-band edge (in Hz) for the highpass filter. If None, don't use
        highpass filter.
    lowpass_freq : float | None, default 30.0
        Pass-band edge (in Hz) for the lowpass filter. If None, don't use
        lowpass filter.
    epochs_tmin : float, default -0.5
        Starting point of the epoch (in s) relative to stimulus onset.
    epochs_tmax : float, default 1.5
        Ending point of the epoch (in s) relative to stimulus onset.    
    baseline : tuple of (float, float), default (-0.2, 0.0)
        Time window (in s) for baseline correction relative to stimulus onset.
    triggers : dict of {str: int, ...} | None, default None
        Triggers (values, int) of the relevant events (usually stimuli) and
        their corresponding labels (keys, str) for creating epochs. If None,
        use all triggers. This will not work if there are more triggers than
        trials in the log file.
    reject_peak_to_peak : float | None, default 200.0
        Peak-to-peak amplitude (in microvolts) for rejecting bad epochs.
    reject_flat : float | None, default 1.0
        Amplitude (in microvolts) for rejecting bad epochs as flat.
    components : dict | None, default None
        Definition of ERP components for single trial analysis. Must have the
        following key (value) pairs: 'name' (list of str), `tmin` (list of
        float), `tmax` (list of float), `roi` (list of list of str), where
        `tmin` and `tmax` are the time windows of interest (in s) and `roi` are
        the lists of channel names for the spatial regions of interest. All of
        four lists must have the same number of elements.
    condition_cols : str | list of str | None, default None
        Columns in the log file to compute condition averages (evokeds) for. If
        given a single column name, computes averages for each condition in
        this column. If given multiple column names, computes averages for each
        condition in each column (i.e., main effects) as well as for each
        combination of conditions across columns (i.e., interaction effects).
        If None, creates one average for each EEG trigger (see `triggers`).
    clean_dir : str | Path | None, default None
        Output directory to save the cleaned (ocular corrected, filtered)
        continuous EEG data (always in `.fif` format) for each participant.
    epochs_dir : str | Path | None, default None
        Output directory to save the full (time-resolved) epochs data
        (in `.fif` and/or `.csv` format, see `to_df`) for each participant.
    trials_dir : str | Path | None, default None
        Output directory to save the single trial behavioral and ERP component
        DataFrame (always in `.csv` format) for each participant.
    evokeds_dir : str | Path | None, default None
        Output directory to save the condition averages (evokeds; in `.fif`
        and/or `.csv` format, see `to_df`) for each participant; see
        `condition_cols`.
    export_dir : str | Path | None, default None
        Output directory to save data at the group level, namely channel
        locations (in `.csv` format), combined single trial and evoked data,
        and grand averages (in `.fif` and/or `.csv` format, see `to_df`).
    to_df : bool | 'both', default True
        Convert all MNE objects (epochs, evokeds, grand averages) to data
        frames and save them in `.csv` instead of `.fif` format. If `both`,
        save in both `.csv` and `.fif` format.

    Returns
    -------
    trials : pandas.DataFrame
        Single trial behavioral and ERP component data for the participant.
    evokeds : list of mne.Evoked
        One average time course (at all channels + ROIs) for each condition in
        `condition_cols` (main effects) and for each combination of conditions
        (interaction effects).
    evokeds_df : pandas.DataFrame
        Same as `evokeds`, but converted to a Pandas DataFrame so it can more
        easily be combined across participants and/or plotted. The column
        `average_by` distinguishes the averages for the different main effects
        and interaction effects.
    config : dict
        Configuration of the pipeline. Will be identical to the input arguments
        except for the list of `bad_channels` (if `bad_channels == 'auto'`).

    Notes
    -----
    [1] https://doi.org/10.3389/fnins.2018.00048
    [2] https://mne.tools/stable/generated/mne.channels.make_standard_montage.html
    [3] https://mne.tools/stable/generated/mne.channels.read_custom_montage.html
    """

    # Backup input arguments for re-use
    config = locals()

    # Get participant ID from filename
    participant_id = path.basename(vhdr_file).split('.')[0]

    # Read raw data
    raw = read_raw_brainvision(vhdr_file, preload=True)

    # Downsample
    if downsample_sfreq is not None:
        orig_sfreq = raw.info['sfreq']
        downsample_sfreq = float(downsample_sfreq)
        print(f'Downsampling from {orig_sfreq} Hz to {downsample_sfreq} Hz')
        raw.resample(downsample_sfreq)

    # Add EOG channels
    raw = add_heog_veog(raw, heog_channels, veog_channels)

    # Apply custom or standard montage
    apply_montage(raw, montage)

    # Interpolate any bad channels
    if bad_channels is not None and bad_channels != 'auto':
        if isinstance(bad_channels, str):
            bad_channels = [bad_channels]
        raw.info['bads'] = raw.info['bads'] + bad_channels
        _ = raw.interpolate_bads()

    # Re-reference to common average
    _ = raw.set_eeg_reference('average')

    # Do ocular correction
    if ocular_correction is not None:
        if path.isfile(ocular_correction):
            correct_besa(raw, besa_file=ocular_correction)
        else:
            correct_ica(raw, method=ocular_correction)

    # Filtering
    _ = raw.filter(highpass_freq, lowpass_freq)

    # Save cleaned continuous data
    if clean_dir is not None:
        save_clean(raw, clean_dir, participant_id)

    # Determine events and the corresponding (selection of) triggers
    events, event_id = events_from_annotations(
        raw, regexp='Stimulus', verbose=False)
    if triggers is not None:
        triggers = {key: int(value) for key, value in triggers.items()}
        event_id = triggers

    # Epoching including baseline correction
    epochs = Epochs(raw, events, event_id, epochs_tmin, epochs_tmax, baseline,
                    preload=True)

    # Drop the last sample to produce a nice even number
    _ = epochs.crop(epochs_tmin, epochs_tmax, include_tmax=False)
    print(epochs)

    # Read behavioral log file
    epochs.metadata = read_log(log_file, skip_log_rows, skip_log_conditions)
    epochs.metadata.insert(0, column='participant_id', value=participant_id)

    # Get indices of bad epochs and channels
    bad_ixs, auto_channels = get_bads(epochs, reject_peak_to_peak, reject_flat)

    # Start over, repairing any (automatically deteced) bad channels
    if bad_channels == 'auto':
        if auto_channels != []:
            config['bad_channels'] = auto_channels
            trials, evokeds, evokeds_df, config = \
                participant_pipeline(**config)
            return trials, evokeds, evokeds_df, config
        else:
            config['bad_channels'] = []

    # Add single trial mean ERP amplitudes to metadata
    trials = compute_single_trials(epochs, components, bad_ixs)

    # Save epochs as data frame and/or MNE object
    if epochs_dir is not None:
        save_epochs(epochs, epochs_dir, participant_id, to_df)

    # Save single trial behavioral and ERP data
    if trials_dir is not None:
        save_df(trials, trials_dir, participant_id, suffix='trials')

    # Save channel locations
    if export_dir is not None:
        save_montage(epochs, export_dir)

    # Compute evokeds
    evokeds, evokeds_df = compute_evokeds(
        epochs, condition_cols, bad_ixs, participant_id)

    # Save evokeds as data frame and/or MNE object
    if evokeds_dir is not None:
        save_evokeds(evokeds, evokeds_df, evokeds_dir, participant_id, to_df)

    return trials, evokeds, evokeds_df, config
