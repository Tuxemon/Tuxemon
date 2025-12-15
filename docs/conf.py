# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import Any

CONF_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CONF_DIR.parent
HANDCRAFTED_DIR = CONF_DIR / "handcrafted"
EXCLUDE_CLASSES = {
    "EventAction",
    "EventCondition",
    "CommonAction",
    "CommonCondition",
    "SpatialCondition",
}

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.append(str(CONF_DIR / "ext"))
sys.path.append(str(Path(__file__).parent.resolve() / "ext"))

# -- Project information -----------------------------------------------------

project = "Tuxemon"
copyright = "2015-2025, William Edwards"
author = "William Edwards"

# The full version, including alpha/beta/rc tags
# You could potentially get a dynamic version from your project here
release = "alpha"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "script_documenter",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "autogen"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here.
html_static_path = ["_static"]


# -- Options for Autodoc and Napoleon ----------------------------------------

# Tell Autodoc how to display type hints
autodoc_typehints = "description"

# Disable NumPy docstring parsing if you primarily use Google-style docstrings
napoleon_numpy_docstring = False

# Define your custom Napoleon sections
napoleon_custom_sections = [
    "Script usage",
    ("Script parameters", "params_style"),
]


# -- Apidoc Automation -------------------------------------------------------


def run_apidoc(_: Any) -> None:
    """
    Automatically runs sphinx-apidoc before the Sphinx build process begins.
    This generates API reference files for all your project's modules.
    """
    ignore_paths: list[str] = []

    argv = [
        "-f",  # Force overwrite output files
        "-e",  # Put documentation for each module on its own page
        "-M",  # Look for module files instead of package files
        "-o",  # Output directory
        "autogen",  # Name of the directory to store the generated files
        str(PROJECT_ROOT),  # Use the repo root so apidoc scans everything
    ] + ignore_paths

    from sphinx.ext import apidoc

    apidoc.main(argv)


def generate_script_lists(_: Any) -> None:
    """Generate action_list.rst and condition_list.rst automatically."""

    def write_list(package_name: str, suffix: str, outfile: Path) -> None:
        package = importlib.import_module(package_name)
        lines = []
        for _, modname, _ in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(f"{package_name}.{modname}")
            for name, obj in vars(module).items():
                if isinstance(obj, type) and obj.__module__ == module.__name__:
                    if name.endswith(suffix) and name not in EXCLUDE_CLASSES:
                        entry = f".. autoscriptinfoclass:: {module.__name__}.{name}"
                        lines.append(entry)
                        print(f"Adding {entry} to {outfile}")
        outfile.write_text("\n".join(sorted(lines)))
        print(f"Generated {outfile} with {len(lines)} entries")

    write_list(
        "tuxemon.event.actions", "Action", HANDCRAFTED_DIR / "action_list.rst"
    )
    write_list(
        "tuxemon.event.conditions",
        "Condition",
        HANDCRAFTED_DIR / "condition_list.rst",
    )
    # write_list("tuxemon.core.effects", "Effect", HANDCRAFTED_DIR / "core_effects_list.rst")
    write_list(
        "tuxemon.core.conditions",
        "Condition",
        HANDCRAFTED_DIR / "core_conditions_list.rst",
    )


def setup(app: Any) -> None:
    """Connect the run_apidoc function to the 'builder-inited' Sphinx event."""
    app.connect("builder-inited", run_apidoc)
    app.connect("builder-inited", generate_script_lists)
