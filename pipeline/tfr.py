import numpy as np
import pandas as pd


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
