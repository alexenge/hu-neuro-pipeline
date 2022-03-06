import os
import os.path as op

import setuptools


def package_tree(pkgroot):
    """Get the submodule list  (adapted from MNE/VisPy)."""

    # Get all submodules based on their `__init__.py`
    path = op.dirname(__file__)
    subdirs = [op.relpath(i[0], path).replace(op.sep, '.')
               for i in os.walk(op.join(path, pkgroot))
               if '__init__.py' in i[2]]

    return sorted(subdirs)


if __name__ == "__main__":

    # Paste README as long description
    with open('README.md', 'r', encoding='utf-8') as fh:
        long_description = fh.read()

    # Actual setup
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
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
        ],
        packages=package_tree('pipeline'),
        install_requires=[
            'chardet',
            'joblib',
            'matplotlib',
            'mne >= 0.24.0',
            'pandas >= 1.1.0, <= 1.3.5',
            'pooch >= 1.5',
            'scikit-learn'
        ],
        python_requires='>=3.8',
    )
