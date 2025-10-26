from os import PathLike

import pandas as pd
from mne.io import BaseRaw
from pandas.api.types import is_list_like

from ..input import InputPipeline


def test_input_pipeline(sample_input_pipeline):
    """Tests the InputPipeline class."""

    pipeline = sample_input_pipeline

    assert isinstance(pipeline, InputPipeline)
    assert isinstance(pipeline.raw_file, str)
    assert isinstance(pipeline.log_file, str)
    assert isinstance(pipeline.raw, BaseRaw)
    assert pipeline.raw.info['subject_info']['his_id'] == '09'
    assert isinstance(pipeline.log, pd.DataFrame)


def test_input_pipeline_besa(sample_input_pipeline_besa):
    """Tests the InputPipeline class incl. BESA file."""

    pipeline = sample_input_pipeline_besa

    assert isinstance(pipeline.besa_file, str)
    assert isinstance(pipeline.besa, pd.DataFrame)


def test_input_pipeline_combine(sample_input_pipeline_combine):
    """Tests the input pipeline class for the case when a participant has
    multiple EEG files that need to be combined."""

    pipeline = sample_input_pipeline_combine

    assert is_list_like(pipeline.raw_file)
    assert isinstance(pipeline.raw, BaseRaw)
    assert pipeline.raw.info['subject_info']['his_id'] == '09_12'
