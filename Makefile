# Schemas to generate with `make schemas`
SCHEMAS = schemas/economy-schema.json \
	  schemas/encounter-schema.json \
	  schemas/environment-schema.json \
	  schemas/inventory-schema.json \
	  schemas/item-schema.json \
	  schemas/monster-schema.json \
	  schemas/music-schema.json \
	  schemas/npc-schema.json \
	  schemas/sound-schema.json \
	  schemas/technique-schema.json

# Default target to run when `make` is called by itself
.PHONY: default
default: run

# Generate JSON schemas for all DB models
.PHONY: schemas
schemas: $(SCHEMAS)
$(SCHEMAS) &: tuxemon/db.py
	mkdir -p schemas
	PYTHONPATH=. python scripts/schema.py --generate

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
	pip install pytest
	PYTHONPATH=. pytest tests

# Format code
.PHONY: format
format:
	./scripts/fmt.sh
