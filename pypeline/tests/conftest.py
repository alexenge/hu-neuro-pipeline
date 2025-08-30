import numpy as np
import pytest

from ..datasets.ucap import get_ucap
from ..epoching import EpochingConfig, EpochingPipeline
from ..input import InputConfig, InputPipeline
from ..preprocessing import PreprocessingConfig, PreprocessingPipeline


@pytest.fixture(scope='session')
def sample_data():
    """Downloads some EEG data to use for running all tests."""

    return get_ucap(participants=['05', '07'])


@pytest.fixture(scope='session')
def sample_input_config(sample_data):
    """Creates an InputConfig for the sample data."""

    return InputConfig(raw_file=sample_data['raw_files'][0],
                       log_file=sample_data['log_files'][0])


@pytest.fixture(scope='session')
def sample_input_config_besa(sample_data):
    """Creates an InputConfig for the sample data incl. BESA file."""

    return InputConfig(raw_file=sample_data['raw_files'][0],
                       log_file=sample_data['log_files'][0],
                       besa_file=sample_data['besa_files'][0])


@pytest.fixture(scope='session')
def sample_input_config_combine(sample_data):
    """Creates an InputConfig for the case when a participant has
    multiple EEG files that need to be combined."""

    return InputConfig(raw_file=sample_data['raw_files'][0:2])


@pytest.fixture(scope='session')
def sample_input_pipeline(sample_input_config):
    """Creates and runs an InputPipeline for the sample data."""

    input_pipeline = InputPipeline(sample_input_config)
    input_pipeline.run()

    return input_pipeline


@pytest.fixture(scope='session')
def sample_input_pipeline_besa(sample_input_config_besa):
    """Creates and runs an InputPipeline for the sample data using BESA."""

    input_pipeline = InputPipeline(sample_input_config_besa)
    input_pipeline.run()

    return input_pipeline


@pytest.fixture(scope='session')
def sample_input_pipeline_combine(sample_input_config_combine):
    """Creates and runs an InputPipeline for the case when a participant has
    multiple EEG files that need to be combined."""

    input_pipeline = InputPipeline(sample_input_config_combine)
    input_pipeline.run()

    return input_pipeline


@pytest.fixture(scope='session')
def sample_preprocessing_config():
    """Creates a PreprocessingConfig for the sample data using ICA."""

    return PreprocessingConfig(downsample_sfreq=100,
                               bad_channels=['Fp1', 'PO8'])


@pytest.fixture(scope='session')
def sample_preprocessing_config_besa():
    """Creates a PreprocessingConfig for the sample data using BESA."""

    return PreprocessingConfig(downsample_sfreq=100,
                               bad_channels=['Fp1', 'PO8'],
                               ica_method=None)


@pytest.fixture(scope='session')
def sample_preprocessing_pipeline(sample_preprocessing_config,
                                  sample_input_pipeline):
    """Creates and runs a PreprocessingPipeline for the sample data."""

    preprocessing_pipeline = PreprocessingPipeline(sample_preprocessing_config)
    raw = sample_input_pipeline.raw
    preprocessing_pipeline.run(raw)

    return preprocessing_pipeline


@pytest.fixture(scope='session')
def sample_preprocessing_pipeline_besa(sample_preprocessing_config_besa,
                                       sample_input_pipeline_besa):
    """Creates and runs a PreprocessingPipeline for the sample data using BESA."""

    preprocessing_pipeline = \
        PreprocessingPipeline(sample_preprocessing_config_besa)
    raw = sample_input_pipeline_besa.raw
    besa = sample_input_pipeline_besa.besa
    preprocessing_pipeline.run(raw, besa)

    return preprocessing_pipeline


@pytest.fixture(scope='session')
def sample_epoching_config():
    """Creates an EpochingConfig for the sample data."""

    return EpochingConfig(triggers=[201, 202, 203, 204, 205, 206, 207, 208,
                                    211, 212, 213, 214, 215, 216, 217, 218])


@pytest.fixture(scope='session')
def sample_epoching_config_match():
    """Creates an EpochingConfig for the sample data."""

    return EpochingConfig(triggers=[201, 202, 203, 204, 205, 206, 207, 208,
                                    211, 212, 213, 214, 215, 216, 217, 218],
                          triggers_column='bot')


@pytest.fixture(scope='session')
def sample_epoching_pipeline(sample_epoching_config,
                             sample_input_pipeline,
                             sample_preprocessing_pipeline):
    """Creates and runs an EpochingPipeline for the sample data."""

    epoching_pipeline = EpochingPipeline(sample_epoching_config)
    raw = sample_preprocessing_pipeline.raw
    log = sample_input_pipeline.log
    epoching_pipeline.run(raw, log)

    return epoching_pipeline


@pytest.fixture(scope='session')
def sample_epoching_pipeline_match(sample_epoching_config_match,
                                   sample_input_pipeline,
                                   sample_preprocessing_pipeline):
    """Creates and runs an EpochingPipeline for the sample data."""

    epoching_pipeline = EpochingPipeline(sample_epoching_config_match)
    # Let's pretend some trials/triggers are missing from the EEG recording
    raw_to_match = sample_preprocessing_pipeline.raw.copy()
    ixs = np.concatenate([np.arange(0, 1001),
                          np.arange(5000, 6001),
                          np.arange(10000, len(raw_to_match.annotations))])
    raw_to_match.annotations.delete(ixs)
    log = sample_input_pipeline.log
    epoching_pipeline.run(raw_to_match, log)

    return epoching_pipeline
