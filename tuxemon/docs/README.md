Guide
#######
http://raxcloud.blogspot.com/2013/02/documenting-python-code-using-sphinx.html


Generate Documentation
##########################

To regenerate:
`cd docs
rm -rf *.rst Makefile
cd ../
sphinx-apidoc -H Tuxemon -e -F -o docs .`

Then, to update:
`make clean; make html`
