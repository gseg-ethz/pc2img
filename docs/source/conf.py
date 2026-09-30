"""Sphinx configuration for the pc2img documentation site.

Minimal by design: no intersphinx, no nitpicky mode, no type-alias map — pc2img's
public surface does not need the cross-repo cross-referencing PCHandler's conf.py
carries. ``release``/``version`` are derived from the installed distribution
(``importlib.metadata``) rather than a literal string or a release-please
version marker comment, so there is nothing here for release-please to rewrite.
"""

import importlib.metadata

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pc2img"
copyright = "2026, ETH Zurich, Geosensors and Engineering Geodesy (GSEG)"
author = "Nicholas Meyer"

# Dynamic version: read from the installed distribution (setuptools_scm derives
# it from git tags at build time). No literal version string, no
# x-release-please-version marker.
release = importlib.metadata.version("pc2img")
version = release

# -- General configuration ----------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

napoleon_numpy_docstring = True

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"

exclude_patterns = ["_build"]

# -- Options for HTML output ---------------------------------------------------

html_theme = "sphinx_rtd_theme"
