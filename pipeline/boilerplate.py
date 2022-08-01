from platform import python_version
from statistics import mean, median

import mne


def boilerplate(config):
    """Auto-creates part of the methods section based on pipeline options."""

    # Prepare empty lists
    boilerplate = []
    references = []

    # Pipeline intro
    text = (
        'The continuous EEG from {n_participants} participants was processed '
        'offline using the single trial EEG pipeline proposed by Frömer et '
        'al. (2018). The pipeline was implemented with the packages MNE '
        '(Version {mne_version}; Gramfort et al., 2013) and STEP-MNE '
        '({step_mne_url}) for Python (Version {python_version}; Van Rossum & '
        'Drake, 2009).\n')
    text = text.format(
        n_participants=len(config['vhdr_files']),
        mne_version=mne.__version__,
        step_mne_url='https://github.com/alexenge/step-mne',  # TODO: Add version
        python_version=python_version()
    )
    boilerplate.append(text)
    references.append(
        'Frömer, R., Maier, M., & Abdel Rahman, R. (2018). Group-level EEG-'
        'processing pipeline for flexible single trial-based analyses '
        'including linear mixed models. Frontiers in Neuroscience, 12, 48. '
        'https://doi.org/10.3389/fnins.2018.00048')
    references.append(
        'Gramfort, A., Luessi, M., Larson, E., Engemann, D. A., Strohmeier, '
        'D., Brodbeck, C., Goj, R., Jas, M., Brooks, T., Parkkonen, L., & '
        'Hämäläinen, M. (2013). MEG and EEG data analysis with MNE-Python. '
        'Frontiers in Neuroscience, 7. '
        'https://doi.org/10.3389/fnins.2013.00267')
    references.append(
        'Van Rossum, G., & Drake, F. L. (2009). Python 3 reference manual. '
        'CreateSpace.')
    
    # Downsampling
    if config['downsample_sfreq'] is not None:
        text = (
            'The data from each participant were downsampled to '
            '{downsample_sfreq} Hz. '
        )
        text = text.format(downsample_sfreq = int(config['downsample_sfreq']))
        boilerplate.append(text)

    # Bad channels
    ns_bads = [len(l) for l in config['bad_channels']]
    if sum(ns_bads) > 0:
        if config['bad_channels'] == 'auto':
            text = (
                'An average of {mean_bads} EEG channels per participant '
                '(Mdn = {mdn_bads}, range {min_bads} to {max_bads}) were '
                'automatically flagged for bad data quality. Channels were '
                'flagged as bad if their inclusion would have led to the '
                'rejection of at least 5% of all available epochs for the '
                'participant, according to the artifact rejection threshold '
                'defined below. The signal for these channels was replaced by '
                'the signal of the neighboring channels using spherical '
                'spline interpolation (Perrin et al., 1989). '
            )
        else:
            text = (
                'An average of {mean_bads} EEG channels per participant '
                '(Mdn = {mdn_bads}, range {min_bads} to {max_bads}) were '
                'manually flagged for bad data quality. The signal for these '
                'channels was replaced by the signal of the neighboring '
                'channels using spherical spline interpolation (Perrin et '
                'al., 1989). '
            )
        text = text.format(
            mean_bads = '{:.1f}'.format(mean(ns_bads)),
            mdn_bads = median(ns_bads),
            min_bads = min(ns_bads),
            max_bads = max(ns_bads)
        )
        boilerplate.append(text)
        references.append(
            'Perrin, F., Pernier, J., Bertrand, O., & Echallier, J. F. '
            '(1989). Spherical splines for scalp potential and current '
            'density mapping. Electroencephalography and Clinical '
            'Neurophysiology, 72(2), 184–187. '
            'https://doi.org/10.1016/0013-4694(89)90180-6'
        )
    else:
        boilerplate.append(
            'No EEG channels were excluded or interpolated based on bad data '
            'quality. '
        )
    
    # Re-referencing
    boilerplate.append(
        'Next, the data were re-referenced to the common average of all EEG '
        'channels.'
    )

    # Ocular correction
    if config['ica_method'] is not None:
        boilerplate.append(
            'Artifacts resulting from blinks and eye movements were corrected '
            'using independent component analysis (ICA). For this, we '
            'temporarily low-pass filtered the data at 1 Hz and extracted the '
            'first 15 independent components using the FastICA algorithm '
            '(Hyvärinen, 1999). Components were then removed automatically '
            'using `find_bads_eog` function in MNE-Python). This function '
            'iteratievly removes components if they are signifcantly '
            'correlated (z > 3.0) with either of two virtual EOG channels '
            '(VEOG: Fp1 - IO1, HEOG: F9 - F10).'
        )
        references.append(
            'Hyvärinen, A. (1999). Fast and robust fixed-point algorithms for '
            'independent component analysis. IEEE Transactions on Neural '
            'Networks, 10(3), 626–634. https://doi.org/10.1109/72.761722'
        )
        
    
    # Combine and print
    boilerplate = ''.join(boilerplate)
    print(boilerplate)
