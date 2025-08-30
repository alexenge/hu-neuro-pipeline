from .epoching import EpochingConfig, EpochingPipeline
from .input import InputConfig, InputPipeline
from .preprocessing import PreprocessingConfig, PreprocessingPipeline


class ParticipantPipeline:

    def __init__(self,
                 input_config: InputConfig,
                 preprocessing_config: PreprocessingConfig,
                 epoching_config: EpochingConfig):

        self.input_pipeline = InputPipeline(input_config)
        self.preprocessing_pipeline = \
            PreprocessingPipeline(preprocessing_config)
        self.epoching_pipeline = EpochingPipeline(epoching_config)

    def run(self):

        self.input_pipeline.run()

        self.preprocessing_pipeline.run(self.input_pipeline.raw,
                                        self.input_pipeline.besa)

        self.epoching_pipeline.run(self.preprocessing_pipeline.raw,
                                   self.input_pipeline.log)

        # TODO: If preprocessing demands auto bad channels, detect them
        # here via a method in epoching_pipeline, then re-run both of them
