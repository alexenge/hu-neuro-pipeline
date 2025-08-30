from ..participant import ParticipantPipeline


def test_participant_pipeline(sample_input_config,
                              sample_preprocessing_config,
                              sample_epoching_config):

    participant_pipeline = ParticipantPipeline(sample_input_config,
                                               sample_preprocessing_config,
                                               sample_epoching_config)
    participant_pipeline.run()


def test_participant_pipeline_besa(sample_input_config_besa,
                                   sample_preprocessing_config_besa,
                                   sample_epoching_config):

    participant_pipeline = ParticipantPipeline(sample_input_config_besa,
                                               sample_preprocessing_config_besa,
                                               sample_epoching_config)
    participant_pipeline.run()
