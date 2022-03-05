from mne import Report


def create_report(
    participant_id, raw, ica, clean, events, event_id, epochs, evokeds):
    """Creates a HTML report for the processing steps of one participant."""

    # Initialize HTML report
    report = Report(title=f'Report for {participant_id}', verbose=False)

    # Add raw data
    report.add_raw(raw, title='Raw data', butterfly=False)

    # Add ICA
    if ica is not None:
        report.add_ica(ica, title='ICA', inst=raw)

    # Add cleaned data
    report.add_raw(clean, title='Cleaned data')

    # Add events
    sfreq = clean.info['sfreq']
    report.add_events(
        events, title='Event triggers', event_id=event_id, sfreq=sfreq)

    # Add epochs
    report.add_epochs(epochs, title='Epochs')

    # Add evokeds
    report.add_evokeds(evokeds)  # Automatically uses comments as titles

    return report
