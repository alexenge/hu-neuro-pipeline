from os import PathLike
from pathlib import Path
from typing import Optional, Union

import chardet
import pandas as pd
from mne.io import concatenate_raws, read_raw
from pandas.api.types import is_list_like


class InputPipeline:
    """The pipeline for reading the raw EEG data and metadata."""

    def __init__(self,
                 raw_file: Union[str, PathLike, list[Union[str, PathLike]]],
                 log_file: Optional[Union[str, PathLike, pd.DataFrame]] = None,
                 besa_file: Optional[Union[str, PathLike]] = None) -> None:

        self.raw_file = raw_file
        self.log_file = log_file
        self.besa_file = besa_file

    def run(self):
        """Runs the input pipeline to read data and metadata."""

        self._read_raw()

        self._get_participant_id()

        self._read_log()

        self._read_besa()

    def _read_raw(self):
        """Reads raw data from the specified file(s)."""

        if is_list_like(self.raw_file):
            raws = [read_raw(elem, preload=True)
                    for elem in self.raw_file]
            self.raw = concatenate_raws(raws)

        else:
            self.raw = read_raw(self.raw_file, preload=True)

    def _get_participant_id(self):
        """Generates a participant ID based on the raw file name(s)."""

        if is_list_like(self.raw_file):
            ids = [Path(elem).stem for elem in self.raw_file]
            participant_id = '_'.join(ids)

        else:
            participant_id = Path(self.raw_file).stem

        if self.raw.info['subject_info'] is not None:
            self.raw.info['subject_info'].update({'his_id': participant_id})
        else:
            self.raw.info['subject_info'] = {'his_id': participant_id}

    def _read_log(self):
        """Reads the behavioral log file with information about each EEG
        trial."""

        if self.log_file is None:
            self.log = None

        elif isinstance(self.log_file, pd.DataFrame):
            self.log = self.log_file

        else:
            with open(self.log_file, 'rb') as f:
                data = f.read()
            chardet_res = chardet.detect(data)
            encoding = chardet_res['encoding']

            if Path(self.log_file).suffix == '.csv':
                self.log = pd.read_csv(self.log_file,
                                       encoding=encoding)

            else:
                self.log = pd.read_csv(self.log_file, delimiter='\t',
                                       encoding=encoding)

    def _read_besa(self):
        """Reads the BESA file containing the ocular correction matrix."""

        if self.besa_file is None:
            self.besa = None

        else:
            self.besa = pd.read_csv(self.besa_file, delimiter='\t',
                                    index_col=0)
