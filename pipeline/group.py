from functools import partial
from glob import glob
from os import path

import pandas as pd
from joblib import Parallel, delayed

from .helpers import check_participant_input, compute_grands, compute_grands_df
from .participant import participant_pipeline
from .savers import save_config, save_df, save_evokeds


def group_pipeline(
    vhdr_files=None,
    log_files=None,
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
    perform_tfr=False,
    tfr_freqs=range(4, 51, 2),
    tfr_cycles=range(2, 26, 1),
    tfr_baseline=(-0.3, -0.1),
    tfr_components={
        'name': [], 'tmin': [], 'tmax': [], 'fmin': [], 'fmax': [], 'roi': []},
    clean_dir=None,
    epochs_dir=None,
    trials_dir=None,
    evokeds_dir=None,
    export_dir=None,
    to_df=True,
    n_jobs=1
):
    """Processes EEG data for all participants of an experiment in parallel.

    For each participant, reads raw data, performs downsampling (optional),
    loads electrode locations, interpolates bad channels (optional), re-
    references to common average, does ocular correction (ICA or MSEC/BESA,
    optional), does filtering (optional), does segmenting into epochs, rejects
    bad epochs, and computes single trial mean ERP amplitudes for components of
    interest as well as condition averages (evokeds).

    At the group level, combines all single trial behavioral data and mean
    amplitudes and combines evokeds into grand averages (e.g., for plotting).

    For details about the EEG processing pipeline, see Frömer et al. (2018)[1].

    Parameters
    ----------
    vhdr_files : str | Path | list of str | list of Path
        Raw EEG files for all participants. Can either be a list of `.vhdr`
        file paths or the path of their parent directory.
    log_files : str | Path | list of str | list of Path | list of pd.DataFrame
        Behavioral log files for all participants. Can either be a list of
        `.txt`, `.log`, or `.csv` file paths or the path of their parent
        directory. Can also be a list of pandas DataFrames, in which case no
        files are being read.
    ocular_correction : str | list of str | list of Path | None, default 'fastica'
        Ocular correction method. Can either be an ICA method (`'fastica'` or
        `'infomax'` or `'picard'`), a list of MSEC (BESA) `.matrix` file paths,
        or their parent directory.
    bad_channels : list of list | list of str | 'auto' | None, default 'auto'
        Bad channels that should be replaced via interpolation. If 'auto',
        interpolates channels if they meet the rejection threshold (see
        `reject_peak_to_peak` and `reject_flat`) in more than 5% of all epochs.
        If list of lists, must contain one list of bad channel labels per
        participants. If list of str, interpolates the same channels for all
        participants. If None, doesn't interpolate any channels.
    skip_log_rows : list of list | list of int | None, default None
        Rows to remove from the log file based on their indices. This is useful
        if the EEG was paused or interrupted at some point. If list of list,
        must contain one list of row indices (starting at 0) per participant.
        If list of int, removes the same row indices for all participants.
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
    n_jobs : int | 'auto', default 1
        Number of CPU cores to use for processing participants in parallel. If
        'auto', use all available cores on the machine minus one. Numbers > 1
        (including 'auto') do not work under Windows.

    Returns
    -------
    trials : pd.DataFrame
        Combined single trial behavioral and ERP component data for all
        participants. Can be used for running linear mixed models (LMMs) on
        reaction times and ERP mean amplitudes.
    evokeds_df : pd.DataFrame
        Time-resolved by-participant averages for all channels and ERP
        components. If multiple `condition_cols`, the column `average_by`
        indicates for which column (main effects) or combination of columns
        (interaction effects) the averages were computed.
    config : dict
        Configuration of the pipeline. Will be identical to the input arguments
        except for the list of `bad_channels` (if `bad_channels == 'auto'`).
        If directories were provided for the input files, the full list of
        filenames is returned.

    Notes
    -----
    [1] https://doi.org/10.3389/fnins.2018.00048
    [2] https://mne.tools/stable/generated/mne.channels.make_standard_montage.html
    [3] https://mne.tools/stable/generated/mne.channels.read_custom_montage.html
    """

    # Make sure that TFR frequencies and cycles are lists
    tfr_freqs = list(tfr_freqs)
    tfr_cycles = list(tfr_cycles)

    # Backup input arguments for re-use
    config = locals()

    # Remove arguments that are specific for each participant
    nonshared_keys = ['vhdr_files', 'log_files', 'ocular_correction',
                      'bad_channels', 'skip_log_rows', 'n_jobs']
    _ = [config.pop(key) for key in nonshared_keys]

    # Create partial function with only the shared arguments
    pipeline_partial = partial(participant_pipeline, **config)

    # Get input file paths if directories were provided
    if isinstance(vhdr_files, str):
        if path.isdir(vhdr_files):
            vhdr_files = glob(f'{vhdr_files}/*.vhdr')
            vhdr_files.sort()
    if isinstance(log_files, str):
        if path.isdir(log_files):
            log_files = glob(f'{log_files}/*.csv') + \
                glob(f'{log_files}/*.txt') + glob(f'{log_files}/*.tsv')
            log_files.sort()

    # Prepare ocular correction method
    if isinstance(ocular_correction, str):
        if ocular_correction in ['fastica', 'infomax', 'picard']:
            ocular_correction = [ocular_correction] * len(vhdr_files)
        elif path.isdir(ocular_correction):
            ocular_correction = glob(f'{ocular_correction}/*.matrix')
            ocular_correction.sort()

    # Extract participant IDs from filenames
    participant_ids = [path.basename(f).split('.')[0] for f in vhdr_files]

    # Construct lists of bad_channels and skip_log_rows per participant
    bad_channels = check_participant_input(bad_channels, participant_ids)
    skip_log_rows = check_participant_input(skip_log_rows, participant_ids)

    # Combine participant-specific inputs
    participant_args = zip(vhdr_files, log_files, ocular_correction,
                           bad_channels, skip_log_rows)

    # Do processing in parallel
    n_jobs_num = -2 if n_jobs == 'auto' else n_jobs
    res = Parallel(n_jobs_num)(
        delayed(pipeline_partial)(*args) for args in participant_args)

    # Sort outputs into seperate lists
    trials, evokeds, evokeds_dfs, configs = list(map(list, zip(*res)))

    # Combine trials and save
    trials = pd.concat(trials, ignore_index=True)
    if export_dir is not None:
        save_df(trials, export_dir, participant_id='all', suffix='trials')

    # Combine evokeds_dfs and save
    evokeds_df = pd.concat(evokeds_dfs, ignore_index=True)
    if export_dir is not None:
        save_df(evokeds_df, export_dir, participant_id='all', suffix='ave')

    # Compute grand averages and save
    grands = compute_grands(evokeds)
    grands_df = compute_grands_df(evokeds_df)
    save_evokeds(
        grands, grands_df, export_dir, participant_id='grand', to_df=to_df)

    # Add participant-specific arguments back to config
    config = {'vhdr_files': vhdr_files, 'log_files': log_files,
              'ocular_correction': ocular_correction,
              'bad_channels': bad_channels,
              'skip_log_rows': skip_log_rows, **config, 'n_jobs': n_jobs}

    # Add automatically detected bad channels
    if 'auto' in bad_channels:
        config['auto_bad_channels'] = [cf['bad_channels'] for cf in configs]

    # Save config
    if export_dir is not None:
        save_config(config, export_dir)

    return trials, evokeds_df, config
