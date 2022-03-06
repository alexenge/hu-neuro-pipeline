"""Single trial EEG pipeline at the Neurocognitive Psychology lab,
Humboldt-Universität zu Berlin"""

# Import submodules
from . import datasets

# Make central functions available as top level imports
from .group import group_pipeline
from .participant import participant_pipeline

# Get current package version
try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "unknown version"
    version_tuple = (0, 0, "unknown version")
