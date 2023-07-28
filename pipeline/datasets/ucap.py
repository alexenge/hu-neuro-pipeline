import json
import re
import urllib.request

import pooch

# URL of the UCAP repo files on OSF
BASE_URL = 'https://files.de-1.osf.io/v1/resources/hdxvb/providers/osfstorage'

# Local cache to download the files to
LOCAL_CACHE = 'hu-neuro-pipeline'


def get_ucap(n_participants=40):
    """Get sample data from the UCAP dataset.

    The data are either downloaded from the OSF or found in the local cache.
    See :footcite:`fromer2018` for details on the UCAP dataset.

    Parameters
    ----------
    n_participants : int, optional
        How many participants to download. By default, downloads all 40
        participants available in the dataset.

    Returns
    -------
    dict
        A dictionary with the file paths of the downloaded data:

        - ``'raw_files'``: A list with the paths of the raw EEG files
          (``.vhdr``)
        - ``'log_files'`` A list with the paths of the log files (``.txt``)

    See Also
    --------
    pipeline.datasets.get_erpcore

    References
    ----------
    .. footbibliography::
    """

    max_participants = 40
    assert n_participants in range(1, max_participants + 1), \
        f'`n_participants` must be an integer between 1 and {max_participants}'

    paths = {}

    eeg_fetcher = construct_fetcher('59cf07fa6c613b02958f3364/', 'ucap/raw/')
    n_files = int(n_participants) * 3
    eeg_paths = list(eeg_fetcher.registry.keys())[:n_files]
    eeg_paths = [eeg_fetcher.fetch(path) for path in eeg_paths]
    vhdr_paths = [path for path in eeg_paths if path.endswith('.vhdr')]
    paths['raw_files'] = vhdr_paths

    participant_ids = [path.split('/')[-1].replace('.vhdr', '')
                       for path in vhdr_paths]

    log_fetcher = construct_fetcher('59cf12259ad5a102cc5c4b93/', 'ucap/log/')
    log_paths = [f'ucap/log/{int(p_id)}_test.txt' for p_id in participant_ids]
    log_paths = [log_fetcher.fetch(path) for path in log_paths]
    paths['log_files'] = log_paths

    cali_fetcher = construct_fetcher('59cf089e6c613b02968f5724/', 'ucap/cali/')
    cali_paths = [f'ucap/cali/{p_id}_cali.matrix' for p_id in participant_ids]
    cali_paths = [cali_fetcher.fetch(path) for path in cali_paths]
    paths['besa_files'] = cali_paths

    return paths


def construct_fetcher(remote_dir, local_dir):
    """Constructs a pooch fetcher for getting UCAP remote files locally."""

    with urllib.request.urlopen(f'{BASE_URL}/{remote_dir}') as url:
        files = json.loads(url.read().decode())['data']

    files = sorted(files, key=lambda d: natsort(d['attributes']['name']))

    urls = {}
    hashes = {}
    for file in files:
        local_path = local_dir + file['attributes']['name']
        urls[local_path] = BASE_URL + file['attributes']['path']
        hashes[local_path] = 'md5:' + file['attributes']['extra']['hashes']['md5']

    fetcher = pooch.create(path=pooch.os_cache(LOCAL_CACHE),
                           base_url=BASE_URL,
                           env='PIPELINE_DATA_DIR',
                           registry=hashes,
                           urls=urls)

    return fetcher


def natsort(s):
    """Natural sort key for sorting strings with numbers in them."""

    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
