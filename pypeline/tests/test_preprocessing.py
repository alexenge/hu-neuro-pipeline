import numpy as np
from mne.io import BaseRaw

from ..preprocessing import PreprocessingConfig, PreprocessingPipeline


def test_preprocessing_config():
    """Tests the PreprocessingConfig class."""

    config = PreprocessingConfig(downsample_sfreq=100,
                                 heog_channels='auto',
                                 veog_channels='auto',
                                 montage='easycap-M1',
                                 bad_channels=['Fp1', 'PO8'],
                                 ref_channels='average',
                                 ica_method='fastica',
                                 ica_n_components=None,
                                 ica_eog_channels='auto')

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


def test_preprocessing_pipeline(sample_preprocessing_config,
                                sample_input_pipeline):
    """Tests the PreprocessingPipeline class with ICA correction."""

    preprocessing_pipeline = PreprocessingPipeline(sample_preprocessing_config)
    raw = sample_input_pipeline.raw
    preprocessing_pipeline.run(raw)

    assert isinstance(preprocessing_pipeline, PreprocessingPipeline)
    assert isinstance(preprocessing_pipeline.raw, BaseRaw)
    assert preprocessing_pipeline.raw.info['sfreq'] == 100.0
    assert preprocessing_pipeline.raw.get_channel_types(['HEOG', 'VEOG']) == \
        ['eog', 'eog']

    # All EEG channels should have locations set via montage
    assert all(~np.isnan(ch['loc']).all()
               for ch in preprocessing_pipeline.raw.info['chs']
               if ch['kind'] == 2)

    assert preprocessing_pipeline.raw.info['custom_ref_applied']
    assert preprocessing_pipeline.ica_eog_channels == ['HEOG', 'VEOG']
    assert len(preprocessing_pipeline.ica.labels_['eog/0/HEOG']) > 0
    assert len(preprocessing_pipeline.ica.labels_['eog/1/VEOG']) > 0
    assert preprocessing_pipeline.raw.info['highpass'] == 0.1
    assert preprocessing_pipeline.raw.info['lowpass'] == 40.0

    # Preprocessing should reduce the mean standard deviation over time
    assert raw.get_data().std(axis=1).mean() / \
        preprocessing_pipeline.raw.get_data().std(axis=1).mean() > 2.0


def test_preprocessing_pipeline_besa(sample_preprocessing_config_besa,
                                     sample_input_pipeline_besa):
    """Tests the PreprocessingPipeline class with BESA correction."""

    preprocessing_pipeline = \
        PreprocessingPipeline(sample_preprocessing_config_besa)
    raw = sample_input_pipeline_besa.raw
    besa = sample_input_pipeline_besa.besa
    preprocessing_pipeline.run(raw, besa)

    # Preprocessing should reduce the mean standard deviation over time
    assert raw.get_data().std(axis=1).mean() / \
        preprocessing_pipeline.raw.get_data().std(axis=1).mean() > 2.0
