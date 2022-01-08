from functools import partial
from glob import glob
from os import path

import pandas as pd
from joblib import Parallel, delayed

from .helpers import check_participant_input, compute_grands, compute_grands_df
from .participant import participant_pipeline
from .perm import compute_perm, compute_perm_tfr
from .savers import save_config, save_df, save_evokeds


def group_pipeline(
    vhdr_files,
    log_files,
    export_dir,
    downsample_sfreq=None,
    veog_channels='auto',
    heog_channels='auto',
    montage='easycap-M1',
    bad_channels='auto',
    ocular_correction='fastica',
    highpass_freq=0.1,
    lowpass_freq=40.,
    triggers=None,
    epochs_tmin=-0.5,
    epochs_tmax=1.5,
    baseline=(-0.2, 0.0),
    skip_log_rows=None,
    skip_log_conditions=None,
    reject_peak_to_peak=200.,
    reject_flat=1.,
    components={'name': [], 'tmin': [], 'tmax': [], 'roi': []},
    condition_cols=None,
    perform_tfr=False,
    tfr_freqs=range(4, 51, 2),
    tfr_cycles=range(2, 26, 1),
    tfr_baseline=(-0.3, -0.1),
    tfr_components={
        'name': [], 'tmin': [], 'tmax': [], 'fmin': [], 'fmax': [], 'roi': []},
    perm_contrasts=[],
    perm_tmin=0.,
    perm_tmax=1.,
    perm_channels=None,
    perm_fmin=None,
    perm_fmax=None,
    clean_dir=None,
    epochs_dir=None,
    to_df=True,
    n_jobs=1
):
    """Processes EEG data for all participants of an experiment.

    For each participant, the raw data is read and cleaned using standard steps
    (downsampling, bad channel interpolation, ocular correction, frequency
    domain filtering). Epochs are created around the `triggers`. Bad epochs are
    removed based on peak-to-peak amplitude. Single trial mean ERP amplitudes
    for ERP `components` of interest are computed and matched to the single
    trial behavioral data from the `log_files`.

    Optionally, this last step is repeated on a time-frequency representation
    (TFR) of the data obtained via Morlet wavelet convolution.

    The result is a single trial data frame which can be used for fitting
    linear mixed-effects models on the mean ERP amplitudes (and power).

    Additionally, by-participant condition averages (`evokeds`) for the ERPs
    (and power) are computed to facilitate plotting. Optionally, these can also
    be tested for condition differences in an exploratory fashion using
    cluster-based permutation tests.

    For details about the pipeline, see Frömer et al. (2018)[1].

    Parameters & returns
    --------------------
    See the README[2] in the GitHub repository for the pipeline.

    Notes
    -----
    [1] https://doi.org/10.3389/fnins.2018.00048
    [2] https://github.com/alexenge/hu-neuro-pipeline/blob/dev/README.md
    """

    # Make sure that TFR frequencies and cycles are lists
    tfr_freqs = list(tfr_freqs)
    tfr_cycles = list(tfr_cycles)

    # Backup input arguments for re-use
    config = locals()

    # Remove arguments that are specific for each participant
    nonshared_keys = [
        'vhdr_files', 'log_files', 'ocular_correction', 'bad_channels',
        'skip_log_rows', 'perm_contrasts', 'perm_tmin', 'perm_tmax',
        'perm_channels', 'perm_fmin', 'perm_fmax', 'n_jobs']
    _ = [config.pop(key) for key in nonshared_keys]

    # Create partial function with only the shared arguments
    pipeline_partial = partial(participant_pipeline, **config)

    # Get input file paths if directories were provided
    if isinstance(vhdr_files, str):
        if path.isdir(vhdr_files):
            vhdr_files = glob(f'{vhdr_files}/*.vhdr')
            vhdr_files.sort()
    if isinstance(log_files, str):
        if path.isdir(log_files):
            log_files = glob(f'{log_files}/*.csv') + \
                glob(f'{log_files}/*.txt') + glob(f'{log_files}/*.tsv')
            log_files.sort()

    # Prepare ocular correction method
    if isinstance(ocular_correction, str):
        if ocular_correction in ['fastica', 'infomax', 'picard']:
            ocular_correction = [ocular_correction] * len(vhdr_files)
        elif path.isdir(ocular_correction):
            ocular_correction = glob(f'{ocular_correction}/*.matrix')
            ocular_correction.sort()

    # Extract participant IDs from filenames
    participant_ids = [path.basename(f).split('.')[0] for f in vhdr_files]

    # Construct lists of bad_channels and skip_log_rows per participant
    bad_channels = check_participant_input(bad_channels, participant_ids)
    skip_log_rows = check_participant_input(skip_log_rows, participant_ids)

    # Combine participant-specific inputs
    participant_args = zip(vhdr_files, log_files, ocular_correction,
                           bad_channels, skip_log_rows)

    # Do processing in parallel
    res = Parallel(n_jobs)(
        delayed(pipeline_partial)(*args) for args in participant_args)

    # Sort outputs into seperate lists
    trials, evokeds, evokeds_dfs, configs = list(map(list, zip(*res)))[0:4]

    # Combine trials and save
    trials = pd.concat(trials, ignore_index=True)
    if export_dir is not None:
        save_df(trials, export_dir, participant_id='all', suffix='trials')

    # Combine evokeds_dfs and save
    evokeds_df = pd.concat(evokeds_dfs, ignore_index=True)
    if export_dir is not None:
        save_df(evokeds_df, export_dir, participant_id='all', suffix='ave')

    # Compute grand averaged ERPs and save
    grands = compute_grands(evokeds)
    grands_df = compute_grands_df(evokeds_df)
    save_evokeds(
        grands, grands_df, export_dir, participant_id='grand', to_df=to_df)

    # Add participant-specific arguments back to config
    config = {'vhdr_files': vhdr_files, 'log_files': log_files,
              'ocular_correction': ocular_correction,
              'bad_channels': bad_channels,
              'skip_log_rows': skip_log_rows, **config, 'n_jobs': n_jobs}

    # Add automatically detected bad channels
    if 'auto' in bad_channels:
        config['auto_bad_channels'] = [cf['bad_channels'] for cf in configs]

    # Save config
    if export_dir is not None:
        save_config(config, export_dir)

    # Define standard returns
    returns = [trials, evokeds_df, config]

    # Cluster based permutation tests for ERPs
    if perm_contrasts != []:
        cluster_df = compute_perm(evokeds, perm_contrasts, perm_tmin,
                                  perm_tmax, perm_channels, n_jobs)
        returns.append(cluster_df)

    # Combine time-frequency results
    if perform_tfr:

        # Sort outputs into seperate lists
        tfr_evokeds, tfr_evokeds_dfs = list(map(list, zip(*res)))[4:6]

        # Combine evokeds_df for power and save
        tfr_evokeds_df = pd.concat(tfr_evokeds_dfs, ignore_index=True)
        if export_dir is not None:
            save_df(tfr_evokeds_df, export_dir,
                    participant_id='all', suffix='tfr-ave')

        # Compute grand averaged power and save
        tfr_grands = compute_grands(tfr_evokeds)
        tfr_grands_df = compute_grands_df(tfr_evokeds_df)
        if export_dir is not None:
            save_evokeds(tfr_grands, tfr_grands_df, export_dir,
                         participant_id='tfr-grand', to_df=to_df)

        # Cluster based permutation tests for ERPs
        tfr_cluster_df = compute_perm_tfr(
            tfr_evokeds, perm_contrasts, perm_tmin, perm_tmax, perm_channels,
            perm_fmin, perm_fmax, n_jobs)

        # Add to the list of returns
        returns += [tfr_evokeds_dfs, tfr_cluster_df]

    return returns
