import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='hu-neuro-pipeline',
    author='Alexander Enge',
    author_email='alexander.enge@hu-berlin.de',
    description='Single trial EEG pipeline at the Neurocognitive '
                'Psychology Lab, Humboldt-Universität zu Berlin',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alexenge/hu-neuro-pipeline',
    project_urls={
        'Issue trackers': 'https://github.com/alexenge/hu-neuro-pipeline/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=['pipeline'],
    install_requires=[
        'chardet',
        'joblib',
        'mne>=0.24.0',
        'pandas',
        'scikit-learn'
    ],
    python_requires='>=3.8',
)
