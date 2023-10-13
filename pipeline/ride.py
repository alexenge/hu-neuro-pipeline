import numpy as np
from ride import RideCfg, ride_call


def correct_ride(epochs, bad_ixs, ride_condition_column, ride_rt_column,
                 ride_s_twd, ride_r_twd):

    assert ride_condition_column in epochs.metadata.columns, \
        f'Column "{ride_condition_column}" not found in the log file'
    assert ride_rt_column in epochs.metadata.columns, \
        f'Column "{ride_rt_column}" not found in the log file'

    good_ixs = [ix for ix in range(len(epochs)) if ix not in bad_ixs]
    epochs_good = epochs[good_ixs].copy()
    metadata = epochs_good.metadata

    # TODO: Move all of this INSIDE the loop because the `r_latency` vector
    # is different for each condition

    comp_name = ('s', 'r')
    comp_twd = (ride_s_twd * 1000, ride_r_twd * 1000)  # Convert s to ms
    comp_latency = (0.0, metadata[ride_rt_column].values)
    sfreq = epochs_good.info['sfreq']
    epoch_twd = (epochs_good.tmin * 1000, epochs_good.tmax * 1000)
    re_samp = 1000 / sfreq
    bl = np.abs(epochs_good.baseline[0]) * 1000

    cfg = RideCfg(comp_name, comp_twd, comp_latency, sfreq, epoch_twd,
                  re_samp=re_samp, bl=bl)

    conditions = metadata[ride_condition_column].unique()
    for condition in conditions:

        condition_ixs = metadata[ride_condition_column] == condition
        epochs_condition = epochs_good[condition_ixs].copy()

        ride_results = ride_call(epochs_condition, cfg)
