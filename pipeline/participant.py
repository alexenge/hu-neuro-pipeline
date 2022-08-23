import numpy as np
import pandas as pd
from mne import Epochs, events_from_annotations
from mne.time_frequency import tfr_morlet

from .averaging import compute_evokeds
from .epoching import (compute_single_trials, get_bad_channels, get_bad_epochs,
                       match_log_to_epochs, read_log, triggers_to_event_id)
from .io import (read_raw, save_clean, save_df, save_epochs, save_evokeds,
                 save_montage, save_report)
from .preprocessing import (add_heog_veog, apply_montage, correct_besa,
                            correct_ica, interpolate_bad_channels)
from .report import create_report
from .tfr import compute_single_trials_tfr, subtract_evoked


def participant_pipeline(
    vhdr_file,
    log_file,
    besa_file=None,
    bad_channels=None,
    auto_bad_channels=None,
    skip_log_rows=None,
    skip_log_conditions=None,
    downsample_sfreq=None,
    veog_channels='auto',
    heog_channels='auto',
    montage='easycap-M1',
    ica_method=None,
    ica_n_components=0.99,
    highpass_freq=0.1,
    lowpass_freq=40.0,
    triggers=None,
    triggers_column=None,
    epochs_tmin=-0.5,
    epochs_tmax=1.5,
    baseline=(-0.2, 0.0),
    reject_peak_to_peak=200.0,
    components={'name': [], 'tmin': [], 'tmax': [], 'roi': []},
    average_by=None,
    perform_tfr=False,
    tfr_subtract_evoked=False,
    tfr_freqs=np.linspace(4.0, 40.0, num=37),
    tfr_cycles=np.linspace(2.0, 20.0, num=37),
    tfr_mode='percent',
    tfr_baseline=(-0.45, -0.05),
    tfr_components={
        'name': [], 'tmin': [], 'tmax': [], 'fmin': [], 'fmax': [], 'roi': []},
    clean_dir=None,
    epochs_dir=None,
    trials_dir=None,
    evokeds_dir=None,
    chanlocs_dir=None,
    tfr_dir=None,
    report_dir=None,
    to_df=True,
):
    """Processes EEG data for a single participant.

    The raw data is read and cleaned using standard steps (downsampling, bad
    channel interpolation, ocular correction, frequency domain filtering).
    Epochs are created around the `triggers`. Bad epochs are removed based on
    peak-to-peak amplitude. Single trial mean ERP amplitudes for ERP
    `components` of interest are computed and matched to the single trial
    behavioral data from the `log_file`.

    Optionally, this last step is repeated on a time-frequency representation
    (TFR) of the data obtained via Morlet wavelet convolution.

    The result is a single trial data frame which can be used for fitting
    linear mixed-effects models on the mean ERP amplitudes (and power).

    Additionally, condition averages (`evokeds`) for the ERPs (and power) are
    computed to facilitate plotting.

    For details about the pipeline, see Frömer et al. (2018)[1].

    Parameters & returns
    --------------------
    See the README[2] in the GitHub repository for the pipeline.

    Notes
    -----
    [1] https://doi.org/10.3389/fnins.2018.00048
    [2] https://github.com/alexenge/hu-neuro-pipeline/blob/dev/README.md
    """

    # Backup input arguments for re-use
    config = locals()

    # Read raw data
    raw, participant_id = read_raw(vhdr_file)

    # Create backup of the raw data for the HTML report
    if report_dir is not None:
        dirty = raw.copy()

    # Downsample
    if downsample_sfreq is not None:
        sfreq = raw.info['sfreq']
        downsample_sfreq = float(downsample_sfreq)
        print(f'Downsampling from {sfreq} Hz to {downsample_sfreq} Hz')
        raw.resample(downsample_sfreq)

    # Add EOG channels
    raw = add_heog_veog(raw, veog_channels, heog_channels)

    # Apply custom or standard montage
    apply_montage(raw, montage)

    # Handle any bad channels
    raw, interpolated_channels = interpolate_bad_channels(
        raw, bad_channels, auto_bad_channels)

    # Re-reference to common average
    _ = raw.set_eeg_reference('average')

    # Do ocular correction with BESA and/or ICA
    if besa_file is not None:
        raw = correct_besa(raw, besa_file)
    if ica_method is not None:
        raw, ica = correct_ica(raw, ica_method, ica_n_components)
    else:
        ica = None

    # Filtering
    filt = raw.copy().filter(highpass_freq, lowpass_freq)

    # Determine events and the corresponding (selection of) triggers
    events, event_id = events_from_annotations(
        filt, regexp='Stimulus', verbose=False)
    if triggers is not None:
        event_id = triggers_to_event_id(triggers)

    # Epoching including baseline correction
    if baseline is not None:
        baseline = tuple(baseline)
    epochs = Epochs(filt, events, event_id, epochs_tmin, epochs_tmax, baseline,
                    preload=True)

    # Automatically detect bad channels and interpolate if necessary
    if bad_channels == 'auto' and auto_bad_channels is None:
        auto_bad_channels = get_bad_channels(epochs)
        config['auto_bad_channels'] = auto_bad_channels
        if auto_bad_channels != []:
            print('Restarting with interpolation of bad channels')
            return participant_pipeline(**config)

    # Add bad ICA components to config
    if ica is not None:
        if ica_n_components < 1.0:
            config['auto_ica_n_components'] = int(ica.n_components_)
        config['auto_ica_bad_components'] = [int(x) for x in ica.exclude]

    # Drop the last sample to produce a nice even number
    _ = epochs.crop(epochs_tmin, epochs_tmax, include_tmax=False)
    print(epochs.__str__().replace(u"\u2013", "-"))

    # Read behavioral log file and match to the epochs
    log = read_log(log_file, skip_log_rows, skip_log_conditions)
    if triggers_column is not None:
        log = match_log_to_epochs(epochs, log, triggers_column)
    epochs.metadata = log
    epochs.metadata.insert(0, column='participant_id', value=participant_id)

    # If log file was provided as a DataFrame, convert to dict for config
    if isinstance(config['log_file'], pd.DataFrame):
        config['log_file'] = config['log_file'].to_dict(orient='list')

    # Get indices of bad epochs
    bad_ixs = get_bad_epochs(epochs, reject_peak_to_peak)
    config['auto_rejected_epochs'] = bad_ixs

    # Compute single trial mean ERP amplitudes and add to metadata
    trials = compute_single_trials(epochs, components, bad_ixs)

    # Compute evokeds
    evokeds, evokeds_df = compute_evokeds(
        epochs, average_by, bad_ixs, participant_id)

    # Save cleaned continuous data
    if clean_dir is not None:
        save_clean(filt, clean_dir, participant_id)

    # Save channel locations
    if chanlocs_dir is not None:
        save_montage(epochs, chanlocs_dir)

    # Save epochs as data frame and/or MNE object
    if epochs_dir is not None:
        save_epochs(epochs, epochs_dir, participant_id, to_df)

    # Save evokeds as data frame and/or MNE object
    if evokeds_dir is not None:
        save_evokeds(evokeds, evokeds_df, evokeds_dir, participant_id, to_df)

    # Create and save HTML report
    if report_dir is not None:
        dirty.info['bads'] = interpolated_channels
        report = create_report(participant_id, dirty, ica, filt, events,
                               event_id, epochs, evokeds)
        save_report(report, report_dir, participant_id)

    # Time-frequency analysis
    if perform_tfr:

        # Epoching again without filtering
        epochs_unfilt = Epochs(raw, events, event_id, epochs_tmin, epochs_tmax,
                               baseline, preload=True, verbose=False)

        # Drop the last sample to produce a nice even number
        _ = epochs_unfilt.crop(epochs_tmin, epochs_tmax, include_tmax=False)

        # Copy original metadata
        epochs_unfilt.metadata = epochs.metadata.copy()

        # Optionally subtract evoked activity
        # See, e.g., https://doi.org/10.1016/j.neuroimage.2006.02.034
        if tfr_subtract_evoked:
            subtract_cols = None if tfr_subtract_evoked is True \
                else tfr_subtract_evoked
            epochs_unfilt = subtract_evoked(
                epochs_unfilt, evokeds, cols=subtract_cols)

        # Morlet wavelet convolution
        print('Doing time-frequency transform with Morlet wavelets')
        tfr = tfr_morlet(epochs_unfilt, tfr_freqs, tfr_cycles, use_fft=True,
                         return_itc=False, average=False)

        # First, divisive baseline correction using the full epoch
        # See https://doi.org/10.3389/fpsyg.2011.00236
        if tfr_mode is not None:
            tfr_modes = \
                ['ratio', 'logratio', 'percent', 'zscore', 'zlogratio']
            assert tfr_mode in tfr_modes, \
                f'`tfr_baseline_mode` must be one of {tfr_modes}'
            tfr.apply_baseline(baseline=(None, None), mode=tfr_mode)

        # Second, additive baseline correction using the prestimulus interval
        if tfr_baseline is not None:
            tfr_baseline = tuple(tfr_baseline)
        tfr.apply_baseline(baseline=tfr_baseline, mode='mean')

        # Reduce numerical precision to reduce object size
        tfr.data = np.float32(tfr.data)

        # Add single trial mean power to metadata
        trials = compute_single_trials_tfr(tfr, tfr_components, bad_ixs)

        # Save single trial data (again)
        if trials_dir is not None:
            save_df(trials, trials_dir, participant_id, suffix='trials')

        # Compute evoked power
        tfr_evokeds, tfr_evokeds_df = compute_evokeds(
            tfr, average_by, bad_ixs, participant_id)

        # Save evoked power
        if tfr_dir is not None:
            save_evokeds(
                tfr_evokeds, tfr_evokeds_df, tfr_dir, participant_id, to_df)

        return trials, evokeds, evokeds_df, config, tfr_evokeds, tfr_evokeds_df

    return trials, evokeds, evokeds_df, config
