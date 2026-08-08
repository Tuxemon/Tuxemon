.PHONY: default setup test-setup dev-setup run test format lint type

default: run

setup:
	pip install -U -r ./requirements.txt

test-setup:
	pip install -e .[test]

dev-setup:
	pip install -e .[dev]

run:
	python ./run_tuxemon.py

test:
	tox -e py3

format:
	tox -e fmt

lint:
	tox -e lint

type:
	tox -e type
