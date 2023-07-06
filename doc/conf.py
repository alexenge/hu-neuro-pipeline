# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pathlib
import sys
sys.path.insert(0, pathlib.Path(__file__).parents[1].resolve().as_posix())

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'hu-neuro-pipeline'
copyright = '2023, Alexander Enge'
author = 'Alexander Enge'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.autosummary',
              'sphinx.ext.intersphinx',
              'sphinx.ext.linkcode',
              'sphinx.ext.napoleon',
              'sphinx.ext.viewcode',
              'nbsphinx',
              'sphinx_copybutton',
              'sphinx_gallery.load_style']


from urllib.parse import quote

def linkcode_resolve(domain, info):
    # print(f"domain={domain}, info={info}")
    if domain != 'py':
        return None
    if not info['module']:
        return None
    filename = quote(info['module'].replace('.', '/'))
    if not filename.startswith("tests"):
        filename = "src/" + filename
    if "fullname" in info:
        anchor = info["fullname"]
        anchor = "#:~:text=" + quote(anchor.split(".")[-1])
    else:
        anchor = ""

    # github
    result = "https://github.com/alexenge/hu-neuro-pipeline/blob/master/%s.py%s" % (filename, anchor)
    # print(result)
    return result



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
