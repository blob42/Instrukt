# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import toml 

with open("../../pyproject.toml") as f:
    data = toml.load(f)

project = 'Instrukt'
copyright = '2023, Chakib Benziane'
author = 'Chakib Benziane'


version = data["tool"]["poetry"]["version"]
release = version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
        "sphinx.ext.autodoc",
        "sphinx.ext.autodoc.typehints",
        "sphinx.ext.autosummary",
        "sphinx.ext.napoleon",
        "sphinx.ext.viewcode",
        "sphinxcontrib.autodoc_pydantic",
        "sphinx_copybutton",
        "sphinx_tabs.tabs",
        "IPython.sphinxext.ipython_console_highlighting",
        "IPython.sphinxext.ipython_directive",
        ]

templates_path = ['_templates']
exclude_patterns = ["build"]



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"
# html_theme = "sphinx_book_theme"
html_static_path = ['_static']
