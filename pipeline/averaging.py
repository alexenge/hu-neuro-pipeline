import numpy as np
import pandas as pd
from mne import Epochs, Evoked, grand_average


def compute_evokeds(epochs, average_by=None, bad_ixs=[], participant_id=None):
    """Computes condition averages (evokeds) based on triggers or columns."""

    # Average by triggers in case no log file columns were provided
    if average_by is None:
        all_evokeds, all_evokeds_df = compute_evokeds_triggers(
            epochs, bad_ixs, participant_id)
    else:
        all_evokeds, all_evokeds_df = compute_evokeds_cols(
            epochs, average_by, bad_ixs, participant_id)

    return all_evokeds, all_evokeds_df


def compute_evokeds_triggers(epochs, bad_ixs=[], participant_id=None):
    """Computes condition averages (evokeds) based on triggers."""

    # Get indices of good epochs
    good_ixs = [ix for ix in range(len(epochs)) if ix not in bad_ixs]

    # Prepare emtpy lists
    all_evokeds = []
    all_evokeds_dfs = []

    # Compute evokeds
    epochs_good = epochs.copy()[good_ixs]
    evokeds = average_by_events(epochs_good)
    all_evokeds = all_evokeds + evokeds

    # Convert to DataFrame
    evokeds_df = create_evokeds_df(evokeds, participant_id=participant_id)
    all_evokeds_dfs.append(evokeds_df)

    # Combine DataFrames
    all_evokeds_df = pd.concat(all_evokeds_dfs, ignore_index=True)

    return all_evokeds, all_evokeds_df


def compute_evokeds_cols(
        epochs, average_by=None, bad_ixs=[], participant_id=None):
    """Computes condition averages (evokeds) based on log file columns."""

    # Make sure that provided values are stored in a list
    if isinstance(average_by, str):
        average_by = [average_by]

    # Get indices of good epochs
    good_ixs = [ix for ix in range(len(epochs)) if ix not in bad_ixs]

    # Prepare emtpy lists
    all_evokeds = []
    all_evokeds_dfs = []

    # Iterate over the provided main effects and interactions
    for cols in average_by:

        # Parse interaction effects into a list
        cols = cols.split('/')

        # Compute evokeds
        epochs_update = update_events(epochs, cols)[good_ixs]
        evokeds = average_by_events(epochs_update)
        all_evokeds = all_evokeds + evokeds

        # Convert to DataFrame
        trials = epochs_update.metadata
        evokeds_df = create_evokeds_df(
            evokeds, cols, trials, participant_id)

        # Append info about averaging
        value = '/'.join(cols)
        evokeds_df.insert(loc=1, column='average_by', value=value)
        all_evokeds_dfs.append(evokeds_df)

    # Combine DataFrames
    all_evokeds_df = pd.concat(all_evokeds_dfs, ignore_index=True)

    # Move condition columns back to the front
    # They might have been moved to the end while concatenating
    if average_by is not None:
        time_ix = all_evokeds_df.columns.get_loc('time')
        for cols in reversed(average_by):
            if not '/' in cols:
                all_evokeds_df.insert(
                    time_ix - 1, column=cols, value=all_evokeds_df.pop(cols))

                # Convert NaNs to empty strings so that R can represent them
                all_evokeds_df[cols] = all_evokeds_df[cols].fillna('')

    return all_evokeds, all_evokeds_df


def average_by_events(epochs, method='mean'):
    """Create a list of evokeds from epochs, one per event type."""

    # Pick channel types for ERPs
    # The `average` method for `EpochsTFR` doesn't support `picks`
    picks_dict = {'picks': ['eeg', 'misc']} \
        if isinstance(epochs, Epochs) else {}

    # Loop over event types and average
    # TODO: Use MNE built-in argument `by_event_type` once it's in `EpochsTFR`
    evokeds = []
    for event_type in epochs.event_id.keys():
        evoked = epochs[event_type].average(**picks_dict, method=method)
        evoked.comment = event_type
        evokeds.append(evoked)

    return evokeds


def update_events(epochs, cols):
    """Updates the events/event_id structures using cols from the metadata."""

    # Generate event codes for the relevant columns
    cols_df = pd.DataFrame(epochs.metadata[cols])
    cols_df = cols_df.astype('str')
    ids = cols_df.agg('/'.join, axis=1)
    codes = ids.astype('category').cat.codes

    # Create copy of the data with the new event codes
    epochs_update = epochs.copy()
    epochs_update.events[:, 2] = codes
    epochs_update.event_id = dict(zip(ids, codes))

    return epochs_update


def create_evokeds_df(evokeds, cols=None, trials=None, participant_id=None):
    """Converts mne.Evoked into a pd.DataFrame with metadata."""

    # Convert ERP amplitudes from volts to microvolts
    # The `to_data_frame` method for `AverageTFR` doesn't support `scalings`
    scalings_dict = {'scalings': {'eeg': 1e6, 'misc': 1e6}} \
        if isinstance(evokeds[0], Evoked) else {}

    # Convert all evokeds to a single DataFrame
    evokeds_dfs = [evoked.to_data_frame(**scalings_dict, time_format=None)
                   for evoked in evokeds]
    evokeds_df = pd.concat(evokeds_dfs, ignore_index=True)

    # Optionally add columns from the metadata
    repeats = len(evokeds_df)
    if cols is not None:
        assert trials is not None, 'Must provide trials (metadata) with cols'
        cols_df = pd.DataFrame(trials[cols])
        cols_df = cols_df.astype('str')
        cols_df = cols_df.drop_duplicates()
        repeats = len(evokeds_df) / len(cols_df)
        cols_df = cols_df.loc[cols_df.index.repeat(repeats)]
        cols_df = cols_df.reset_index(drop=True)
        evokeds_df = pd.concat([cols_df, evokeds_df], axis=1)

    # Otherwise add comments from evokeds (assumed to contain event IDs)
    else:
        comments = [evoked.comment for evoked in evokeds]
        repeats = len(evokeds_df) / len(comments)
        comments = np.repeat(comments, repeats)
        evokeds_df.insert(loc=0, column='event_id', value=comments)

    # Optionally add participant_id
    if participant_id is not None:
        evokeds_df.insert(loc=0, column='participant_id', value=participant_id)

    return evokeds_df


def compute_grands(evokeds_per_participant):
    """Averages evokeds of all participants into grand averages."""

    # Average across participants for each condition
    evokeds_per_condition = list(map(list, zip(*evokeds_per_participant)))
    grands = [grand_average(x) for x in evokeds_per_condition]

    # Add meaningful comments
    comments = [x[0].comment for x in evokeds_per_condition]
    for grand, comment in zip(grands, comments):
        grand.comment = comment

    return grands


def compute_grands_df(evokeds_df):
    """Averages evoked DataFrames of all participants into grand averages."""

    # Get indices of columns to group by (conditions, times, frequencies)
    first_grouping_ix = 1  # Column 0 is participant_id (to average over)
    last_grouping_col = 'freq' if 'freq' in evokeds_df.columns else 'time'
    last_grouping_ix = evokeds_df.columns.get_loc(last_grouping_col)
    grouping_ixs = range(first_grouping_ix, last_grouping_ix + 1)

    # Average by grouping columns
    group_cols = list(evokeds_df.columns[grouping_ixs])
    grands_df = evokeds_df.groupby(group_cols, dropna=False).mean()

    # Convert conditions from index back to columns
    grands_df = grands_df.reset_index()

    return grands_df
