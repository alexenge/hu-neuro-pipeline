from os import makedirs, path

import pandas as pd
from mne import Epochs, events_from_annotations, write_evokeds
from mne.io import read_raw_brainvision

from helpers import (add_heog_veog, apply_montage, compute_evokeds,
                     compute_single_trials, correct_besa, correct_ica,
                     get_bad_ixs, read_log)

# aha example
aha_dict = dict(
    vhdr_file='/Users/alexander/Research/aha/data/raw/eeg/exp1/Vp0002.vhdr',
    log_file='/Users/alexander/Research/aha/data/raw/rt/exp1/VP_02_Tag1.txt',
    downsample_sfreq=250,
    veog_channels='auto',
    heog_channels='auto',
    montage='easycap-M1',
    ocular_correction='/Users/alexander/Research/aha/data/raw/eeg/exp1/cali/Vp0002_cali.matrix',
    highpass_freq=0.1,
    lowpass_freq=30,
    epochs_tmin=-0.5,
    epochs_tmax=1.5,
    baseline=(-0.2, 0),
    triggers={'match': 221, 'mismatch': 222},
    skip_log_rows={'bek_unbek': 'bekannt'},
    reject_peak_to_peak=200,
    reject_flat=1,
    components_df=pd.DataFrame({'name': ['P1', 'N1', 'N400'],
                                'tmin': [0.1, 0.15, 0.4],
                                'tmax': [0.15, 0.2, 0.7],
                                'roi': [
                                    ['PO3', 'PO4', 'POz', 'O1', 'O2', 'Oz'],
                                    ['P7', 'P8', 'PO7', 'PO8', 'PO9', 'PO10'],
                                    ['C1', 'C2', 'Cz', 'CP1', 'CP2', 'CPz']]}),
    condition_cols=['Wdh', 'Bed'],
    clean_dir=None,
    epochs_dir='/Users/alexander/Research/aha/data/test/epochs',
    trials_dir='/Users/alexander/Research/aha/data/test/trials',
    evokeds_dir='/Users/alexander/Research/aha/data/test/evokeds',
    to_df='both',
)
locals().update(aha_dict)

# ManyPipelines example
manypipelines_dict = dict(
    vhdr_file='/Users/alexander/Research/manypipelines/Results/EEG/raw/EMP01.vhdr',
    log_file='/Users/alexander/Research/manypipelines/Results/Behavior/EMP01_events.csv',
    downsample_sfreq=256, veog_channels=None, heog_channels=None,
    montage='/Users/alexander/Research/manypipelines/Results/EEG/channel_locations/chanlocs_besa.txt',
    ocular_correction='fastica', highpass_freq=0.1, lowpass_freq=30,
    epochs_tmin=-0.5, epochs_tmax=1.5, baseline=(-0.2, 0),
    triggers=None, skip_log_rows=None, reject_peak_to_peak=200, reject_flat=1,
    components_df=pd.DataFrame(
        {'name': ['N1'],
         'tmin': [0.15],
         'tmax': [0.2],
         'roi': [['P7', 'P8', 'PO7', 'PO8', 'PO9', 'PO10']]}),
    condition_cols={'h1': 'scene_category', 'h2': 'old', 'h3': 'behavior',
                    'h4': 'subsequent_memory'},
    clean_dir=None, epochs_dir=None,
    trials_dir='/Users/alexander/Research/manypipelines/Results/EEG/trials',
    evokeds_dir='/Users/alexander/Research/manypipelines/Results/EEG/evokeds',
    to_df=True,)
locals().update(manypipelines_dict)


def preprocess(
    vhdr_file=None,
    log_file=None,
    downsample_sfreq=None,
    veog_channels='auto',
    heog_channels='auto',
    montage='easycap-M1',
    ocular_correction='fastica',
    highpass_freq=0.1,
    lowpass_freq=30,
    epochs_tmin=-0.5,
    epochs_tmax=1.5,
    baseline=(-0.2, 0),
    triggers=None,
    skip_log_rows=None,
    reject_peak_to_peak=200,
    reject_flat=1,
    components_df=pd.DataFrame({
        'name': [], 'tmin': [], 'tmax': [], 'roi': []}),
    condition_cols=None,
    clean_dir=None,
    epochs_dir=None,
    trials_dir=None,
    evokeds_dir=None,
    to_df=True,
):

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
        makedirs(clean_dir, exist_ok=True)
        fname = f'{clean_dir}/{participant_id}_cleaned_eeg.fif'
        raw.save(fname)

    # Determine events and the corresponding (selection of) triggers
    events, event_id = events_from_annotations(
        raw, regexp='Stimulus', verbose=False)
    event_id = triggers if triggers is not None else event_id

    # Epoching including baseline correction
    epochs = Epochs(raw, events, event_id, epochs_tmin, epochs_tmax, baseline,
                    preload=True)

    # Drop the last sample to produce a nice even number
    _ = epochs.crop(epochs_tmin, epochs_tmax, include_tmax=False)
    print(epochs)

    # Read behavioral log file
    epochs.metadata = read_log(log_file, skip_log_rows)

    # # Reject bad epochs despite based on peak to peak and flat amplitude
    # epochs = _bad_epochs_to_nan(epochs, reject_peak_to_peak, reject_flat)

    # Get indices of bad epochs
    bad_ixs = get_bad_ixs(epochs, reject_peak_to_peak, reject_flat)

    # Add single trial mean ERP amplitudes to metadata
    compute_single_trials(epochs, components_df, bad_ixs)

    # Save epochs as data frame or MNE object
    if epochs_dir is not None:
        makedirs(epochs_dir, exist_ok=True)
        if to_df is True or to_df == 'both':
            scalings = {'eeg': 1e6, 'misc': 1e6}
            epochs_df = epochs.to_data_frame(scalings=scalings)
            metadata_df = epochs.metadata
            n_samples = len(epochs.times)
            metadata_df = metadata_df.loc[metadata_df.index.repeat(n_samples)]
            metadata_df = metadata_df.reset_index(drop=True)
            epochs_df = pd.concat([metadata_df, epochs_df], axis=1)
            fname = f'{epochs_dir}/{participant_id}_epo.csv'
            epochs_df.to_csv(
                fname, na_rep='NA', float_format='%.4f', index=False)
        if to_df is False or to_df == 'both':
            fname = f'{epochs_dir}/{participant_id}_epo.fif'
            epochs.save(fname)

    # Save single trial behavioral and ERP data
    if trials_dir is not None:
        makedirs(trials_dir, exist_ok=True)
        fname = f'{trials_dir}/{participant_id}_trials.csv'
        epochs.metadata.to_csv(
            fname, na_rep='NA', float_format='%.4f', index=False)

    # For computing evokeds, make sure columns to average by are in a dict
    if not isinstance(condition_cols, dict):
        condition_cols = {'': condition_cols}

    # Compute one set of evokeds for each (combination of) condition(s)
    for suffix, cols in condition_cols.items():
        evokeds, evokeds_df = compute_evokeds(epochs, cols, bad_ixs)
        if evokeds_dir is not None:
            makedirs(evokeds_dir, exist_ok=True)
            suffix = f'_{suffix}' if suffix != '' else suffix
            if to_df is True or to_df == 'both':
                fname = f'{evokeds_dir}/{participant_id}{suffix}_ave.csv'
                evokeds_df.to_csv(
                    fname, na_rep='NA', float_format='%.4f', index=False)
            if to_df is False or to_df == 'both':
                fname = f'{evokeds_dir}/{participant_id}_ave.fif'
                write_evokeds(fname, evokeds)

    return epochs


# Test run
epochs = preprocess(**manypipelines_dict)
