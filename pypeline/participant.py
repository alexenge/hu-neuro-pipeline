from dataclasses import dataclass

from .epoching import EpochingConfig, EpochingPipeline
from .input import InputConfig, InputPipeline
from .preproc import PreprocConfig, PreprocPipeline


@dataclass
class ParticipantConfig:
    """The configuration for the participant pipeline."""

    input_config: InputConfig = None
    preproc_config: PreprocConfig = None
    epoching_config: EpochingConfig = None


class ParticipantPipeline:
    """The participant pipeline for processing the EEG data of a single
    participant."""

    def __init__(self, config: ParticipantConfig):

        self.input_pipeline = InputPipeline(config.input_config)
        self.preproc_pipeline = \
            PreprocPipeline(config.preproc_config)
        self.epoching_pipeline = EpochingPipeline(config.epoching_config)

    def run(self):

        self.input_pipeline.run()

        self.preproc_pipeline.run(self.input_pipeline.raw,
                                  self.input_pipeline.besa)

        self.epoching_pipeline.run(self.preproc_pipeline.raw,
                                   self.input_pipeline.log)

        # TODO: Maybe this could be done on the continuous raw data (i.e.,
        # fully within the preproc pipeline) rather then on the epochs.
        # Let's check once we added automatic break detection (#212).
        if self.preproc_pipeline.config.bad_channels == 'auto':
            self._detect_bad_channels_and_rerun()

    def _detect_bad_channels_and_rerun(self):

        bad_channels = self.epoching_pipeline.detect_bad_channels()

        if len(bad_channels) > 0:
            self.preproc_pipeline.config.bad_channels = bad_channels
            self.preproc_pipeline.run(self.input_pipeline.raw,
                                      self.input_pipeline.besa)
            self.epoching_pipeline.run(self.preproc_pipeline.raw,
                                       self.input_pipeline.log)
