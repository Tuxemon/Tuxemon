from sphinx.ext.autodoc import ClassDocumenter, ModuleDocumenter
from sphinx.application import Sphinx
from docutils.statemachine import StringList
from typing import Optional


class ScriptClassDocumenter(ClassDocumenter):
    objtype = 'scriptinfoclass'
    directivetype = 'scriptinfoclass'
    priority = ClassDocumenter.priority - 1
    titles_allowed = True

    def add_directive_header(self, sig: str) -> None:
        sourcename = self.get_sourcename()
        name = self.format_name()

        self.add_line(name, sourcename)
        self.add_line("^" * len(name), sourcename)

    def add_content(
        self,
        more_content: Optional[StringList],
        no_docstring: bool = False,
    ) -> None:
        sourcename = self.get_sourcename()
        docstring = self.get_doc()

        if docstring:
            for line in self.process_doc(docstring):
                self.add_line(line, sourcename)


def setup(app: Sphinx) -> None:

    app.setup_extension('sphinx.ext.autodoc')  # Require autodoc extension

    app.add_autodocumenter(ScriptClassDocumenter)
