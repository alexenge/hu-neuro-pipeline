import numpy as np
import pandas as pd
from mne import concatenate_epochs, set_log_level


def subtract_evoked(epochs, evokeds=None, cols=None):
    """Subtracts evoked activity (across or by conditions) from epochs."""

    # If no columns were requested, subtract evoked activity across conditions
    set_log_level('ERROR')
    if cols is None:
        print('Subtracting evoked activity')
        epochs = epochs.subtract_evoked()
    
    # Otherwise subtract seperately for all (combinations of) conditions
    else:
        print(f'Subtracting evoked activity per condition in \'{cols}\'')
        epochs = subtract_evoked_cols(epochs, evokeds, cols)
    set_log_level('INFO')
    
    return epochs


def subtract_evoked_cols(epochs, evokeds, cols):
    """Subtracts evoked activity (separately by conditions) from epochs."""

    # Combine relevant columns
    cols = cols.split('/')
    cols_df = pd.DataFrame(epochs.metadata[cols])
    cols_df = cols_df.astype('str')
    ids = cols_df.agg('/'.join, axis=1).reset_index(drop=True)

    # Loop over epochs
    epochs_subtracted = []
    for ix, id in enumerate(ids):

        # Subtract the relevant evoked from each epoch
        evoked_id = [ev for ev in evokeds if ev.comment == id][0]
        epoch_subtracted = epochs[ix].subtract_evoked(evoked_id)
        epochs_subtracted.append(epoch_subtracted)
    
    # Combine list of subtracted epochs
    epochs_subtracted = concatenate_epochs(epochs_subtracted)
    
    return epochs_subtracted


def compute_single_trials_tfr(epochs, components, bad_ixs=None):
    """Computes single trial power for a dict of multiple components."""

    # Check that values in the dict are lists
    if not isinstance(components['name'], list):
        components = {key: [value] for key, value in components.items()}

    # Loop over components
    components_df = pd.DataFrame(components)
    for _, component in components_df.iterrows():

        # Comput single trial power
        compute_component_tfr(
            epochs, component['name'], component['tmin'],
            component['tmax'], component['fmin'], component['fmax'],
            component['roi'], bad_ixs)

    return epochs.metadata


def compute_component_tfr(
        epochs, name, tmin, tmax, fmin, fmax, roi, bad_ixs=None):
    """Computes single trial power for a single component."""

    # Check that requested region of interest channels are present in the data
    for ch in roi:
        assert ch in epochs.ch_names, f'ROI channel \'{ch}\' not in the data'

    # Select region, time window, and frequencies of interest
    print(f'Computing single trial power amplitudes for \'{name}\'')
    epochs_oi = epochs.copy().pick_channels(roi).crop(tmin, tmax, fmin, fmax)

    # Compute mean power per trial
    mean_power = epochs_oi.data.mean(axis=(1, 2, 3))

    # Set power for bad epochs to NaN
    if bad_ixs is not None:
        if isinstance(bad_ixs, int):
            bad_ixs = [bad_ixs]
        mean_power[bad_ixs] = np.nan

    # Add as a new column to the original metadata
    epochs.metadata[name] = mean_power
