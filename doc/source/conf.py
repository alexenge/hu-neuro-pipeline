# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import inspect
import os
import sys
from pathlib import Path

import pandas as pd

# Make sure the pipeline package is available
sys.path.insert(0, Path(__file__).parents[2].resolve().as_posix())
import pipeline

# Make sure Quarto and its dependencies are available
# This seems to be necessary when install Quarto via conda -- it doesn't by
# itself find the `share` directory or `deno` in the correct places
bin_path = Path(sys.executable).parent
share_path = bin_path.parent.joinpath('share')
os.environ['QUARTO_SHARE_PATH'] = share_path.joinpath('quarto').resolve().as_posix()
os.environ['DENO_DIR'] = bin_path.resolve().as_posix()
os.environ['DENO_BIN'] = bin_path.joinpath('deno').resolve().as_posix()
os.environ['QUARTO_DENO'] = bin_path.joinpath('deno').resolve().as_posix()

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'hu-neuro-pipeline'
copyright = '2023, Alexander Enge'
author = 'Alexander Enge'
version = '.'.join(pipeline.__version__.split('.', 2)[:2])
release = pipeline.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.autosummary',
              'sphinx.ext.intersphinx',
              'sphinx.ext.linkcode',
              'sphinx.ext.napoleon',
              'sphinxcontrib.bibtex',
              'sphinxcontrib.apa',
              'myst_nb',
              'sphinx_copybutton',
              'sphinx_gallery.load_style']
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']
source_suffix = {
    '.rst': 'restructuredtext',
    '.qmd': 'myst-nb'
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = 'hu-neuro-pipeline'
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.png'
html_theme = 'sphinx_book_theme'
html_theme_options = {
    'path_to_docs': 'doc',
    'repository_url': 'https://github.com/alexenge/hu-neuro-pipeline',
    'repository_branch': 'main',
    'use_repository_button': True,
    'use_issues_button': True,
    'use_edit_page_button': True,
    'use_fullscreen_button': False,
    'extra_navbar': ''}
html_static_path = ['_static']
html_css_files = ['custom.css']
pygments_style = 'tango'

# -- Options for sphinx.linkscode --------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html

def linkcode_resolve(domain, info):
    def find_source():
        # try to find the file and line number, based on code from numpy:
        # https://github.com/numpy/numpy/blob/master/doc/source/conf.py#L286
        obj = sys.modules[info['module']]
        for part in info['fullname'].split('.'):
            obj = getattr(obj, part)
        fn = inspect.getsourcefile(obj)
        fn = os.path.relpath(fn, start=os.path.dirname(pipeline.__file__))
        source, lineno = inspect.getsourcelines(obj)
        return fn, lineno, lineno + len(source) - 1

    if domain != 'py' or not info['module']:
        return None
    try:
        filename = 'pipeline/%s#L%d-L%d' % find_source()
    except Exception:
        filename = info['module'].replace('.', '/') + '.py'
    tag = 'main' if 'dev' in release else ('v' + release)

    return "https://github.com/alexenge/hu-neuro-pipeline/blob/%s/%s" % (tag, filename)

# -- InterSphinx options -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'mne': ('https://mne.tools/stable', None),
    'numpy': ('https://numpy.org/doc/stable', None),
    'scipy': ('https://docs.scipy.org/doc/scipy', None),
    'matplotlib': ('https://matplotlib.org/stable', None),
    'sklearn': ('https://scikit-learn.org/stable', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/stable', None),
}

# -- Napoleon options --------------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration

napoleon_preprocess_types = True

## -- sphinxcontrib-bibtex options -------------------------------------------
# https://sphinxcontrib-bibtex.readthedocs.io/en/latest/usage.html#configuration

bibtex_bibfiles = ['references.bib']
bibtex_default_style = 'apa'

# -- nbsphinx options --------------------------------------------------------
# https://nbsphinx.readthedocs.io/en/latest/configuration.html

nb_execution_timeout = 600
nb_custom_formats = {
    '.pct.py': ['jupytext.reads', {'fmt': 'py:percent'}],
    '.qmd': ['jupytext.reads', {'fmt': 'quarto'}],
    '.Rmd': ['jupytext.reads', {'fmt': 'Rmd'}]
}
nb_render_image_options = {'width': '70%', 'align': 'center'}

# -- Convert Python syntax examples to R syntax examples ---------------------


def convert_input_tables():
    """Converts tables with Python syntax examples to R syntax examples."""

    input_dir = Path(__file__).parent / 'tables_py'
    input_files = input_dir.glob('*.csv')

    output_dir = Path(__file__).parent / 'tables_r'
    output_dir.mkdir(exist_ok=True)

    for input_file in input_files:

        df = pd.read_csv(input_file)

        df.to_csv(input_file, index=False)

        for col_name in ['Argument', 'Example']:

            python_strings = list(df[col_name])

            r_strings = []

            for python_string in python_strings:

                if not isinstance(python_string, str):

                    r_strings.append(python_string)

                    continue

                r_string = python_string.\
                    replace('\'', 'PLACEHOLDER').\
                    replace('\"', '\'').\
                    replace('PLACEHOLDER', '\"').\
                    replace('[(', 'list(c(').\
                    replace(')]', '))').\
                    replace('[[', 'list(c(').\
                    replace(': [', ' = list(').\
                    replace('[', 'c(').\
                    replace(']', ')').\
                    replace('{', 'list(').\
                    replace('":', '" =').\
                    replace('}', ')').\
                    replace('``(', '``c(').\
                    replace('True', 'TRUE').\
                    replace('False', 'FALSE').\
                    replace('None', 'NULL').\
                    replace('np.arange', 'seq').\
                    replace('np.linspace', 'seq').\
                    replace('step=', 'by = ').\
                    replace('num=', 'length.out = ').\
                    replace(r'^nan$', '')
                r_strings.append(r_string)

            df[col_name] = r_strings

        output_file = output_dir / input_file.name
        df.to_csv(output_file, index=False)


def convert_input_page():

    input_file = Path(__file__).parent / 'inputs_py.rst'

    with open(input_file, 'r') as file:
        input = file.read()
        output = input.\
            replace('Python syntax', 'R syntax').\
            replace(' tables/', ' tables_r/')
    
    output_file = Path(__file__).parent / 'inputs_r.rst'

    with open(output_file, 'w') as file:
        file.write(output)


def run_before_docs(app):
    """Runs some functions before the documentation is built."""

    convert_input_tables()
    convert_input_page()


def setup(app):
    """Controls the setup of the Sphinx documentation build process."""

    app.connect('builder-inited', run_before_docs)
