import numpy as np
import pandas as pd
from mne.channels import find_ch_adjacency
from mne.stats import combine_adjacency, permutation_cluster_1samp_test


def compute_perm(evokeds_per_participant, contrasts, tmin=0.0, tmax=1.0,
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
        ch_adjacency, _ = find_ch_adjacency(evoked.info, 'eeg')

        # Run permutation test
        t_obs, clusters, cluster_p_vals, H0 = permutation_cluster_1samp_test(
            X, n_permutations=n_permutations, adjacency=ch_adjacency,
            n_jobs=n_jobs, seed=seed)

        # Sort clusters by p values
        cluster_ranks = cluster_p_vals.argsort()
        cluster_p_vals = cluster_p_vals[cluster_ranks]
        clusters = [clusters[rank] for rank in cluster_ranks]

        # Create cluster images with cluster labels and p values
        labels = np.full_like(t_obs, 'NA', dtype=object)
        p_vals = np.ones_like(t_obs)
        pos_ix = 0
        neg_ix = 0
        for ix, cluster in enumerate(clusters):

            # Check if the cluster is positive or negative
            if t_obs[cluster][0] > 0:
                pos_ix += 1
                labels[cluster] = f'pos_{pos_ix}'
            else:
                neg_ix += 1
                labels[cluster] = f'neg_{neg_ix}'

            # Extract cluster level p value
            p_val = cluster_p_vals[ix]
            p_vals[cluster] = p_val

        # Prepare DataFrame for storing t values, cluster labels, and p values
        cluster_df = pd.DataFrame({
            'contrast': ' - '.join(contrast),
            'time': np.repeat(times, repeats=n_channels),
            'channel': np.tile(channels, reps=n_times)})

        # Add t values, cluster labels, and p values
        arrs = [t_obs, labels, p_vals]
        stats = ['t_obs', 'cluster', 'p_val']
        for arr, stat in zip(arrs, stats):

            # Convert array to long format
            # Initial array is has shape (times, channels)
            # New array is has shape (times * channels,)
            arr_long = arr.flatten()

            # Add to DataFrame
            cluster_df[stat] = arr_long

        # Append to the list of all contrasts
        cluster_dfs.append(cluster_df)

    # Combine DataFrames of all contrasts
    cluster_df = pd.concat(cluster_dfs, ignore_index=True)

    return cluster_df


def compute_perm_tfr(
        evokeds_per_participant, contrasts, tmin=0.0, tmax=1.0, channels=None,
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
        ch_adjacency, _ = find_ch_adjacency(evoked.info, 'eeg')
        adjacency = combine_adjacency(n_freqs, ch_adjacency)

        # Run permutation test
        t_obs, clusters, cluster_p_vals, H0 = permutation_cluster_1samp_test(
            X, n_permutations=n_permutations, adjacency=adjacency,
            n_jobs=n_jobs, seed=seed)

        # Sort clusters by p values
        cluster_ranks = cluster_p_vals.argsort()
        cluster_p_vals = cluster_p_vals[cluster_ranks]
        clusters = [clusters[rank] for rank in cluster_ranks]

        # Create cluster images with cluster labels and p values
        labels = np.full_like(t_obs, 'NA', dtype=object)
        p_vals = np.ones_like(t_obs)
        pos_ix = 0
        neg_ix = 0
        for ix, cluster in enumerate(clusters):

            # Check if the cluster is positive or negative
            if t_obs[cluster][0] > 0:
                pos_ix += 1
                labels[cluster] = f'pos_{pos_ix}'
            else:
                neg_ix += 1
                labels[cluster] = f'neg_{neg_ix}'

            # Extract cluster level p value
            p_val = cluster_p_vals[ix]
            p_vals[cluster] = p_val

        # Prepare DataFrame for storing t values, cluster labels, and p values
        cluster_df = pd.DataFrame({
            'contrast': ' - '.join(contrast),
            'time': np.repeat(times, n_channels * n_freqs),
            'freq': np.repeat(np.tile(freqs, n_times), n_channels),
            'channel': np.tile(channels, n_times * n_freqs)})

        # Add t values, cluster labels, and p values
        arrs = [t_obs, labels, p_vals]
        stats = ['t_obs', 'cluster', 'p_val']
        for arr, stat in zip(arrs, stats):

            # Convert array to long format
            # Initial array is has shape (times, channels)
            # New array is has shape (times * channels,)
            arr_long = arr.flatten()

            # Add to DataFrame
            cluster_df[stat] = arr_long

        # Append to the list of all contrasts
        cluster_dfs.append(cluster_df)

    # Combine DataFrames of all contrasts
    cluster_df = pd.concat(cluster_dfs, ignore_index=True)

    return cluster_df
