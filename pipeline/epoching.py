from collections import Counter

import chardet
import numpy as np
import pandas as pd
from mne import pick_channels
from mne.channels import combine_channels


def events_from_triggers(triggers):
    """Convert list or dict of triggers to MNE-style event_id"""

    # Convert list to dict with triggers as condition names
    if isinstance(triggers, list):
        triggers = {str(trigger): trigger for trigger in triggers}

    # Make sure that trigger values are integers (R would pass them as floats)
    triggers = {key: int(value) for key, value in triggers.items()}
    event_id = triggers

    return event_id


def read_log(log_file, skip_log_rows=None, skip_log_conditions=None):
    """Reads the behavioral log file with information about each EEG trial."""

    # Check if data are already in a DataFrame
    if isinstance(log_file, pd.DataFrame):
        log = log_file
    else:

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

    # Remove rows via indices (e.g., if the EEG was paused accidently)
    if skip_log_rows is not None:
        log = log.drop(skip_log_rows)

    # Remove rows via conditions (e.g., for filler stimuli without triggers)
    if skip_log_conditions is not None:
        assert isinstance(skip_log_conditions, dict), \
            '"skip_log_conditions" must be a dict ({column: [conditions]})'
        for col, values in skip_log_conditions.items():
            if not isinstance(values, list):
                log = log[log[col] != values]
            else:
                log = log[~log[col].isin(values)]

    return log


def get_bads(
        epochs, reject_peak_to_peak=None, reject_flat=None, percent_bad=0.05):
    """Detects bad epochs/channels based on peak-to-peak and flat amplitude."""

    # Convert thresholds to volts in dicts
    if reject_peak_to_peak is not None:
        reject_peak_to_peak = {'eeg': reject_peak_to_peak * 1e-6}
    if reject_flat is not None:
        reject_flat = {'eeg': reject_flat * 1e-6}

    # Reject on a copy of the data
    epochs_rej = epochs.copy().drop_bad(reject_peak_to_peak, reject_flat)
    drop_log = [elem for elem in epochs_rej.drop_log if elem != ('IGNORED',)]
    bad_tuples = [(ix, elem) for ix, elem in enumerate(drop_log) if elem != ()]

    # Get bad epochs from tuples
    bad_ixs = [bad_tuple[0] for bad_tuple in bad_tuples]

    # Get channels that are responsible for the bad epochs
    bad_channels = [bad_tuple[1] for bad_tuple in bad_tuples]
    bad_channels = list(sum(bad_channels, ()))  # Makes it a flat list

    # See which channels are responsible for at least X percent of epochs
    counts = Counter(bad_channels)
    bad_channels = [ch for ch, count in counts.items()
                    if count > len(epochs) * percent_bad]

    return (bad_ixs, bad_channels)


def compute_single_trials(epochs, components, bad_ixs=None):
    """Computes single trial mean amplitudes a dict of multiple components."""

    # Check that values in the dict are lists
    if not isinstance(components['name'], list):
        components = {key: [value] for key, value in components.items()}

    # Loop over components
    components_df = pd.DataFrame(components)
    for _, component in components_df.iterrows():

        # Compute single trial mean ERP amplitudes
        compute_component(
            epochs, component['name'], component['tmin'],
            component['tmax'], component['roi'], bad_ixs)

    return epochs.metadata


def compute_component(epochs, name, tmin, tmax, roi, bad_ixs=None):
    """Computes single trial mean amplitudes for single component."""

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
