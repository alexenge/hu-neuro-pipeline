import json
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from .utils import get_dataset

LOCAL_CACHE = 'hu-neuro-pipeline/erpcore'
MANIFEST_FILE = Path(__file__).parent.joinpath('erpcore_manifest.csv')

OSF_IDS = {'ERN': 'q6gwp',
           'LRP': '28e6c',
           'MMN': '5q4xs',
           'N170': 'pfde9',
           'N2pc': 'yefrq',
           'N400': '29xpq',
           'P3': 'etdkz'}

FILE_TYPE_DICT = {'eeg.set': 'raw_files',
                  'events.tsv': 'log_files'}


def get_erpcore(component, participants=40, path=None):
    """Get sample data from the ERP CORE dataset.

    Data that are not yet available locally will be downloaded from the OSF.
    See :footcite:`kappenman2021` for details on the ERP CORE dataset.

    Parameters
    ----------
    component : str
        Which ERP CORE experiment to download. Each experiment was designed to
        elicit one of seven common ERP components:

        - ``'ERN'`` (flanker task)
        - ``'LRP'`` (flanker task)
        - ``'MMN'`` (passive auditory oddball task)
        - ``'N170'`` (face perception task)
        - ``'N2pc'`` (simple visual search task)
        - ``'N400'`` (word pair judgment task)
        - ``'P3'`` (active visual oddball task)

    participants : int or list of str, optional
        Which participants to download. By default, downloads all 40
        participants available in the dataset. If an integer, downloads that
        many participants starting from the first participant. If a list of
        strings, downloads the participants with the given IDs (e.g.,
        ``['sub-001', 'sub-002']``).
    path : str or Path, optional
        Local directory path to download the data to. By default, uses the
        user's local cache directory. An alternative way to specify the
        download path is to set the environment variable ``PIPELINE_DATA_DIR``.

    Returns
    -------
    dict
        A dictionary with the file paths of the downloaded data:

        - ``'raw_files'``: A list with the paths of the raw EEG files
          (``eeg.set``)
        - ``'log_files'`` A list with the paths of the log files
          (``events.tsv``)

    See Also
    --------
    pipeline.datasets.get_ucap

    References
    ----------
    .. footbibliography::
    """

    manifest_df = pd.read_csv(MANIFEST_FILE, dtype={'participant_id': str})
    manifest_df = manifest_df[manifest_df['component'] == component]

    osf_id = OSF_IDS[component]
    base_url = f'https://files.de-1.osf.io/v1/resources/{osf_id}/providers/osfstorage'

    return get_dataset(manifest_df, base_url, participants, path)


def _write_erpcore_manifest():
    """Writes a CSV table containing the file paths of the ERP CORE datasets."""

    dfs = []
    for component, osf_id in OSF_IDS.items():

        base_url = f'https://files.de-1.osf.io/v1/resources/{osf_id}/providers/osfstorage/'

        bids_suffix = _find_bids_remote_path(base_url)

        files = _list_files(base_url, bids_suffix, exclude_dirs=['stimuli'])

        attributes = [file['attributes'] for file in files]
        df = pd.DataFrame.from_dict(attributes)

        df.insert(0, 'component', component)

        participants = df['name'].str.split('_|\.').str[0]
        participants = [p if p.startswith('sub') else '' for p in participants]
        df.insert(1, 'participant_id', participants)
        df = df.sort_values('participant_id')

        local_paths = df['materialized'].str.\
            replace(f'/{component} Raw Data BIDS-Compatible/',
                    f'erpcore/{component}/')
        df.insert(2, 'local_path', local_paths)

        hashes = df['extra'].apply(lambda x: f'md5:{x["hashes"]["md5"]}')
        df.insert(3, 'hash', hashes)

        urls = df['path'].apply(lambda x: f'{base_url}{x}')
        df.insert(4, 'url', urls)

        file_exts = df['name'].str.split('_').str[-1]
        file_types = file_exts.map(FILE_TYPE_DICT)
        df.insert(5, 'file_type', file_types)

        df = df[['component', 'local_path', 'url', 'hash', 'participant_id',
                 'file_type', 'size']]

        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    df.to_csv(MANIFEST_FILE, index=False)


def _find_bids_remote_path(base_url):
    """Finds the BIDS directory for a given ERP CORE component dataaset."""

    with urlopen(base_url) as url:
        files = json.loads(url.read().decode())['data']
        bids_dir = [f for f in files
                    if 'Raw Data BIDS-Compatible'
                    in f['attributes']['name']][0]

    return bids_dir['attributes']['path']


def _list_files(base_url, suffix, exclude_dirs=None):
    """Lists files recursively in a remote directory on OSF."""

    with urlopen(f'{base_url}/{suffix}') as url:
        files = json.loads(url.read().decode())['data']

        for file in files:
            if file['attributes']['kind'] == 'folder':

                if exclude_dirs is not None \
                        and file['attributes']['name'] in exclude_dirs:
                    continue

                new_suffix = file['attributes']['path']
                files += _list_files(base_url, new_suffix, exclude_dirs)

        files = [file for file in files
                 if file['attributes']['kind'] == 'file']

    return files
