import json
import re
import urllib.request

import pooch

# URL of the UCAP repo files on OSF
base_url = 'https://files.de-1.osf.io/v1/resources/hdxvb/providers/osfstorage'

# Local cache to download the files to
local_cache = 'hu-neuro-pipeline'


def construct_fetcher(remote_dir, local_dir):
    """Constructs a pooch fetcher for getting UCAP remote files locally."""

    # Parse remote files on OSF
    urls = {}
    hashes = {}
    with urllib.request.urlopen(f'{base_url}/{remote_dir}') as url:
        files = json.loads(url.read().decode())['data']
        files_attributes = [file['attributes'] for file in files]

        # Natural-sort files by name
        # Necessary because log file names are without leading zeros
        natsort = lambda s: [int(t) if t.isdigit() else t.lower()
                             for t in re.split('(\d+)', s)]
        files_attributes_sorted = sorted(
            files_attributes, key=lambda d: natsort(d['name']))

        # Extract file URLs and hashsums
        for attributes in files_attributes_sorted:
            local_path = local_dir + attributes['name']
            urls[local_path] = base_url + attributes['path']
            hashes[local_path] = 'md5:' + attributes['extra']['hashes']['md5']

    # Construct fetcher for getting UCAP data
    fetcher = pooch.create(
        path=pooch.os_cache(local_cache),
        base_url=base_url,
        env='PIPELINE_DATA_DIR',
        registry=hashes,
        urls=urls,
    )

    return fetcher


def get_paths(n_participants=40):
    """Downloads sample data from the UCAP study and returns the paths."""

    # Prepare dict of file paths for return
    paths = {}

    # Get raw EEG files - note that there are 3 files per participant
    eeg_fetcher = construct_fetcher('59cf07fa6c613b02958f3364/', 'raw/')
    n_files = int(n_participants) * 3
    eeg_paths = list(eeg_fetcher.registry.keys())[:n_files]
    eeg_paths = [eeg_fetcher.fetch(path) for path in eeg_paths]
    vhdr_paths = [path for path in eeg_paths if path.endswith('.vhdr')]
    paths['vhdr_files'] = vhdr_paths

    # Extract participant IDs
    participant_ids = [
        path.split('/')[-1].replace('.vhdr', '') for path in vhdr_paths]

    # Get corresponding behavioral log files
    log_fetcher = construct_fetcher('59cf12259ad5a102cc5c4b93/', 'log/')
    log_paths = [f'log/{int(p_id)}_test.txt' for p_id in participant_ids]
    log_paths = [log_fetcher.fetch(path) for path in log_paths]
    paths['log_files'] = log_paths

    # Get corresponding BESA/MSEC cali files
    cali_fetcher = construct_fetcher('59cf089e6c613b02968f5724/', 'cali/')
    cali_paths = [f'cali/{p_id}_cali.matrix' for p_id in participant_ids]
    cali_paths = [cali_fetcher.fetch(path) for path in cali_paths]
    paths['besa_files'] = cali_paths

    return paths
