import numpy as np
from mne.io import BaseRaw

from ..preprocessing import PreprocessingConfig, PreprocessingPipeline


def test_preprocessing_config(sample_preprocessing_config):
    """Tests the PreprocessingConfig class."""

    config = sample_preprocessing_config

    assert isinstance(config, PreprocessingConfig)
    assert config.downsample_sfreq == 100
    assert config.heog_channels == 'auto'
    assert config.veog_channels == 'auto'
    assert config.montage == 'easycap-M1'
    assert config.bad_channels == ['Fp1', 'PO8']
    assert config.ref_channels == 'average'
    assert config.ica_method == 'fastica'
    assert config.ica_n_components is None
    assert config.ica_eog_channels == 'auto'


def test_preprocessing_pipeline(sample_preprocessing_pipeline,
                                sample_input_pipeline):
    """Tests the PreprocessingPipeline class with ICA correction."""

    pipeline = sample_preprocessing_pipeline

    assert isinstance(pipeline, PreprocessingPipeline)
    assert isinstance(pipeline.raw, BaseRaw)
    assert pipeline.raw.info['sfreq'] == 100.0
    assert pipeline.raw.get_channel_types(['HEOG', 'VEOG']) == \
        ['eog', 'eog']

    # All EEG channels should have locations set via montage
    assert all(~np.isnan(ch['loc']).all() for ch in pipeline.raw.info['chs']
               if ch['kind'] == 2)

    assert pipeline.raw.info['custom_ref_applied']
    assert pipeline.ica_eog_channels == ['HEOG', 'VEOG']
    assert len(pipeline.ica.labels_['eog/0/HEOG']) > 0
    assert len(pipeline.ica.labels_['eog/1/VEOG']) > 0
    assert pipeline.raw.info['highpass'] == 0.1
    assert pipeline.raw.info['lowpass'] == 40.0

    # Preprocessing should reduce the average standard deviation of the data
    std_input = sample_input_pipeline.raw.get_data().std(axis=1).mean()
    std_preprocessed = pipeline.raw.get_data().std(axis=1).mean()
    assert std_input / std_preprocessed > 2.0


def test_preprocessing_pipeline_besa(sample_preprocessing_pipeline_besa,
                                     sample_input_pipeline_besa):
    """Tests the PreprocessingPipeline class with BESA correction."""

    pipeline = sample_preprocessing_pipeline_besa

    # Preprocessing should reduce the average standard deviation of the data
    std_input = sample_input_pipeline_besa.raw.get_data().std(axis=1).mean()
    std_preprocessed = pipeline.raw.get_data().std(axis=1).mean()
    assert std_input / std_preprocessed > 2.0
