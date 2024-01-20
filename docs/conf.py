# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.append(os.path.abspath("./ext"))
sys.path.insert(0, os.path.abspath('../'))


# -- Project information -----------------------------------------------------
from typing import Any

project = 'Tuxemon'
copyright = '2015-2024, William Edwards'
author = 'William Edwards'

# The full version, including alpha/beta/rc tags
release = 'alpha'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    'sphinx.ext.napoleon',
    'script_documenter',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

autodoc_typehints = "description"

napoleon_numpy_docstring = False

napoleon_custom_sections = [
    "Script usage",
    ("Script parameters", "params_style")
]


# Apidoc call to generate automatic reference docs. Taken from
# https://github.com/readthedocs/readthedocs.org/issues/1139#issuecomment-398083449
def run_apidoc(_: Any) -> None:
    ignore_paths: list[str] = []

    argv = [
        "-f",
        "-e",
        "-M",
        "-o",
        "autogen",
        ".."
    ] + ignore_paths

    # Sphinx 1.7+
    from sphinx.ext import apidoc
    apidoc.main(argv)


def setup(app: Any) -> None:
    app.connect('builder-inited', run_apidoc)
