from os import path
from sys import exit

import chardet
import numpy as np
import pandas as pd
from mne import EpochsArray, pick_channels, set_bipolar_reference
from mne.channels import (combine_channels, make_standard_montage,
                          read_custom_montage)
from mne.preprocessing import ICA


def add_heog_veog(raw, heog_channels='auto', veog_channels='auto'):

    # Add bipolar HEOG channel
    if heog_channels is not None:
        if heog_channels == 'auto':
            heog_channels = ['F9', 'F10', 'Afp9', 'Afp10']
        raw = add_eog(raw, heog_channels, new_name='HEOG')

    # Add bipolar VEOG channel
    if veog_channels is not None:
        if veog_channels == 'auto':
            veog_channels = ['Fp1', 'FP1', 'Auge_u', 'IO1']
        raw = add_eog(raw, veog_channels, new_name='VEOG')

    return raw


def add_eog(raw, channels, new_name):

    # Check that exactly two of the provided channels are in the data
    channels = [ch for ch in channels if ch in raw.ch_names]
    if len(channels) != 2:
        exit(f'Could not find two channels for computing bipolar {new_name}. '
             'Please provide different channel names or choose None.')

    # Compute bipolar EOG channel
    anode = channels[0]
    cathode = channels[1]
    print(f'Adding bipolar channel {new_name} ({anode} - {cathode})')
    raw = set_bipolar_reference(
        raw, anode, cathode, new_name, drop_refs=False, verbose=False)
    raw = raw.set_channel_types({new_name: 'eog'})

    return raw


def apply_montage(raw, montage):

    # Load custom montage from file
    if path.isfile(montage):
        print(f'Loading custom montage from {montage}')
        digmontage = read_custom_montage(montage)

    # Or load standard montage
    else:
        print(f'Loading standard montage {montage}')
        digmontage = make_standard_montage(montage)

    # Make sure that EOG channels are of the correct type
    for channel_name in ['HEOG', 'VEOG']:
        if channel_name in raw.ch_names:
            raw.set_channel_types({channel_name: 'eog'})

    # Remove channels from the data that are not in the montage
    raw_channels = set(raw.ch_names)
    montage_channels = set(digmontage.ch_names)
    eog_channels = set(['HEOG', 'VEOG'])
    drop_channels = list(raw_channels - montage_channels - eog_channels)
    print(f'Removing channels that are not in the montage {drop_channels}')
    raw.drop_channels(drop_channels)

    # Apply montage
    raw.set_montage(digmontage)


def correct_ica(raw, n_components=15, random_seed=1234, method='fastica'):

    # Run ICA on a copy of the data
    raw_filt_ica = raw.copy()
    raw_filt_ica.load_data().filter(l_freq=1, h_freq=None, verbose=False)
    ica = ICA(
        n_components, random_state=random_seed, method=method, max_iter='auto')
    ica.fit(raw_filt_ica)

    # Remove bad components from the raw data
    eog_indices, _ = ica.find_bads_eog(raw, verbose=False)
    ica.exclude = eog_indices
    raw = ica.apply(raw)


def correct_besa(raw, besa_file):

    # Read BESA matrix
    print(f'Doing ocular correction with MSEC (BESA)')
    besa_matrix = pd.read_csv(besa_file, delimiter='\t', index_col=0)

    # Get EEG channel labels that are present in the data
    eeg_channels = raw.copy().pick_types(eeg=True).ch_names

    # Convert EEG channel labels to uppercase
    eeg_upper = pd.Series(eeg_channels).str.upper().values

    # Also convert BESA matrix labels to uppercase
    besa_matrix.index = besa_matrix.index.str.upper()
    besa_matrix.columns = besa_matrix.columns.str.upper()

    # Match so that the BESA matrix only contains channels that are in the data
    row_channels = [ch for ch in besa_matrix.index if ch in eeg_upper]
    col_channels = [ch for ch in besa_matrix.columns if ch in eeg_upper]
    besa_matrix = besa_matrix.reindex(index=row_channels, columns=col_channels)

    # Apply BESA matrix to the data
    eeg_data, _ = raw[eeg_channels]
    eeg_data = besa_matrix.values.dot(eeg_data)
    raw[eeg_channels] = eeg_data


def read_log(log_file, skip_log_rows=None):

    # Detect file encoding
    with open(log_file, 'rb') as f:
        data = f.read()
    chardet_res = chardet.detect(data)
    encoding = chardet_res['encoding']

    # Read into DataFrame
    if '.csv' in log_file:
        log = pd.read_csv(log_file, encoding=encoding)
    else:
        log = pd.read_csv(log_file, delimiter='\t', encoding=encoding)

    # Remove rows that are not present in the EEG data
    if isinstance(skip_log_rows, list):
        log = log.drop(skip_log_rows)
    elif isinstance(skip_log_rows, dict):
        for column, values in skip_log_rows.items():
            if not isinstance(values, list):
                log = log[log[column] != values]
            else:
                log = log[~log[column].isin(values)]

    return log


