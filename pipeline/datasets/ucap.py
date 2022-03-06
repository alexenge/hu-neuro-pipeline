import pooch

# Basic url for the UCAP study from the OSF API
base_url='https://files.de-1.osf.io/v1/resources/hdxvb/providers/osfstorage/'

# Individual files relative to the `base_url`
urls = {'cali/09_cali.matrix': '59cf1d40b83f6902b0a6223c',
        'cali/47_cali.matrix': '59cf1d699ad5a102cd5c5d5f',
        'log/09_test.txt' : '59cf1bcf594d9002c57fb913',
        'log/47_test.txt' : '59cf1c47b83f6902b2a63a88',
        'raw/09.eeg': '59cf46586c613b02968f68d0',
        'raw/09.vhdr': '59cf17186c613b02978f427e',
        'raw/09.vmrk': '59cf17209ad5a102cd5c5b9b',
        'raw/47.eeg': '59cf5689594d9002c67ffc1b',
        'raw/47.vhdr': '59cf0889b83f6902b2a63609',
        'raw/47.vmrk': '59cf08979ad5a102ce5c7ed1'}

# Hash sums for pooch to check
hashes = {'cali/09_cali.matrix': 'md5:af36707efa1ba6f40e51cc22f87f1bd8',
          'cali/47_cali.matrix': 'md5:d485eaa980e4d039d5fad75f8d4d604a',
          'log/09_test.txt' : 'md5:3cb0fce820de4d9676785f786c9bfe90',
          'log/47_test.txt' : 'md5:b8d742098e07312c103d0f48ecd94b9b',
          'raw/09.eeg': 'md5:294453b8b3f9e426aa49953e5be21cda',
          'raw/09.vhdr': 'md5:1910df2cb36fbc5373da2c7ae607dea7',
          'raw/09.vmrk': 'md5:65caf0211aa3054b5e081ac28838dc3c',
          'raw/47.eeg': 'md5:7a4f34c38932b748c5ec982ed1ae42c1',
          'raw/47.vhdr': 'md5:871c26bbe195fc797c4343cfbbc845eb',
          'raw/47.vmrk': 'md5:62a9633c19fc35fccf0ff1843e7bfdf9'}

# Construct fetcher for getting UCAP data
fetcher = pooch.create(
    path=pooch.os_cache('hu-neuro-pipeline'), # Local cache
    base_url=base_url,
    env='PIPELINE_DATA_DIR', # Environment variable to overwrite `path`
    registry=hashes,
    urls={key: f'{base_url}{uuid}' for key, uuid in urls.items()},
)

def get_paths():
    """Downloads sample data from the UCAP study and returns the paths."""

    # Get local file paths and fetch if necessary
    paths = [fetcher.fetch(key) for key in fetcher.registry.keys()]

    # Sort by file type
    paths_dict = {
        'vhdr_files': [p for p in paths if p.endswith('.vhdr')],
        'log_files': [p for p in paths if p.endswith('.txt')],
        'cali_files': [p for p in paths if p.endswith('.matrix')]}

    return paths_dict
