from os import PathLike
from typing import Optional, Union

import pandas as pd

from .epoching import EpochingConfig, EpochingPipeline
from .input import InputPipeline
from .preprocessing import PreprocessingConfig, PreprocessingPipeline


class ParticipantPipeline:

    def __init__(self,
                 raw_file: Union[str, PathLike, list[Union[str, PathLike]]],
                 log_file: Optional[Union[str, PathLike, pd.DataFrame]] = None,
                 besa_file: Optional[Union[str, PathLike]] = None,
                 preprocessing_config: PreprocessingConfig = None,
                 epoching_config: EpochingConfig = None):

        self.input_pipeline = InputPipeline(raw_file, log_file, besa_file)
        self.preprocessing_pipeline = \
            PreprocessingPipeline(preprocessing_config)
        self.epoching_pipeline = EpochingPipeline(epoching_config)

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
