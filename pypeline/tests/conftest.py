import pytest

from ..datasets.ucap import get_ucap
from ..input import InputConfig


@pytest.fixture(scope="session")
def sample_data():
    """Downloads some EEG data to use for running all tests."""

    return get_ucap(participants=['05', '07'])


@pytest.fixture(scope="session")
def sample_input_config(sample_data):
    """Creates an InputConfig for the sample data."""

    return InputConfig(raw_file=sample_data['raw_files'][0],
                       log_file=sample_data['log_files'][0],
                       besa_file=sample_data['besa_files'][0])


@pytest.fixture(scope="session")
def sample_input_config_combine(sample_data):
    """Creates an InputConfig for the case when a participant has
    multiple EEG files that need to be combined."""

    return InputConfig(raw_file=sample_data['raw_files'][0:2])
