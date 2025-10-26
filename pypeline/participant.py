from dataclasses import dataclass

from .epoching import EpochingConfig, EpochingPipeline
from .input import InputConfig, InputPipeline
from .preprocessing import PreprocessingConfig, PreprocessingPipeline


@dataclass
class ParticipantConfig:
    """The configuration for the participant pipeline."""

    input_config: InputConfig = None
    preprocessing_config: PreprocessingConfig = None
    epoching_config: EpochingConfig = None


class ParticipantPipeline:
    """The participant pipeline for processing the EEG data of a single
    participant."""

    def __init__(self, config: ParticipantConfig):

        self.input_pipeline = InputPipeline(config.input_config)
        self.preprocessing_pipeline = \
            PreprocessingPipeline(config.preprocessing_config)
        self.epoching_pipeline = EpochingPipeline(config.epoching_config)

    def run(self):

        self.input_pipeline.run()

        self.preprocessing_pipeline.run(self.input_pipeline.raw,
                                        self.input_pipeline.besa)

        self.epoching_pipeline.run(self.preprocessing_pipeline.raw,
                                   self.input_pipeline.log)

        # TODO: Maybe this could be done on the continuous raw data (i.e.,
        # fully within the preprocessing pipeline) rather then on the epochs.
        # Let's check once we added automatic break detection (#212).
        if self.preprocessing_pipeline.config.bad_channels == 'auto':
            self._detect_bad_channels_and_rerun()

    def _detect_bad_channels_and_rerun(self):

        bad_channels = self.epoching_pipeline.detect_bad_channels()

        if len(bad_channels) > 0:
            self.preprocessing_pipeline.config.bad_channels = bad_channels
            self.preprocessing_pipeline.run(self.input_pipeline.raw,
                                            self.input_pipeline.besa)
            self.epoching_pipeline.run(self.preprocessing_pipeline.raw,
                                       self.input_pipeline.log)