def get_bad_ixs(epochs, reject_peak_to_peak=None, reject_flat=None):

    # Convert thresholds to volts in dicts
    if reject_peak_to_peak is not None:
        reject_peak_to_peak = {'eeg': reject_peak_to_peak * 1e-6}
    if reject_flat is not None:
        reject_flat = {'eeg': reject_flat * 1e-6}

    # Reject on a copy of the data
    epochs_rej = epochs.copy().drop_bad(reject_peak_to_peak, reject_flat)
    drop_log = [elem for elem in epochs_rej.drop_log if elem != ('IGNORED',)]
    bad_ixs = [ix for ix, elem in enumerate(drop_log) if elem != ()]

    return bad_ixs


def bad_epochs_to_nan(epochs, reject_peak_to_peak=None, reject_flat=None):

    # Convert thresholds to volts in dicts
    if reject_peak_to_peak is not None:
        reject_peak_to_peak = {'eeg': reject_peak_to_peak * 1e-6}
    if reject_flat is not None:
        reject_flat = {'eeg': reject_flat * 1e-6}

    # Get indices of epochs that are to be rejected
    epochs_rej = epochs.copy().drop_bad(reject_peak_to_peak, reject_flat)
    drop_log = [elem for elem in epochs_rej.drop_log if elem != ('IGNORED',)]
    drop_ixs = [ix for ix, elem in enumerate(drop_log) if elem != ()]

    # Create new epochs object with rejected epochs set to NaN
    data = epochs.get_data()
    data[drop_ixs] = np.nan
    epochs_clean = EpochsArray(
        data, info=epochs.info, events=epochs.events, tmin=epochs.tmin,
        event_id=epochs.event_id, baseline=epochs.baseline,
        metadata=epochs.metadata, verbose=False)

    return epochs_clean


def compute_single_trials(epochs, components_df, bad_ixs=None):

    # Compute single trial mean ERP amplitudes for each component
    for _, component in components_df.iterrows():
        compute_component(
            epochs, component['name'], component['tmin'],
            component['tmax'], component['roi'], bad_ixs)


def compute_component(epochs, name, tmin, tmax, roi, bad_ixs=None):

    # Create virtual channel for the average in the region of interest
    print(f'Computing single trial ERP amplitudes for {name}')
    roi_dict = {name: pick_channels(epochs.ch_names, roi)}
    backup_verbose = epochs.verbose
    epochs.verbose = False
    epochs_roi = combine_channels(epochs, roi_dict)
    epochs.add_channels([epochs_roi], force_update_info=True)
    epochs.set_channel_types({name: 'misc'})
    epochs.verbose = backup_verbose

    # Compute mean amplitudes by averaging across the relevant time window
    epochs_roi.crop(tmin, tmax)
    df = epochs_roi.to_data_frame()
    mean_amp = df.groupby('epoch')[name].mean()

    # Set ERPs for bad epochs to NaN
    if bad_ixs is not None:
        if isinstance(bad_ixs, int):
            bad_ixs = [bad_ixs]
        mean_amp[bad_ixs] = np.nan

    # Add as a new column to the original metadata
    epochs.metadata.reset_index(drop=True, inplace=True)
    epochs.metadata = pd.concat([epochs.metadata, mean_amp], axis=1)


def compute_evokeds(epochs, average_by=None, bad_ixs=None):

    # Drop bad epochs before averaging
    if bad_ixs is not None:
        if isinstance(bad_ixs, int):
            bad_ixs = [bad_ixs]
        epochs_good = epochs.copy().drop(bad_ixs, verbose=False)
    else:
        epochs_good = epochs

    # Prepare empty lists
    all_evokeds = []
    all_evokeds_dfs = []

    # Either average by columns in the metadata / log file
    if average_by is not None:

        # Make sure average_by is a list
        if isinstance(average_by, str):
            average_by = [average_by]

        # Get unique combinations of conditions
        conditions = epochs_good.metadata[average_by].drop_duplicates()

        # Compute evoked averages for each condition
        for _, condition in conditions.iterrows():

            # Construct query for the current condition
            query = [f'{key} == \'{value}\''
                     for key, value in condition.iteritems()]
            query = ' & '.join(query)

            # Average the relevant epochs
            evokeds = epochs_good[query].average(picks=['eeg', 'misc'])
            comment = '/'.join([str(value) for value in condition])
            evokeds.comment = comment
            all_evokeds.append(evokeds)

            # Create DataFrame
            scalings = {'eeg': 1e6, 'misc': 1e6}
            evokeds_df = evokeds.to_data_frame(scalings=scalings)

            # Add additional columns for the condition
            condition_df = condition.to_frame().transpose()
            nrows = len(evokeds_df)
            condition_df = pd.concat([condition_df] * nrows, ignore_index=True)
            evokeds_df = pd.concat([condition_df, evokeds_df], axis=1)
            all_evokeds_dfs.append(evokeds_df)

    # Or average by events / triggers
    else:
        for id in epochs_good.event_id:

            # Average the relevant epochs
            evokeds = epochs_good[id].average(picks=['eeg', 'misc'])
            all_evokeds.append(evokeds)

            # Create DataFrame
            scalings = {'eeg': 1e6, 'misc': 1e6}
            evokeds_df = evokeds.to_data_frame(scalings=scalings)
            evokeds_df.insert(loc=0, column='event_id', value=id)
            all_evokeds_dfs.append(evokeds_df)

    # Combine DataFrames
    all_evokeds_df = pd.concat(all_evokeds_dfs)

    return all_evokeds, all_evokeds_df
