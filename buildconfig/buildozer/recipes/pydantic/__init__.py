from pythonforandroid.recipe import PythonRecipe


class PydanticRecipe(PythonRecipe):
    version = "2.13.4"
    url = "https://files.pythonhosted.org/packages/18/a5/b60d21ac674192f8ab0ba4e9fd860690f9b4a6e51ca5df118733b487d8d6/pydantic-{version}.tar.gz"
    name = "pydantic"
    depends = ["pydantic_core", "setuptools"]
    site_packages_name = "pydantic"
    call_hostpython_via_targetpython = False
    install_in_hostpython = True


recipe = PydanticRecipe()