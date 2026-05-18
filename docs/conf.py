# Configuration file for the Sphinx documentation builder.
import importlib
import pkgutil
import sys
from pathlib import Path

CONF_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CONF_DIR.parent
HANDCRAFTED_DIR = CONF_DIR / "handcrafted"
EXCLUDE_CLASSES = {
    "EventAction",
    "EventCondition",
    "EventBehavior",
    "CommonAction",
    "CommonCondition",
    "SpatialCondition",
}

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.append(str(CONF_DIR / "ext"))
sys.path.append(str(Path(__file__).parent.resolve() / "ext"))

# -- Project information -----------------------------------------------------

project = "Tuxemon"
copyright = "2015-2026, William Edwards"
author = "William Edwards"
release = "alpha"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.napoleon",
    "script_documenter",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "autogen"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Options for Autodoc and Napoleon ----------------------------------------

autodoc_typehints = "description"
napoleon_numpy_docstring = False
napoleon_custom_sections = [
    "Script usage",
    ("Script parameters", "params_style"),
]

# -- Handcrafted script lists ------------------------------------------------


def generate_script_lists(_: object) -> None:
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
    write_list(
        "tuxemon.event.behaviors",
        "Behavior",
        HANDCRAFTED_DIR / "behavior_list.rst",
    )
    write_list(
        "tuxemon.core.effects",
        "Effect",
        HANDCRAFTED_DIR / "core_effects_list.rst",
    )
    write_list(
        "tuxemon.core.conditions",
        "Condition",
        HANDCRAFTED_DIR / "core_conditions_list.rst",
    )


def setup(app: object) -> None:
    """Connect the generate_script_lists function to the 'builder-inited' Sphinx event."""
    app.connect("builder-inited", generate_script_lists)
