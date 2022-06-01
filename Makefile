# Generate JSON schemas for all DB models
.PHONY: schemas
schemas: tuxemon/db.py
	mkdir -p schemas
	PYTHONPATH=. python scripts/schema.py --generate

# Validate all JSON data in db
.PHONY: validate
validate:
	PYTHONPATH=. python scripts/schema.py --validate

# Run the game
.PHONY: run
run:
	python ./run_tuxemon.py
