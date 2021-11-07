import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='step-mne',
    version='0.0.1',
    author='Alexander Enge',
    author_email='alexander.enge@hu-berlin.de',
    description='Single trial EEG pipeline using MNE-Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alexenge/step-mne',
    project_urls={
        'Issue trackers': 'https://github.com/alexenge/step-mne/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=['step_mne'],
    install_requires=[
        'chardet',
        'mne>=0.24.0',
        'pandas>=1.0.0',
    ],
    python_requires='>=3.8',
)
