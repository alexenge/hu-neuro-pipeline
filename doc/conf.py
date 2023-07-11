# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib
import sys

sys.path.insert(0, pathlib.Path(__file__).parents[1].resolve().as_posix())

import pipeline

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
              'nbsphinx',
              'sphinx_copybutton',
              'sphinx_gallery.load_style']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '**.ipynb_checkpoints']

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
        import inspect
        import os
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

# -- nbsphinx options --------------------------------------------------------
# https://nbsphinx.readthedocs.io/en/latest/configuration.html

nbsphinx_custom_formats = {
    '.Rmd': ['jupytext.reads', {'fmt': 'Rmd'}]
}

# -- Sphinx-Gallery options --------------------------------------------------
# https://sphinx-gallery.github.io/stable/configuration.html
sphinx_gallery_conf = {
     'examples_dirs': '../examples',   # path to your example scripts
     'gallery_dirs': 'auto_examples',  # path to where to save gallery generated output
}
