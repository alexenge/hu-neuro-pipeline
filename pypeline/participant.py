from .input import InputConfig, InputPipeline
from .preprocessing import PreprocessingConfig, PreprocessingPipeline


class ParticipantPipeline:

    def __init__(self,
                 input_config: InputConfig,
                 preprocessing_config: PreprocessingConfig):

        self.input_pipeline = InputPipeline(input_config)
        self.preprocessing_pipeline = \
            PreprocessingPipeline(preprocessing_config)

    def run(self):

        self.input_pipeline.run()

        raw = self.input_pipeline.raw
        if hasattr(self.input_pipeline, 'besa'):
            besa = self.input_pipeline.besa
        else:
            besa = None

        self.preprocessing_pipeline.run(raw, besa)
