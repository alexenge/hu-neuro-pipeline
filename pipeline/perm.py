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
        t_obs, clusters, cluster_p_vals, H0 = permutation_cluster_1samp_test(
            X, n_permutations=n_permutations, adjacency=channel_adjacency,
            n_jobs=n_jobs, seed=seed)

        # Create cluster images with cluster indices and p values
        ixs = np.zeros_like(t_obs)
        p_vals = np.ones_like(t_obs)
        pos_ix = 0
        neg_ix = 0
        for ix, cluster in enumerate(clusters):

            # Check if the cluster is positive or negative
            if t_obs[cluster][0] > 0:
                pos_ix += 1
                ixs[cluster] = pos_ix
            else:
                neg_ix -= 1
                ixs[cluster] = neg_ix

            # Extract cluster level p value
            p_val = cluster_p_vals[ix]
            p_vals[cluster] = p_val

        # Convert to DataFrames, adding info about contrast, stat, time
        dfs = []
        arrs = [t_obs, ixs, p_vals]
        stats = ['t_obs', 'cluster_index', 'p_val']
        for arr, stat in zip(arrs, stats):
            df = pd.DataFrame(arr, columns=channels)
            df.insert(0, 'contrast', ' - '.join(contrast))
            df.insert(1, 'stat', stat)
            df.insert(2, 'time', times)
            dfs.append(df)

        # Combine DataFrames
        cluster_df = pd.concat(dfs)

        # Append to the list of all contrasts
        cluster_dfs.append(cluster_df)

    # Combine DataFrames of all contrasts
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
        t_obs, clusters, cluster_p_vals, H0 = permutation_cluster_1samp_test(
            X, n_permutations=n_permutations, adjacency=adjacency,
            n_jobs=n_jobs, seed=seed)

        # Create cluster images with cluster indices and p values
        ixs = np.zeros_like(t_obs)
        p_vals = np.ones_like(t_obs)
        pos_ix = 0
        neg_ix = 0
        for ix, cluster in enumerate(clusters):

            # Check if the cluster is positive or negative
            if t_obs[cluster][0] > 0:
                pos_ix += 1
                ixs[cluster] = pos_ix
            else:
                neg_ix -= 1
                ixs[cluster] = neg_ix

            # Extract cluster level p value
            p_val = cluster_p_vals[ix]
            p_vals[cluster] = p_val

        # Convert to DataFrames, adding info about contrast, stat, time, freq
        dfs = []
        arrs = [t_obs, ixs, p_vals]
        stats = ['t_obs', 'cluster_index', 'p_val']
        for arr, stat in zip(arrs, stats):
            arr = arr.reshape(n_times * n_freqs, n_channels)
            df = pd.DataFrame(arr, columns=channels)
            df.insert(0, 'contrast', ' - '.join(contrast))
            df.insert(1, 'stat', stat)
            df.insert(2, 'time', np.repeat(times, n_freqs))
            df.insert(3, 'freq', np.tile(freqs, n_times))
            dfs.append(df)

        # Combine DataFrames
        cluster_df = pd.concat(dfs)

        # Append to the list of all contrasts
        cluster_dfs.append(cluster_df)

    # Combine DataFrames of all contrasts
    cluster_df = pd.concat(cluster_dfs, ignore_index=True)

    return cluster_df
