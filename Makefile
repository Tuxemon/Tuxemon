# Default target to run when `make` is called by itself
.PHONY: default
default: run

# Validate all JSON data in db
.PHONY: validate
validate:
	PYTHONPATH=. python scripts/schema.py --validate
	PYTHONPATH=. python scripts/test_actions.py

# Install dependencies
.PHONY: setup
setup:
	pip install -U -r ./requirements.txt

# Run the game
.PHONY: run
run:
	python ./run_tuxemon.py

# Run tests
.PHONY: test
test:
	tox -e py3

# Format code
.PHONY: format
format:
	tox -e fmt
