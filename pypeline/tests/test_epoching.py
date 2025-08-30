import numpy as np
import pandas as pd
from mne import Epochs

from ..epoching import EpochingConfig, EpochingPipeline


def test_epoching_config(sample_epoching_config):
    """Tests the EpochingConfig class."""

    config = sample_epoching_config

    assert isinstance(config, EpochingConfig)
    assert config.triggers == [201, 202, 203, 204, 205, 206, 207, 208,
                               211, 212, 213, 214, 215, 216, 217, 218]
    assert config.triggers_column is None
    assert config.tmin == -0.2
    assert config.tmax == 0.8
    assert config.baseline == (-0.2, 0.0)
    assert config.reject == 200.0


def test_epoching_pipeline(sample_epoching_pipeline):
    """Tests the EpochingPipeline class."""

    pipeline = sample_epoching_pipeline

    assert isinstance(pipeline, EpochingPipeline)
    assert isinstance(pipeline.events, np.ndarray)
    assert isinstance(pipeline.event_id, dict)
    assert (set(pipeline.event_id.values()) == set(pipeline.config.triggers))
    assert set(pipeline.event_id.keys()) == \
        set(map(str, pipeline.config.triggers))
    assert all(trigger in pipeline.events[:, 2]
               for trigger in pipeline.config.triggers)
    assert isinstance(pipeline.epochs, Epochs)
    assert isinstance(pipeline.epochs.metadata, pd.DataFrame)
    assert isinstance(pipeline.bad_ixs, list)
    assert len(pipeline.bad_ixs) > 0


def test_epoching_pipeline_match(sample_epoching_pipeline_match):
    """Tests the EpochingPipeline class with a triggers column to match."""

    pipeline = sample_epoching_pipeline_match

    assert len(pipeline.epochs) > 0
    assert len(pipeline.epochs) < 1920
    triggers_column = pipeline.config.triggers_column
    assert np.array_equal(pipeline.epochs.events[:, 2],
                          pipeline.epochs.metadata[triggers_column].values)
