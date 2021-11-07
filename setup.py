import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='mne-step',
    version='0.0.1',
    author='Alexander Enge',
    author_email='alexander.enge@hu-berlin.de',
    description='Single trial EEG pipeline using MNE-Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alexenge/mne-step',
    project_urls={
        'Issue trackers': 'https://github.com/alexenge/mne-step/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=['mne_step'],
    install_requires=[
        'chardet>=4.0.0',
        'mne>=0.24.0',
        'pandas>=1.3.0',
    ],
    python_requires='>=3.8',
)