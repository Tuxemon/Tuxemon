from pythonforandroid.recipe import PythonRecipe


class TuxemonRecipe(PythonRecipe):
    version = 'development'
    url = 'https://github.com/Tuxemon/Tuxemon/archive/development.zip'
    depends = ['setuptools']
    site_packages_name = 'tuxemon'
    call_hostpython_via_targetpython = False
    install_in_hostpython = True

recipe = TuxemonRecipe()
