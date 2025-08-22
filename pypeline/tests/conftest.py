import pytest

from ..datasets.ucap import get_ucap
from ..input import InputConfig, InputPipeline
from ..preprocessing import PreprocessingConfig, PreprocessingPipeline


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


@pytest.fixture(scope="session")
def sample_input_pipeline(sample_input_config):
    """Creates and runs an InputPipeline for the sample data."""

    input_pipeline = InputPipeline(sample_input_config)
    input_pipeline.run()
    
    return input_pipeline


@pytest.fixture(scope="session")
def sample_preprocessing_config():
    """Creates a PreprocessingConfig for the sample data."""
    
    return PreprocessingConfig(downsample_sfreq=100,
                               heog_channels='auto',
                               veog_channels='auto',
                               montage='easycap-M1',
                               bad_channels=['Fp1', 'PO8'],
                               ref_channels='average',
                               ica_method='fastica',
                               ica_n_components=20,
                               ica_eog_channels='auto')
