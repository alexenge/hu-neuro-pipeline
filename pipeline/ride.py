import numpy as np
from ride import RideCfg, correct_trials, ride_call


def correct_ride(epochs, bad_ixs, ride_condition_column, ride_rt_column,
                 ride_s_twd, ride_r_twd):
    """Estimates speech artifacts using RIDE and subtracts them from epochs."""

    assert ride_condition_column in epochs.metadata.columns, \
        f'Column "{ride_condition_column}" not found in the log file'
    assert ride_rt_column in epochs.metadata.columns, \
        f'Column "{ride_rt_column}" not found in the log file'

    # Prepare RIDE configuration
    comp_name = ['s', 'r']
    comp_twd = [[x * 1000 for x in ride_s_twd],  # Ride expects ms, not s
                [x * 1000 for x in ride_r_twd]]
    sfreq = epochs.info['sfreq']
    epoch_twd = [epochs.tmin * 1000, epochs.tmax * 1000]
    re_samp = 1000 / sfreq
    bl = np.abs(epochs.baseline[0]) * 1000

    # Perform RIDE correction separately for each condition
    conditions = epochs.metadata[ride_condition_column].unique()
    ride_results_conditions = {}
    epochs_corr = epochs.copy()
    for condition in conditions:

        # Select epochs of the current condition
        is_condition = epochs.metadata[ride_condition_column] == condition
        condition_ixs = np.where(is_condition)[0]
        epochs_condition = epochs[condition_ixs].copy()

        # Exclude bad epochs
        condition_good_ixs = [ix for ix in condition_ixs if ix not in bad_ixs]
        epochs_condition_good = epochs[condition_good_ixs].copy()
        comp_latency = [0.0,
                        epochs_condition_good.metadata[ride_rt_column].values]

        # Perform RIDE correction
        cfg = RideCfg(comp_name, comp_twd, comp_latency, sfreq, epoch_twd,
                      re_samp=re_samp, bl=bl)
        ride_results = ride_call(epochs_condition_good, cfg)
        ride_results_conditions[condition] = ride_results

        # Subtract RIDE R component from all (good + bad) epochs
        rt = epochs_condition.metadata[ride_rt_column].values
        epochs_condition_corr = correct_trials(ride_results, epochs_condition,
                                               rt)
        epochs_corr._data[condition_ixs] = epochs_condition_corr._data

    return epochs_corr, ride_results_conditions
