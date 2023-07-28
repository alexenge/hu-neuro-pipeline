import json
import urllib.request
from pathlib import Path
from warnings import warn

import pooch

osf_ids = {'ERN': 'q6gwp',
           'LRP': '28e6c',
           'MMN': '5q4xs',
           'N170': 'pfde9',
           'N2pc': 'yefrq',
           'N400': '29xpq',
           'P3': 'etdkz'}

LOCAL_CACHE = 'hu-neuro-pipeline'


def get_erpcore(component, n_participants=40):
    """Get sample data from the ERP CORE dataset.

    The data are either downloaded from the OSF or found in the local cache.
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

    n_participants : int, optional
        How many participants to download. By default, downloads all 40
        participants available in the dataset.

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

    n_participants = int(n_participants)
    max_participants = 40
    assert n_participants in range(1, max_participants + 1), \
        f'`n_participants` must be an integer between 1 and {max_participants}'
    if n_participants < max_participants:
        warn(f'Only fetching data for the first {n_participants} ' +
             'participant(s). This will not be reflected in the ' +
             '`participants.tsv` file of the BIDS structure, which will ' +
             f'contain all {max_participants} participants.')

    exclude_range = range(n_participants + 1, max_participants + 1)
    exclude_dirs = [f'sub-{id:03d}' for id in exclude_range]
    exclude_dirs += ['stimuli']

    osf_id = osf_ids[component]
    base_url = f'https://files.de-1.osf.io/v1/resources/{osf_id}/providers/osfstorage/'
    bids_dir = find_bids_dir(base_url)
    fetcher = construct_fetcher(base_url=base_url,
                                remote_dir=bids_dir,
                                local_dir='erpcore/',
                                exclude_dirs=exclude_dirs)

    paths = {'raw_files': [], 'log_files': []}
    for file in sorted(fetcher.registry_files):
        file = fetcher.fetch(file)
        if file.endswith('_eeg.set'):
            paths['raw_files'].append(file)
        elif file.endswith('_events.tsv'):
            paths['log_files'].append(file)

    return paths


def find_bids_dir(base_url):
    """Finds the BIDS directory for a given ERP CORE component."""

    with urllib.request.urlopen(base_url) as url:
        files = json.loads(url.read().decode())['data']
        bids_dir = [f for f in files
                    if 'Raw Data BIDS-Compatible'
                    in f['attributes']['name']][0]

    return bids_dir['attributes']['path']


def construct_fetcher(base_url, remote_dir, local_dir, exclude_dirs=None):
    """Constructs a pooch fetcher for getting ERP CORE remote files locally."""

    files = list_files(base_url, remote_dir, recursive=True,
                       exclude_dirs=exclude_dirs)

    urls = {}
    hashes = {}
    for file in files:
        relative_path = file['attributes']['materialized']
        relative_path = relative_path.replace(' Raw Data BIDS-Compatible', '')
        local_path = str(Path(f'{local_dir}/{relative_path}'))
        urls[local_path] = base_url + file['attributes']['path']
        hashes[local_path] = 'md5:' + file['attributes']['extra']['hashes']['md5']

    fetcher = pooch.create(
        path=pooch.os_cache(LOCAL_CACHE),
        base_url=base_url,
        env='PIPELINE_DATA_DIR',
        registry=hashes,
        urls=urls,
    )

    return fetcher


def list_files(base_url, remote_dir, recursive=False, exclude_dirs=None):
    """Lists files in a remote directory on OSF."""

    with urllib.request.urlopen(f'{base_url}/{remote_dir}') as url:
        files = json.loads(url.read().decode())['data']

        if recursive:
            for file in files:
                if file['attributes']['kind'] == 'folder':

                    if exclude_dirs is not None:
                        if file['attributes']['name'] in exclude_dirs:
                            continue

                    remote_dir_dir = file['attributes']['path']
                    files += list_files(base_url, remote_dir_dir,
                                        recursive, exclude_dirs)

            files = [file for file in files
                     if file['attributes']['kind'] == 'file']

    return files
