import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from mne import Report, set_log_level


def create_report(
    participant_id, raw, ica, clean, events, event_id, epochs, evokeds):
    """Creates a HTML report for the processing steps of one participant."""

    # Disable warnings about number of open figures
    mpl.rcParams.update({'figure.max_open_warning': 0})
    plt.ioff()

    # Initialize HTML report
    print('Creating HTML report')
    set_log_level('ERROR')
    report = Report(title=f'Report for {participant_id}', verbose=False)

    # Add raw data info
    report.add_raw(raw, title='Raw data', butterfly=False)

    # Add raw time series plots
    n_figs = 10
    raw_figs = plot_time_series(raw, n_figs)
    captions = [f'Segment {i + 1} of {n_figs}' for i in range(n_figs)]
    report.add_figure(
        raw_figs, title='Raw time series', caption=captions, tags=('raw',))

    # Add ICA
    if ica is not None:
        raw.info['bads'] = []  # Else plotting ICA fails
        report.add_ica(ica, title='ICA', inst=raw)

    # Add cleaned data info
    report.add_raw(
        clean, title='Cleaned data', butterfly=False, tags=('clean',))

    # Add cleaned time series plots
    clean_figs = plot_time_series(clean, n_figs)
    report.add_figure(clean_figs, title='Cleaned time series',
                      caption=captions, tags=('clean',))

    # Add events
    sfreq = clean.info['sfreq']
    report.add_events(
        events, title='Event triggers', event_id=event_id, sfreq=sfreq)

    # Add epochs
    report.add_epochs(epochs, title='Epochs')

    # Add evokeds
    report.add_evokeds(evokeds)  # Automatically uses comments as titles
    set_log_level('INFO')

    return report


def plot_time_series(raw, n=10, duration=10.):
    """Plots some seconds of raw data for all channels at `n` time points."""

    # Get evenly spaced starting time points
    starts = np.linspace(0, raw.times[-1], num=n, endpoint=False).astype('int')

    # Create an all-channel plot for each time window
    n_channels = len(raw.ch_names)
    figs = [raw.plot(
        start=start,
        duration=duration,
        n_channels=n_channels,
        bad_color='red',
        show=False,
        show_scrollbars=False,
        show_scalebars=False)
        for start in starts]
    
    return figs
