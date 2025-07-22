import pandas as pd
from mne.io import BaseRaw

from ..input import InputConfig, InputPipeline


def test_input_config(sample_data):
    """Tests the InputConfig class."""

    input_config = InputConfig(raw_file=sample_data['raw_files'][0],
                               log_file=sample_data['log_files'][0],
                               besa_file=sample_data['besa_files'][0])

    assert isinstance(input_config, InputConfig)
    assert isinstance(input_config.raw_file, str)
    assert isinstance(input_config.log_file, str)
    assert isinstance(input_config.besa_file, str)


def test_input_pipeline(sample_input_config):
    """Tests the InputPipeline class."""

    input_pipeline = InputPipeline(sample_input_config)

    assert isinstance(input_pipeline, InputPipeline)
    assert input_pipeline.config == sample_input_config

    input_pipeline.run()

    assert isinstance(input_pipeline.raw, BaseRaw)
    assert input_pipeline.participant_id == '05'
    assert isinstance(input_pipeline.log, pd.DataFrame)
    assert isinstance(input_pipeline.besa, pd.DataFrame)


def test_input_pipeline_combine(sample_input_config_combine):
    """Tests the input pipeline class for the case when a participant has
    multiple EEG files that need to be combined."""

    input_pipeline = InputPipeline(sample_input_config_combine)
    input_pipeline.run()

    assert isinstance(input_pipeline.raw, BaseRaw)
    assert input_pipeline.participant_id == '05_07'
