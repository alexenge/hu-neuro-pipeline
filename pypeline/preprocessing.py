from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from warnings import warn

import pandas as pd
from mne import set_bipolar_reference
from mne.channels import make_standard_montage, read_custom_montage
from mne.channels.montage import DigMontage, get_builtin_montages
from mne.io import BaseRaw
from mne.preprocessing import ICA


@dataclass
class PreprocessingConfig:
    """The configuration for the preprocessing pipeline."""

    downsample_sfreq: float = None
    heog_channels: list[str] | str = 'auto'
    veog_channels: list[str] | str = 'auto'
    montage: str | PathLike = 'easycap-M1'
    bad_channels: list[str] | str = 'auto'
    ref_channels: list[str] | str = 'average'
    ica_method: str = 'fastica'
    ica_n_components: int | float = None
    ica_eog_channels: list[str] | str = 'auto'
    highpass_freq: float = 0.1
    lowpass_freq: float = 40.0


class PreprocessingPipeline:
    """The preprocessing pipeline for cleaning the raw EEG data."""

    def __init__(self, config):

        assert isinstance(config, PreprocessingConfig), \
            "`config` must be an instance of the `PreprocessingConfig` class"
        self.config = config

    def run(self, raw, besa=None):
        """Run the preprocessing pipeline."""

        assert isinstance(raw, BaseRaw), \
            "`raw` must be an instance of the `mne.io.BaseRaw` class"
        self.raw = raw.copy()

        if self.config.downsample_sfreq is not None:
            self._resample()

        if self.config.heog_channels is not None:
            self._add_heog()

        if self.config.veog_channels is not None:
            self._add_veog()

        self._adjust_channel_types()

        self._apply_montage()

        if self.config.bad_channels is not None:
            if self.config.bad_channels != 'auto':
                self._interpolate_bad_channels()

        self._set_eeg_reference()

        if besa is not None:
            assert isinstance(besa, pd.DataFrame), \
                "`besa` must be a `pandas.DataFrame`"
            self.besa = besa
            self._correct_besa()

        if self.config.ica_method is not None:
            if self.config.ica_eog_channels == 'auto':
                self.ica_eog_channels = ['HEOG', 'VEOG']
            else:
                self.ica_eog_channels = self.config.ica_eog_channels
            self._correct_ica()

        if self.config.lowpass_freq is not None \
                or self.config.highpass_freq is not None:
            self._filter()

    def _resample(self):
        """Resample the raw data to the specified sampling frequency."""

        self.raw.resample(self.config.downsample_sfreq)

    def _add_heog(self):
        """Add a bipolar HEOG channel to the raw data."""

        if self.config.heog_channels == 'auto':
            self.heog_channels = AUTO_HEOG_CHANNELS
        else:
            self.heog_channels = self.config.heog_channels

        self._add_eog(self.heog_channels, name='HEOG')

    def _add_veog(self):
        """Add a bipolar VEOG channel to the raw data."""

        if self.config.veog_channels == 'auto':
            self.veog_channels = AUTO_VEOG_CHANNELS
        else:
            self.veog_channels = self.config.veog_channels

        self._add_eog(self.veog_channels, name='VEOG')

    def _add_eog(self, channels, name):
        """Add a bipolar EOG channel to the raw data."""

        channels = [ch for ch in channels if ch in self.raw.ch_names]

        assert len(channels) == 2, ('Invalid channel selection for computing '
                                    f'bipolar channel "{name}". Please '
                                    'provide exactly two channels that are '
                                    'present in the EEG data')

        anode = channels[0]
        cathode = channels[1]

        self.raw = set_bipolar_reference(self.raw, anode, cathode, name,
                                         drop_refs=False, verbose=False)
        self.raw.set_channel_types({name: 'eog'})

    def _apply_montage(self):
        """Apply a standard or custom montage to the raw data."""

        if not isinstance(self.config.montage, DigMontage):

            if Path(self.config.montage).exists():
                montage = read_custom_montage(self.config.montage)

            elif self.config.montage in get_builtin_montages():
                montage = make_standard_montage(self.config.montage)

            else:
                raise ValueError('`montage` must be a valid file path, the '
                                 'name of a valid standard montage, or an MNE '
                                 '`DigMontage` object')

        else:
            montage = self.config.montage

        self.raw.set_montage(montage, match_case=False, on_missing='warn')

    def _adjust_channel_types(self):
        """Adjust the channel types of the raw data."""

        self._adjust_channel_type(DEFAULT_EOG_CHANNELS, type='eog')
        self._adjust_channel_type(DEFAULT_MISC_CHANNELS, type='misc')

    def _adjust_channel_type(self, channels, type):
        """Adjust the channel type of the specified channels."""

        for ch_name in channels:
            if ch_name in self.raw.ch_names:
                self.raw.set_channel_types({ch_name: type},
                                           on_unit_change='ignore')

    def _interpolate_bad_channels(self):
        """Interpolate bad channels in the raw data."""

        self.raw.info['bads'] += self.config.bad_channels
        self.raw.interpolate_bads()

    def _set_eeg_reference(self):
        """Set the EEG reference to the specified channels."""

        self.raw.set_eeg_reference(self.config.ref_channels)

    def _correct_besa(self):
        """Correct the raw data using the BESA/MSEC procedure."""

        # Subset BESA matrix to only channels that are in the data
        besa = self.besa.copy()
        eeg_channels = self.raw.copy().pick_types(eeg=True).ch_names
        eeg_channels_upper = pd.Series(eeg_channels).str.upper().values
        besa.index = besa.index.str.upper()
        besa.columns = besa.columns.str.upper()
        row_channels = [ch for ch in besa.index if ch in eeg_channels_upper]
        col_channels = [ch for ch in besa.columns if ch in eeg_channels_upper]
        besa = besa.reindex(index=row_channels, columns=col_channels)

        eeg_data, _ = self.raw[eeg_channels]
        eeg_data = besa.values.dot(eeg_data)
        self.raw[eeg_channels] = eeg_data

    def _correct_ica(self, random_seed=1234):
        """Correct the raw data using independent component analysis (ICA)."""

        n_components = self.config.ica_n_components
        method = self.config.ica_method
        eog_channels = self.ica_eog_channels

        if n_components is not None:
            if n_components >= 1.0 and not isinstance(n_components, int):
                warn('Converting `ica_n_components` to integer: '
                     f'{n_components} -> {int(n_components)}')
                n_components = int(n_components)

        raw_ica = self.raw.copy()
        raw_ica.load_data().filter(l_freq=1, h_freq=None, verbose=False)
        ica = ICA(n_components, random_state=random_seed, method=method,
                  max_iter='auto')
        ica.fit(raw_ica)

        eog_indices, _ = ica.find_bads_eog(self.raw, ch_name=eog_channels,
                                           verbose=False)
        ica.exclude = eog_indices

        self.ica = ica
        self.raw = ica.apply(self.raw)

    def _filter(self):
        """Filter the raw data using a bandpass filter."""

        self.raw.filter(self.config.highpass_freq,
                        self.config.lowpass_freq,
                        n_jobs=1, picks='eeg')


AUTO_HEOG_CHANNELS = ['F9', 'F10', 'Afp9', 'Afp10', 'HEOG_left', 'HEOG_right']
AUTO_VEOG_CHANNELS = ['Fp1', 'FP1', 'Auge_u',
                      'IO1', 'VEOG_lower', 'VEOG_upper']

DEFAULT_EOG_CHANNELS = ['HEOG', 'VEOG', 'IO1', 'IO2', 'Afp9', 'Afp10', 'Auge_u',
                        'VEOG_upper', 'VEOG_lower', 'HEOG_left', 'HEOG_right']
DEFAULT_MISC_CHANNELS = ['A1', 'A2', 'M1', 'M2', 'audio', 'sound', 'pulse']
