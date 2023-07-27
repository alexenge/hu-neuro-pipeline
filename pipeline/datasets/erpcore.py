import json
import sys
import urllib.request
from pathlib import Path
from types import ModuleType
from warnings import warn

import pooch

osf_ids = {'ERN': 'q6gwp',
           'LRP': '28e6c',
           'MMN': '5q4xs',
           'N170': 'pfde9',
           'N2pc': 'yefrq',
           'N400': '29xpq',
           'P3': 'etdkz'}

local_cache = 'hu-neuro-pipeline'


class ern(ModuleType):
    def get_paths(n_participants=40):
        return get_paths('ERN', n_participants)


class lrp(ModuleType):
    def get_paths(n_participants=40):
        return get_paths('LRP', n_participants)


class mmn(ModuleType):
    def get_paths(n_participants=40):
        return get_paths('MMN', n_participants)


class n170(ModuleType):
    def get_paths(n_participants=40):
        return get_paths('N170', n_participants)


class n2pc(ModuleType):
    def get_paths(n_participants=40):
        return get_paths('N2pc', n_participants)


class n400(ModuleType):
    def get_paths(n_participants=40):
        return get_paths('N400', n_participants)


class p3(ModuleType):
    def get_paths(n_participants=40):
        return get_paths('P3', n_participants)


def add_submodule(submod):
    name = submod.__name__
    sys.modules[__name__ + '.' + name] = submod(name)


add_submodule(ern)
add_submodule(lrp)
add_submodule(mmn)
add_submodule(n170)
add_submodule(n2pc)
add_submodule(n400)
add_submodule(p3)


def get_paths(component=None, n_participants=40):
    """Downloads sample data from the ERP CORE study and returns the paths."""

    assert component is not None and component in osf_ids.keys(), \
        f'`component` must be one of {list(osf_ids.keys())}'
    max_participants = 40
    assert n_participants in range(1, max_participants + 1), \
        f'`n_participants` must be an integer between 1 and {max_participants}'
    if n_participants < max_participants:
        warn(f'Only fetching data for the first {n_participants} ' +
             f'participant(s). This will not be reflected in the ' +
             f'`participants.tsv` file of the BIDS structure, which will ' +
             f'contain all {max_participants} participants.')

    exclude_range = range(n_participants + 1, max_participants + 1)
    exclude_dirs = ['sub-{:03d}'.format(id) for id in exclude_range]
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
        fetcher.fetch(file)
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
        remote_path = file['attributes']['materialized']
        local_path = str(Path(f'{local_dir}/{remote_path}'))
        urls[local_path] = base_url + file['attributes']['path']
        hashes[local_path] = 'md5:' + file['attributes']['extra']['hashes']['md5']

    fetcher = pooch.create(
        path=pooch.os_cache(local_cache),
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
