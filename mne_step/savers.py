from os import makedirs

import pandas as pd
from mne import write_evokeds


def save_clean(raw, clean_dir, participant_id=''):

    # Re-format participant ID for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = 'cleaned_eeg'

    # Create output folder and save
    makedirs(clean_dir, exist_ok=True)
    fname = f'{clean_dir}/{participant_id_}{suffix}.fif'
    raw.save(fname)


def save_df(df, output_dir, participant_id='', suffix=''):

    # Create output folder
    makedirs(output_dir, exist_ok=True)

    # Re-format participant ID and suffix for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = '' if suffix == '' else suffix

    # Save DataFrame
    fname = f'{output_dir}/{participant_id_}{suffix}.csv'
    df.to_csv(
        fname, na_rep='NA', float_format='%.4f', index=False)


def save_epochs(epochs, epochs_dir, participant_id='', to_df=True):

    # Create output folder
    makedirs(epochs_dir, exist_ok=True)

    # Re-format participant ID for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = 'epo'

    # Convert to DataFrame
    if to_df is True or to_df == 'both':
        scalings = {'eeg': 1e6, 'misc': 1e6}
        epochs_df = epochs.to_data_frame(scalings=scalings)

        # Add metadata from log file
        metadata_df = epochs.metadata.copy()
        metadata_df = metadata_df.drop([col for col in metadata_df.columns
                                        if col in epochs_df.columns], axis=1)
        n_samples = len(epochs.times)
        metadata_df = metadata_df.loc[metadata_df.index.repeat(n_samples)]
        metadata_df = metadata_df.reset_index(drop=True)
        epochs_df = pd.concat([metadata_df, epochs_df], axis=1)

        # Save DataFrame
        save_df(epochs_df, epochs_dir, participant_id, suffix)

    # Save as MNE object
    if to_df is False or to_df == 'both':
        fname = f'{epochs_dir}/{participant_id_}{suffix}.fif'
        epochs.save(fname, overwrite=True)


def save_evokeds_dict(
        evokeds_dict, evokeds_dir, participant_id='', to_df=True):

    # Save each set of evokeds and/or evokeds_df in the dict
    for suffix, evokeds_tuple in evokeds_dict.items():
        evokeds = evokeds_tuple[0]
        evokeds_df = evokeds_tuple[1]
        save_evokeds(
            evokeds, evokeds_df, evokeds_dir, participant_id, suffix, to_df)


def save_evokeds(evokeds, evokeds_df, evokeds_dir, participant_id='',
                 suffix='', to_df=True):

    # Create output directory
    makedirs(evokeds_dir, exist_ok=True)

    # Re-format participant ID and suffix for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = 'ave' if suffix == '' else f'{suffix}_ave'

    # Save evokeds as DataFrame
    if to_df is True or to_df == 'both':
        save_df(evokeds_df, evokeds_dir, participant_id, suffix)

    # Save evokeds as MNE object
    if to_df is False or to_df == 'both':
        fname = f'{evokeds_dir}/{participant_id_}{suffix}.fif'
        write_evokeds(fname, evokeds, verbose=False)


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
    save_df(coords_df, export_dir, suffix='channel_locations')
