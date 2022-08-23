import json
import re
from glob import glob
from os import makedirs, path

import pandas as pd
from mne import Evoked, write_evokeds
from mne.channels.layout import _find_topomap_coords
from mne.io import concatenate_raws, read_raw_brainvision
from mne.time_frequency import AverageTFR, write_tfrs


def read_raw(vhdr_file_or_files):
    """Reads one or more raw EEG datasets from the same participant."""

    # Read raw datasets and combine if a list was provided
    if isinstance(vhdr_file_or_files, list):
        vhdr_files = vhdr_file_or_files
        print(f'\n=== Reading and combining raw data from {vhdr_files} ===')
        raw_list = [read_raw_brainvision(f) for f in vhdr_files]
        raw = concatenate_raws(raw_list)
        participant_id = get_participant_id(vhdr_files)

    # Read raw dataset if only a single one was provided
    else:
        vhdr_file = vhdr_file_or_files
        print(f'\n=== Reading raw data from {vhdr_file} ===')
        raw = read_raw_brainvision(vhdr_file, preload=True)
        participant_id = get_participant_id(vhdr_file)

    return raw, participant_id


def get_participant_id(vhdr_file_or_files):
    """Extracts the basename of an input file to use as participant ID."""

    # Extract participant ID from raw data file name(s)
    if isinstance(vhdr_file_or_files, list):
        vhdr_files = vhdr_file_or_files
        participant_id = [path.basename(f).split('.')[0] for f in vhdr_files]
        participant_id = '_'.join(participant_id)
    else:
        vhdr_file = vhdr_file_or_files
        participant_id = path.basename(vhdr_file).split('.')[0]

    return participant_id


def files_from_dir(dir_path, extensions, natsort_files=True):
    """Retrieves files matching pattern(s) from a given parent directory."""

    # Find all files with one of the right extensions
    assert path.isdir(dir_path), f'Didn\'t find directory `{dir_path}`!'
    files = []
    for extension in extensions:
        files += glob(f'{dir_path}/*.{extension}')

    # Sort naturally because some files might not have leading zeros
    if natsort_files:
        natsort = lambda s: [
            int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)]
        files = sorted(files, key=natsort)

    return files


def convert_participant_input(input, participant_ids):
    """Converts different inputs (e.g., dict) into a per-participant list."""

    # If it's a dict, convert to list
    if isinstance(input, dict):
        participant_dict = {id: None for id in participant_ids}
        for id, values in input.items():
            assert id in participant_ids, \
                f'Participant ID {id} is not in vhdr_files'
            participant_dict[id] = values
        return participant_dict.values()

    # If it's a list of list, it must have the same length as participant_ids
    elif is_nested_list(input):
        assert len(input) == len(participant_ids), \
            'Input lists must have the same length'
        return input

    # Otherwise all participants get the same values
    else:
        return [input] * len(participant_ids)


def is_nested_list(input):
    """Checks if a list is nested, i.e., contains at least one other list."""

    # Check if there is any list in the list
    if isinstance(input, list):
        return any(isinstance(elem, list) for elem in input)
    else:
        return False


def save_clean(raw, output_dir, participant_id=''):
    """Saves cleaned (continuous) EEG data in `.fif` format."""

    # Re-format participant ID for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = 'cleaned_eeg'

    # Create output folder and save
    makedirs(output_dir, exist_ok=True)
    fname = f'{output_dir}/{participant_id_}{suffix}.fif'
    raw.save(fname)


def save_df(df, output_dir, participant_id='', suffix=''):
    """Saves pd.DataFrame in `.csv` format."""

    # Create output folder
    makedirs(output_dir, exist_ok=True)

    # Re-format participant ID and suffix for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = '' if suffix == '' else suffix

    # Save DataFrame
    fname = f'{output_dir}/{participant_id_}{suffix}.csv'
    df.to_csv(
        fname, na_rep='NA', float_format='%.4f', index=False)


