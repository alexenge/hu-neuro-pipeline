import pandas as pd
from mne.io import BaseRaw

from ..input import InputConfig, InputPipeline


def test_input_config(sample_input_config):
    """Tests the InputConfig class."""

    config = sample_input_config

    assert isinstance(config, InputConfig)
    assert isinstance(config.raw_file, str)
    assert isinstance(config.log_file, str)


def test_input_config_besa(sample_input_config_besa):
    """Tests the InputConfig class incl. BESA file."""

    config = sample_input_config_besa

    assert isinstance(config.besa_file, str)


def test_input_config_combine(sample_input_config_combine):
    """Tests the InputConfig class for the case when a participant has
    multiple EEG files that need to be combined."""

    config = sample_input_config_combine

    assert isinstance(config.raw_file, list)
    assert len(config.raw_file) == 2
    assert all(isinstance(f, str) for f in config.raw_file)


def test_input_pipeline(sample_input_pipeline):
    """Tests the InputPipeline class."""

    pipeline = sample_input_pipeline

    assert isinstance(pipeline, InputPipeline)
    assert isinstance(pipeline.raw, BaseRaw)
    assert pipeline.raw.info['subject_info']['his_id'] == '05'
    assert isinstance(pipeline.log, pd.DataFrame)


def test_input_pipeline_besa(sample_input_pipeline_besa):
    """Tests the InputPipeline class incl. BESA file."""

    pipeline = sample_input_pipeline_besa

    assert isinstance(pipeline.besa, pd.DataFrame)


def test_input_pipeline_combine(sample_input_pipeline_combine):
    """Tests the input pipeline class for the case when a participant has
    multiple EEG files that need to be combined."""

    pipeline = sample_input_pipeline_combine

    assert isinstance(pipeline.raw, BaseRaw)
    assert pipeline.raw.info['subject_info']['his_id'] == '05_07'
