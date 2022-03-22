import chardet
import numpy as np
import pandas as pd
from mne import combine_evoked, pick_channels, set_log_level
from mne.channels import combine_channels
from scipy.stats import zscore


def triggers_to_event_id(triggers):
    """Convert list or dict of triggers to MNE-style event_id"""

    # Convert list to dict with triggers as condition names
    if isinstance(triggers, list):
        triggers = {str(trigger): trigger for trigger in triggers}
    else:
        assert isinstance(triggers, dict), \
            '`triggers` must be either list or dict'

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


def match_log_to_epochs(epochs, log, triggers_column, depth=10):
    """Auto-detects missing EEG trials and removes them from the log file."""

    # Make sure that the requested column is available in the log file
    assert triggers_column in log.columns, \
        f'Column \'{triggers_column}\' is not in the log file'

    # Read lists of triggers from log file and EEG epochs
    events_log = log[triggers_column].tolist()
    events_epochs = list(epochs.events[:, 2])

    # Check for each row in the log file
    previous_repaired = False
    for ix in range(len(events_log)):

        # Add `nan` in case trials are missing at the end of the EEG...
        if len(events_epochs) <= ix:
            print(f'Log file (row index {ix}): Found missing EEG epoch')
            events_epochs.insert(ix, np.nan)

        # ... or if the log and EEG trigers don't match up
        elif events_log[ix] != events_epochs[ix]:
            print(f'Log file (row index {ix}): Found missing EEG epoch')
            events_epochs.insert(ix, np.nan)
            previous_repaired = True

        # If they do match up, we check that the next trials do match as well
        elif previous_repaired: 
            if events_log[ix:ix + depth] != events_epochs[ix:ix + depth]:
                print(f'Log file (row index {ix}): Assuming missing EEG epoch')
                events_epochs.insert(ix, np.nan)
            else:
                previous_repaired = False

    # Remove trials with missing EEG epochs from the log file
    missing_ixs = np.where(np.isnan(events_epochs))[0].tolist()
    print(f'Dropping rows from the log file data: {missing_ixs}')
    log = log.reset_index(drop=True)
    log = log.drop(index=missing_ixs)

    return log


def get_bad_epochs(epochs, reject_peak_to_peak=None):
    """Detects bad epochs based on peak-to-peak amplitude."""

    # Convert thresholds to volts
    if reject_peak_to_peak is not None:
        reject_peak_to_peak = {'eeg': reject_peak_to_peak * 1e-6}

    # Reject on a copy of the data
    epochs_rej = epochs.copy().drop_bad(reject_peak_to_peak)

    # Get indices of bad epochs from the rejection log
    all_ixs = [elem for elem in epochs_rej.drop_log if elem != ('IGNORED',)]
    bad_ixs = [ix for ix, elem in enumerate(all_ixs) if elem != ()]

    return bad_ixs


def get_bad_channels(epochs, threshold=3., by_event_type=True):
    """Automatically detects bad channels using their average standard error"""

    # Compute standard error for each condition seperately, then average...
    if by_event_type:
        ses = epochs.standard_error(by_event_type=True)
        ses = combine_evoked(ses, weights='nave')
    
    # ... or directly compute standard error across all epochs
    else:
        ses = epochs.standard_error()

    # Average across time points for each channel
    ses = ses.data.mean(axis=1)

    # Convert to z scores
    zs = zscore(ses)

    # Look up bad channel labels
    ixs = np.where(zs > threshold)[0]
    bad_channels = [epochs.ch_names[ix] for ix in ixs]
    if bad_channels != []:
        print(f'Automatically detected bad channels {bad_channels} with '
              f'z_SE > {threshold}')
    else:
        print(f'Didn\'t detect any bad channels with z_SE > {threshold}')

    return bad_channels


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

    # Check that requested region of interest channels are present in the data
    for ch in roi:
        assert ch in epochs.ch_names, f'ROI channel \'{ch}\' not in the data'

    # Create virtual channel for the average in the region of interest
    print(f'Computing single trial ERP amplitudes for \'{name}\'')
    set_log_level('ERROR')
    roi_dict = {name: pick_channels(epochs.ch_names, roi)}
    epochs_roi = combine_channels(epochs, roi_dict)
    epochs.add_channels([epochs_roi], force_update_info=True)
    epochs.set_channel_types({name: 'misc'})

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
    set_log_level('INFO')
