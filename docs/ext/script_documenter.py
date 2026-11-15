from docutils.statemachine import StringList
from sphinx.application import Sphinx
from sphinx.ext.autodoc import ClassDocumenter


class ScriptClassDocumenter(ClassDocumenter):
    """Custom autodoc documenter for script info classes."""

    objtype = "scriptinfoclass"
    directivetype = "scriptinfoclass"
    priority = ClassDocumenter.priority - 1
    titles_allowed = True

    def add_directive_header(self, sig: str) -> None:
        """Add a simple header with the class name."""
        sourcename = self.get_sourcename()
        name = self.format_name()
        self.add_line(name, sourcename)
        self.add_line("^" * len(name), sourcename)

    def add_content(
        self,
        more_content: StringList | None,
        no_docstring: bool = False,
    ) -> None:
        """Add the processed docstring content if available."""
        sourcename = self.get_sourcename()
        docstring = self.get_doc()
        if docstring:
            for line in self.process_doc(docstring):
                self.add_line(line, sourcename)


def setup(app: Sphinx) -> None:
    """Register the custom ScriptClassDocumenter with Sphinx."""
    app.setup_extension("sphinx.ext.autodoc")
    app.add_autodocumenter(ScriptClassDocumenter)
