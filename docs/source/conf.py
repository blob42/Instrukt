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
        "myst_parser",
        "sphinx_markdown_builder"
        ]

source_suffix = {
        ".rst": "restructuredtext",
        ".md": "markdown",
        }

myst_enable_extensions = [
        "colon_fence",
        ]

markdown_anchor_sections = True

autodoc_pydantic_model_show_json = False
autodoc_pydantic_field_list_validators = False
autodoc_pydantic_config_members = False
autodoc_pydantic_model_show_config_summary = False
autodoc_pydantic_model_show_validator_members = False
autodoc_pydantic_model_show_validator_summary = False
autodoc_pydantic_model_signature_prefix = "class"
autodoc_pydantic_field_signature_prefix = "param"
autodoc_member_order = "groupwise"
autoclass_content = "both"
autodoc_typehints_format = "short"

autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "inherited-members": "BaseModel",
    "undoc-members": True,
    "special-members": "__call__",
}

templates_path = ['_templates']

# exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = "sphinx_rtd_theme"
#https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html

# html_theme = "sphinx_book_theme"
html_static_path = ['_static']
