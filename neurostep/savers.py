from os import makedirs

import pandas as pd
from mne import write_evokeds


def save_clean(raw, clean_dir, participant_id):

    # Create output folder and save
    makedirs(clean_dir, exist_ok=True)
    fname = f'{clean_dir}/{participant_id}_cleaned_eeg.fif'
    raw.save(fname)


def save_epochs(epochs, epochs_dir, participant_id, to_df=True):

    # Create output folder
    makedirs(epochs_dir, exist_ok=True)

    # Convert to DataFrame
    if to_df is True or to_df == 'both':
        scalings = {'eeg': 1e6, 'misc': 1e6}
        epochs_df = epochs.to_data_frame(scalings=scalings)

        # Add metadata from log file
        metadata_df = epochs.metadata
        n_samples = len(epochs.times)
        metadata_df = metadata_df.loc[metadata_df.index.repeat(n_samples)]
        metadata_df = metadata_df.reset_index(drop=True)
        epochs_df = pd.concat([metadata_df, epochs_df], axis=1)

        # Save DataFrame
        fname = f'{epochs_dir}/{participant_id}_epo.csv'
        epochs_df.to_csv(
            fname, na_rep='NA', float_format='%.4f', index=False)

    # Save as MNE object
    if to_df is False or to_df == 'both':
        fname = f'{epochs_dir}/{participant_id}_epo.fif'
        epochs.save(fname)


def save_evokeds(
        evokeds, evokeds_df, evokeds_dir, participant_id, suffix, to_df=True):

    # Create output directory
    makedirs(evokeds_dir, exist_ok=True)

    # Prepare suffix with underscore for file name
    suffix = f'_{suffix}' if suffix != '' else suffix

    # Save evokeds as DataFrame
    if to_df is True or to_df == 'both':
        fname = f'{evokeds_dir}/{participant_id}{suffix}_ave.csv'
        evokeds_df.to_csv(
            fname, na_rep='NA', float_format='%.4f', index=False)

    # Save evokeds as MNE object
    if to_df is False or to_df == 'both':
        fname = f'{evokeds_dir}/{participant_id}_ave.fif'
        write_evokeds(fname, evokeds)


def save_montage(epochs, export_dir):

    # Create output directory
    makedirs(export_dir, exist_ok=True)

    # Get locations of EEG channels
    chs = epochs.copy().pick_types(eeg=True).info['chs']
    coords = [ch['loc'][0:3] for ch in chs]
    coords_df = pd.DataFrame(columns=['x', 'y', 'z'], data=coords)

    # Add channel names
    ch_names = [ch['ch_name'] for ch in chs]
    coords_df.insert(loc=0, column='ch_name', value=ch_names)

    # Save
    fname = f'{export_dir}/channel_locations.csv'
    coords_df.to_csv(
        fname, na_rep='NA', float_format='%.4f', index=False)
