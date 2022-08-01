from os import path

import pandas as pd
from mne import set_bipolar_reference
from mne.channels import make_standard_montage, read_custom_montage
from mne.preprocessing import ICA


def add_heog_veog(raw, veog_channels='auto', heog_channels='auto'):
    """Adds virtual VEOG and HEOG using default or non-default EOG names."""

    # Add bipolar VEOG channel
    if veog_channels is not None:
        if veog_channels == 'auto':
            veog_channels = ['Fp1', 'FP1', 'Auge_u', 'IO1']
        raw = add_eog(raw, veog_channels, new_name='VEOG')

    # Add bipolar HEOG channel
    if heog_channels is not None:
        if heog_channels == 'auto':
            heog_channels = ['F9', 'F10', 'Afp9', 'Afp10']
        raw = add_eog(raw, heog_channels, new_name='HEOG')

    return raw


def add_eog(raw, channels, new_name):
    """Computes a single bipolar EOG channel from a list of possible names."""

    # Check that exactly two of the provided channels are in the data
    channels = [ch for ch in channels if ch in raw.ch_names]
    assert len(channels) == 2, (
        'Could not find exactly two channels for computing bipolar '
        f'{new_name}. Please provide different channel names or choose `None`')

    # Compute bipolar EOG channel
    anode = channels[0]
    cathode = channels[1]
    print(f'Adding bipolar channel {new_name} ({anode} - {cathode})')
    raw = set_bipolar_reference(
        raw, anode, cathode, new_name, drop_refs=False, verbose=False)
    raw = raw.set_channel_types({new_name: 'eog'})

    return raw


def apply_montage(raw, montage):
    """Reads channel locations from custom file or standard montage."""

    # Load custom montage from file
    if path.isfile(montage):
        print(f'Loading custom montage from {montage}')
        digmontage = read_custom_montage(montage)

    # Or load standard montage
    else:
        print(f'Loading standard montage {montage}')
        digmontage = make_standard_montage(montage)

    # Make sure that EOG channels are of the `eog` type
    eog_channels = ['HEOG', 'VEOG', 'IO1', 'IO2', 'Afp9', 'Afp10', 'Auge_u']
    for ch_name in eog_channels:
        if ch_name in raw.ch_names:
            raw.set_channel_types({ch_name: 'eog'})

    # Make sure that mastoid channels are of the `misc` type
    misc_channels = ['A1', 'A2', 'M1', 'M2']
    for ch_name in misc_channels:
        if ch_name in raw.ch_names:
            raw.set_channel_types({ch_name: 'misc'})

    # Drop EEG channels that are not in the montage
    raw_channels = set(raw.copy().pick_types(eeg=True).ch_names)
    montage_channels = set(digmontage.ch_names)
    drop_channels = list(raw_channels - montage_channels)
    if drop_channels != []:
        print(f'Removing channels that are not in the montage {drop_channels}')
        raw.drop_channels(drop_channels)

    # Apply montage
    raw.set_montage(digmontage)


def interpolate_bad_channels(raw, bad_channels=None, auto_bad_channels=None):
    """Interpolates any channels from the two lists."""

    # Combine lists of bad channels
    all_bad_channels = []
    if bad_channels is not None and bad_channels != 'auto':
        all_bad_channels += bad_channels
    if auto_bad_channels is not None:
        all_bad_channels += auto_bad_channels

    # Interpolate bad channels
    if all_bad_channels != []:
        raw.info['bads'] += auto_bad_channels
        raw = raw.interpolate_bads()

    return raw, all_bad_channels


def correct_ica(raw, method='fastica', n_components=0.99, random_seed=1234):
    """Corrects ocular artifacts using ICA and automatic component removal."""

    # Run ICA on a copy of the data
    raw_filt_ica = raw.copy()
    raw_filt_ica.load_data().filter(l_freq=1, h_freq=None, verbose=False)
    ica = ICA(
        n_components, random_state=random_seed, method=method, max_iter='auto')
    ica.fit(raw_filt_ica)

    # Remove bad components from the raw data
    eog_indices, _ = ica.find_bads_eog(
        raw, ch_name=['HEOG', 'VEOG'], verbose=False)
    ica.exclude = eog_indices
    raw = ica.apply(raw)

    return raw, ica


def correct_besa(raw, besa_file):
    """Corrects ocular artifacts using a pre-computed MSEC (BESA) matrix."""

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

    return raw