def save_epochs(epochs, output_dir, participant_id='', to_df=True):
    """Saves mne.Epochs with metadata in `.fif` and/or `.csv` format."""

    # Create output folder
    makedirs(output_dir, exist_ok=True)

    # Re-format participant ID for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = 'epo'

    # Convert to DataFrame
    if to_df is True or to_df == 'both':
        scalings = {'eeg': 1e6, 'misc': 1e6}
        epochs_df = epochs.to_data_frame(scalings=scalings, time_format=None)

        # Add metadata from log file
        metadata_df = epochs.metadata.copy()
        metadata_df = metadata_df.drop([col for col in metadata_df.columns
                                        if col in epochs_df.columns], axis=1)
        n_samples = len(epochs.times)
        metadata_df = metadata_df.loc[metadata_df.index.repeat(n_samples)]
        metadata_df = metadata_df.reset_index(drop=True)
        epochs_df = pd.concat([metadata_df, epochs_df], axis=1)

        # Save DataFrame
        save_df(epochs_df, output_dir, participant_id, suffix)

    # Save as MNE object
    if to_df is False or to_df == 'both':
        fname = f'{output_dir}/{participant_id_}{suffix}.fif'
        epochs.save(fname, overwrite=True)


def save_evokeds(
        evokeds, evokeds_df, output_dir, participant_id='', to_df=True):
    """Saves a list of mne.Evokeds in `.fif` and/or `.csv` format."""

    # Re-format participant ID for filename
    participant_id_ = '' if participant_id == '' else f'{participant_id}_'
    suffix = 'ave'

    # Create output directory
    makedirs(output_dir, exist_ok=True)

    # Save evokeds as DataFrame
    if to_df is True or to_df == 'both':
        save_df(evokeds_df, output_dir, participant_id, suffix)

    # Save evokeds as MNE object
    if to_df is False or to_df == 'both':

        # Save evokeds for ERPs
        if isinstance(evokeds[0], Evoked):
            fname = f'{output_dir}/{participant_id_}{suffix}.fif'
            write_evokeds(fname, evokeds, overwrite=True, verbose=False)

        # Save vokeds for TFR
        elif isinstance(evokeds[0], AverageTFR):
            fname = f'{output_dir}/{participant_id_}{suffix}.h5'
            write_tfrs(fname, evokeds, overwrite=True, verbose=False)


def save_montage(epochs, output_dir):
    """Saves channel locations in `.csv` format."""

    # Create output directory
    makedirs(output_dir, exist_ok=True)

    # Get locations of EEG channels
    chs = epochs.copy().pick_types(eeg=True).info['chs']
    coords = [ch['loc'][0:3] for ch in chs]
    coords_df = pd.DataFrame(
        columns=['cart_x', 'cart_y', 'cart_z'], data=coords)

    # Add channel names
    ch_names = [ch['ch_name'] for ch in chs]
    coords_df.insert(loc=0, column='channel', value=ch_names)

    # Add 2D flattened coordinates
    # Multiplied to mm scale (with head radius =~ 95 mm as in R-eegUtils)
    coords_df[['x', 'y']] = _find_topomap_coords(epochs.info, ch_names) * 947

    # Save
    save_df(coords_df, output_dir, suffix='channel_locations')


def save_config(config, output_dir):
    """Saves dict of pipeline config options in `.json` format."""

    # Create output directory
    makedirs(output_dir, exist_ok=True)

    # Save
    fname = f'{output_dir}/config.json'
    with open(fname, 'w') as f:
        json.dump(config, f, indent=4)


def save_report(report, output_dir, participant_id):
    """Saves HTML report."""

    # Create output directory
    makedirs(output_dir, exist_ok=True)

    # Save
    fname = f'{output_dir}/{participant_id}_report.html'
    print(f'Saving HTML report to {fname}')
    _ = report.save(fname, open_browser=False, overwrite=True)
