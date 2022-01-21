import numpy as np
import pandas as pd
from mne.channels import find_ch_adjacency
from mne.stats import combine_adjacency, permutation_cluster_1samp_test


def compute_perm(evokeds_per_participant, contrasts, tmin=0., tmax=1.,
                 channels=None, n_jobs=1, n_permutations=5001, seed=1234):
    """Performs a cluster based permutation test for a given contrast"""

    # Extract one example evoked for reading data dimensions
    example_evoked = evokeds_per_participant[0][0].copy()

    # Get relevant time samples
    times = example_evoked.times
    if tmin is not None:
        times = [t for t in times if t >= tmin]
    if tmax is not None:
        times = [t for t in times if t < tmax]

    # Get relevant channels
    if channels is None:
        channels = example_evoked.pick_types(eeg=True).ch_names
    else:
        assert all([ch in example_evoked.ch_names for ch in channels]), \
            'All channels in `perm_channels` must be present in the data!'

    # Get dimensions of data for the permutation test
    n_participants = len(evokeds_per_participant)
    n_times = len(times)
    n_channels = len(channels)

    # Prepare emtpy list for results
    cluster_dfs = []

    # Sequentially handle each contrast
    for contrast in contrasts:

        # Prepare empty array
        X = np.zeros((n_participants, n_times, n_channels))

        # Compute a difference wave for each participant
        for ix, evokeds in enumerate(evokeds_per_participant):

            # Extract evoked data for the two conditions of interest
            data_conditions = []
            for condition in contrast:
                evoked = [ev for ev in evokeds if ev.comment == condition][0]
                evoked = evoked.copy().crop(
                    tmin, tmax, include_tmax=False).pick_channels(channels)
                data_conditions.append(evoked.data)

            # Compute difference between conditions
            data_diff = data_conditions[0] - data_conditions[1]
            data_diff = data_diff.swapaxes(1, 0)  # Time points, channels
            X[ix] = data_diff

        # Compute channel adjacency matrix
        channel_adjacency, _ = find_ch_adjacency(evoked.info, 'eeg')

        # Run permutation test
        t_obs, clusters, cluster_pv, H0 = permutation_cluster_1samp_test(
            X, n_permutations=n_permutations, adjacency=channel_adjacency,
            n_jobs=n_jobs, seed=seed)

        # Create cluster image
        cluster_arr = np.ones_like(t_obs)
        for ix, cluster in enumerate(clusters):
            pv = cluster_pv[ix]
            cluster_arr[cluster] = pv

        # Convert to DataFrame
        cluster_df = pd.DataFrame(cluster_arr, index=times, columns=channels)
        cluster_df = cluster_df.reset_index().rename(columns={'index': 'time'})

        # Add info about the current contrast
        contrast_str = ' - '.join(contrast)
        cluster_df.insert(0, 'contrast', contrast_str)

        # Append to the list of all contrasts
        cluster_dfs.append(cluster_df)

    # Combine DataFrames of all contrasts
    # TODO: Maybe we should convert this to long format for easier plotting
    cluster_df = pd.concat(cluster_dfs, ignore_index=True)

    return cluster_df


def compute_perm_tfr(
        evokeds_per_participant, contrasts, tmin=0., tmax=1., channels=None,
        fmin=None, fmax=None, n_jobs=1, n_permutations=5001, seed=1234):
    """Performs a cluster based permutation test on time-frequency data"""

    # Extract one example evoked for reading data dimensions
    example_evoked = evokeds_per_participant[0][0].copy()

    # Get relevant time samples
    times = example_evoked.times
    if tmin is not None:
        times = [t for t in times if t >= tmin]
    if tmax is not None:
        times = [t for t in times if t < tmax]

    # Get relevant frequencies
    freqs = example_evoked.freqs
    if fmin is not None:
        freqs = [f for f in freqs if f >= fmin]
    if fmax is not None:
        freqs = [f for f in freqs if f < fmax]

    # Get relevant channels
    if channels is None:
        channels = example_evoked.pick_types(eeg=True).ch_names
    else:
        assert all([ch in example_evoked.ch_names for ch in channels]), \
            'All channels in `perm_channels` must be present in the data!'

    # Get dimensions of data for the permutation test
    n_participants = len(evokeds_per_participant)
    n_times = len(times)
    n_freqs = len(freqs)
    n_channels = len(channels)

    # Prepare emtpy list for results
    cluster_dfs = []

    # Sequentially handle each contrast
    for contrast in contrasts:

        # Prepare empty array
        X = np.zeros((n_participants, n_times, n_freqs, n_channels))

        # Compute a difference wave for each participant
        for ix, evokeds in enumerate(evokeds_per_participant):

            # Extract evoked data for the two conditions of interest
            data_conditions = []
            for condition in contrast:
                evoked = [ev for ev in evokeds if ev.comment == condition][0]
                evoked = evoked.copy().crop(
                    tmin, tmax, fmin, fmax, include_tmax=False).pick_channels(
                        channels)
                data_conditions.append(evoked.data)

            # Compute difference between conditions
            data_diff = data_conditions[0] - data_conditions[1]
            data_diff = data_diff.swapaxes(0, 2)  # Times, freqs, channels
            X[ix] = data_diff

        # Compute frequency and channel adjacency matrix
        # Based on channel locations and a lattice matrix for frequencies
        channel_adjacency, _ = find_ch_adjacency(evoked.info, 'eeg')
        adjacency = combine_adjacency(n_freqs, channel_adjacency)

        # Run permutation test
        t_obs, clusters, cluster_pv, H0 = permutation_cluster_1samp_test(
            X, n_permutations=n_permutations, adjacency=adjacency,
            n_jobs=n_jobs, seed=seed)

        # Create cluster image
        cluster_arr = np.ones_like(t_obs)
        for ix, cluster in enumerate(clusters):
            pv = cluster_pv[ix]
            cluster_arr[cluster] = pv

        # Stack array so we can convert it to a DataFrame
        cluster_arr = cluster_arr.reshape(n_times * n_freqs, n_channels)

        # Convert to DataFrame
        cluster_df = pd.DataFrame(cluster_arr, columns=channels)

        # Add information about the current contrast, times, and frequencies
        info_df = pd.DataFrame({'contrast': ' - '.join(contrast),
                                'time': np.repeat(times, n_freqs),
                                'freq': np.tile(freqs, n_times)})
        cluster_df = pd.concat([info_df, cluster_df], axis=1)

        # Append to the list of all contrasts
        cluster_dfs.append(cluster_df)

    # Combine DataFrames of all contrasts
    # TODO: Maybe we should convert this to long format for easier plotting
    cluster_df = pd.concat(cluster_dfs, ignore_index=True)

    return cluster_df
