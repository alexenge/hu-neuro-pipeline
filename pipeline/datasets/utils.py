from warnings import warn

import pandas as pd
import pooch
from numpy import nan
from pandas.api.types import is_list_like

LOCAL_CACHE = 'hu-neuro-pipeline'


def get_dataset(manifest_df, base_url, participants, path):

    if path is None:
        path = pooch.os_cache(LOCAL_CACHE)
        env = 'PIPELINE_DATA_DIR'
    else:
        env = None

    fetcher = pooch.create(path=path, base_url=base_url, env=env)
    local_dir = fetcher.abspath

    manifest_df = _select_participants(manifest_df, participants)

    file_types = manifest_df['file_type'].unique()
    file_types = file_types[~pd.isnull(file_types)]
    paths = {file_type: [] for file_type in file_types}

    for ix, row in manifest_df.iterrows():

        local_file = local_dir.joinpath(row['local_path'])

        if not local_file.exists():
            fetcher.registry[row['local_path']] = row['hash']
            fetcher.urls[row['local_path']] = row['url']
            _ = fetcher.fetch(row['local_path'])

        if row['file_type'] in paths:
            paths[row['file_type']].append(str(local_file))

    return paths


def _select_participants(df, participants):
    """Selects a subset of participants by their IDs or total number."""

    all_participants = df['participant_id'].str.zfill(2).unique().tolist()
    if nan in all_participants:  # Ignore general (e.g., BIDS) files for now
        all_participants.remove(nan)

    if isinstance(participants, float):
        warn(f'Converting `participants` from float ({participants}) to ' +
             f'int ({int(participants)})')
        selected_participants = all_participants[:int(participants)]

    if isinstance(participants, int):
        assert participants in range(1, len(all_participants) + 1), \
            '`participants` must be an integer between 1 and ' + \
            f'{len(all_participants)}'
        selected_participants = all_participants[:participants]

    if isinstance(participants, str):
        assert participants in all_participants, \
            f'Participant \'{participants}\' not found in the dataset. ' + \
            f'Valid participants are {all_participants}'
        selected_participants = [participants]

    if is_list_like(participants):
        missing_participants = list(set(participants) - set(all_participants))
        assert not missing_participants, \
            f'Participants {missing_participants} not found in the ' + \
            f'dataset. Valid participants are {all_participants}'
        selected_participants = participants

    selected_participants += [nan]  # Re-include general (e.g., BIDS) files

    return df[df['participant_id'].isin(selected_participants)]
