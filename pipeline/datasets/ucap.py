import json
from pathlib import Path
from urllib.request import urlopen

import pandas as pd

from .utils import get_dataset

BASE_URL = 'https://files.de-1.osf.io/v1/resources/hdxvb/providers/osfstorage'
MANIFEST_FILE = Path(__file__).parent.joinpath('ucap_manifest.csv')

FILE_TYPE_DICT = {'vhdr': 'raw_files',
                  'txt': 'log_files',
                  'matrix': 'besa_files'}


def get_ucap(participants=40, path=None):
    """Get sample data from the UCAP dataset.

    Data that are not yet available locally will be downloaded from the OSF.
    See :footcite:`fromer2018` for details on the UCAP dataset.

    Parameters
    ----------
    participants : int or list of str, optional
        Which participants to download. By default, downloads all 40
        participants available in the dataset. If an integer, downloads that
        many participants starting from the first participant. If a list of
        strings, downloads the participants with the given IDs (e.g.,
        ``['05', '07']``).
    path : str or Path, optional
        Local directory path to download the data to. By default, uses the
        user's local cache directory. An alternative way to specify the
        download path is to set the environment variable ``PIPELINE_DATA_DIR``.

    Returns
    -------
    dict
        A dictionary with the file paths of the downloaded data:

        - ``'raw_files'``: A list with the paths of the raw EEG files
          (``.vhdr``)
        - ``'log_files'`` A list with the paths of the log files (``.txt``)
        - ``'besa_files'`` A list with the paths of the BESA calibration files
          (``.matrix``)

    See Also
    --------
    pipeline.datasets.get_erpcore

    References
    ----------
    .. footbibliography::
    """

    manifest_df = pd.read_csv(MANIFEST_FILE, dtype={'participant_id': str})

    return get_dataset(manifest_df, BASE_URL, participants, path)


def _write_ucap_manifest():
    """Writes a CSV table containing the file paths of the UCAP dataset."""

    eeg_url = '59cf07fa6c613b02958f3364/'
    log_url = '59cf12259ad5a102cc5c4b93/'
    cali_url = '59cf089e6c613b02968f5724/'

    files = []
    for url in [eeg_url, log_url, cali_url]:
        with urlopen(f'{BASE_URL}/{url}') as url:
            files += json.loads(url.read().decode())['data']

    attributes = [file['attributes'] for file in files]

    df = pd.DataFrame.from_dict(attributes)

    participants = df['name'].str.split('_|\.').str[0].str.zfill(2)

    n_expected_files = 5  # Complete participants have 3 x EEG, 1 x log, 1 x cali
    n_files = participants.value_counts()
    good_participant_ids = n_files[n_files == n_expected_files].index.to_list()

    df.insert(0, 'participant_id', participants)
    df = df.sort_values(by=['participant_id', 'name'])
    df = df[df['participant_id'].isin(good_participant_ids)]

    local_paths = df['materialized'].str.replace('/UCAP/Data/', 'ucap/')
    df.insert(1, 'local_path', local_paths)

    hashes = df['extra'].apply(lambda x: f'md5:{x["hashes"]["md5"]}')
    df.insert(2, 'hash', hashes)

    urls = df['path'].apply(lambda x: f'{BASE_URL}{x}')
    df.insert(3, 'url', urls)

    file_exts = df['name'].apply(lambda x: Path(x).suffix[1:])
    file_types = file_exts.map(FILE_TYPE_DICT)
    df.insert(4, 'file_type', file_types)

    df = df[['local_path', 'url', 'hash', 'participant_id',
             'file_type', 'size']]

    df.to_csv(MANIFEST_FILE, index=False)
