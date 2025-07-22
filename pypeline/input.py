from dataclasses import dataclass
from os import PathLike
from pathlib import Path

import chardet
import pandas as pd
from mne.io import concatenate_raws, read_raw
from pandas.api.types import is_list_like


@dataclass
class InputConfig:
    raw_file: str | PathLike | list[str | PathLike]
    log_file: str | PathLike | pd.DataFrame = None
    besa_file: str | PathLike = None


class InputPipeline:

    def __init__(self, config):

        assert isinstance(config, InputConfig), \
            "`config` must be an instance of the `InputConfig` class"

        self.config = config

    def run(self):

        self.raw = self._read_raw()

        self.participant_id = self._get_participant_id()

        if self.config.log_file is not None:
            self.log = self._read_log()

        if self.config.besa_file is not None:
            self.besa = self._read_besa()

    def _read_raw(self):
        """Reads raw data from the specified file(s)."""

        if is_list_like(self.config.raw_file):
            raws = [read_raw(elem, preload=True)
                    for elem in self.config.raw_file]
            return concatenate_raws(raws)

        else:
            return read_raw(self.config.raw_file, preload=True)

    def _get_participant_id(self):
        """Generates a participant ID based on the raw file name(s)."""

        if is_list_like(self.config.raw_file):
            ids = [Path(elem).stem for elem in self.config.raw_file]
            return '_'.join(ids)

        else:
            return Path(self.config.raw_file).stem

    def _read_log(self):
        """Reads the behavioral log file with information about each EEG
        trial."""

        if isinstance(self.config.log_file, pd.DataFrame):
            return self.config.log_file

        else:
            with open(self.config.log_file, 'rb') as f:
                data = f.read()
            chardet_res = chardet.detect(data)
            encoding = chardet_res['encoding']

            if Path(self.config.log_file).suffix == '.csv':
                return pd.read_csv(self.config.log_file,
                                   encoding=encoding)

            else:
                return pd.read_csv(self.config.log_file, delimiter='\t',
                                   encoding=encoding)

    def _read_besa(self):
        """Reads the BESA file containing the ocular correction matrix."""

        return pd.read_csv(self.config.besa_file,
                           delimiter='\t', index_col=0)
