from dataclasses import dataclass

import numpy as np
from mne import Epochs, events_from_annotations
from mne.io import BaseRaw
from mne.io.brainvision.brainvision import RawBrainVision


@dataclass
class EpochingConfig:
    triggers: list[int] = None
    triggers_column: str = None
    tmin: float = -0.2
    tmax: float = 0.8
    baseline: tuple[float, float] = (-0.2, 0.0)
    reject = 200.0


class EpochingPipeline:

    def __init__(self, config):

        assert isinstance(config, EpochingConfig), \
            "`config` must be an instance of the `EpochingConfig` class"

        self.config = config

    def run(self, raw, log=None):

        assert isinstance(raw, BaseRaw), \
            "`raw` must be an instance of the `mne.io.BaseRaw` class"

        self._get_events(raw)

        self._create_epochs(raw)

        if log is not None:
            participant_id = raw.info['subject_info']['his_id']
            self._add_log(log, participant_id)

        if self.config.reject is not None:
            self._reject_bad_epochs()

    def _get_events(self, raw):

        self.events, self.event_id = events_from_annotations(raw,
                                                             verbose=False)

        if self.config.triggers is not None:
            if isinstance(raw, RawBrainVision):
                self.event_id = {str(trigger): int(trigger)
                                 for trigger in self.config.triggers}
            else:
                self.event_id = {key: value
                                 for key, value in self.event_id.items()
                                 if int(key) in self.config.triggers}

    def _create_epochs(self, raw):

        self.epochs = Epochs(raw, self.events, self.event_id,
                             tmin=self.config.tmin, tmax=self.config.tmax,
                             baseline=self.config.baseline, preload=True)

        # Drop the last sample to produce a nice even number
        self.epochs.crop(tmin=None, tmax=self.config.tmax, include_tmax=False)

    def _add_log(self, log, participant_id):

        if self.config.triggers_column is not None:
            log, self.missing_ixs = self._match_log_to_epochs(log)

        self.epochs.metadata = log

        self.epochs.metadata.insert(0, column='participant_id',
                                    value=participant_id)

    def _match_log_to_epochs(self, log, depth=10):

        assert self.config.triggers_column in log.columns, \
            f'Column \'{self.config.triggers_column}\' is not in the log file'

        events_log = log[self.config.triggers_column].tolist()

        event_id_keys = list(self.epochs.event_id.keys())
        event_id_values = list(self.epochs.event_id.values())
        events_epochs = [int(event_id_keys[event_id_values.index(event)])
                         for event in self.epochs.events[:, 2]]

        previous_repaired = False
        for ix in range(len(events_log)):

            # Add `nan` in case trials are missing at the end of the EEG...
            if len(events_epochs) <= ix:
                print(f'Log file (row index {ix}): Found missing EEG epoch')
                events_epochs.insert(ix, np.nan)

            # ... or if the log and EEG trigers don't match up
            elif events_log[ix] != events_epochs[ix]:
                print(f'Log file (row index {ix}): Found missing EEG epoch')
                events_epochs.insert(ix, np.nan)
                previous_repaired = True

            # If they do match up, check that the next trials do match as well
            elif previous_repaired:
                if events_log[ix:ix + depth] != events_epochs[ix:ix + depth]:
                    print(f'Log file (row index {ix}): '
                          'Assuming missing EEG epoch')
                    events_epochs.insert(ix, np.nan)
                else:
                    previous_repaired = False

        missing_ixs = np.where(np.isnan(events_epochs))[0].tolist()
        print(f'Dropping rows from the log file data: {missing_ixs}')
        log = log.reset_index(drop=True)
        log = log.drop(index=missing_ixs)

        return log, missing_ixs

    def _reject_bad_epochs(self):

        reject_dict = {'eeg': self.config.reject * 1e-6}
        # TODO: Decide if this needs to be done on a copy of the data
        self.epochs.drop_bad(reject_dict)

        self._get_bad_ixs()

    def _get_bad_ixs(self):

        drop_log = [elem for elem in self.epochs.drop_log
                    if 'IGNORED' not in elem]
        self.bad_ixs = [ix for ix, elem in enumerate(drop_log) if elem != ()]
