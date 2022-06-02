#!/usr/bin/python

import os
from argparse import ArgumentParser
from tuxemon.db import (
    db,
    EconomyModel,
    EncounterModel,
    EnvironmentModel,
    InventoryModel,
    ItemModel,
    MonsterModel,
    MusicModel,
    NpcModel,
    SoundModel,
    TechniqueModel,
)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-g",
        "--generate",
        dest="generate",
        action="store_true",
        default=False,
        help="Generate JSON schemas",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        dest="output",
        default="schemas",
        help="Schema output directory",
    )
    parser.add_argument(
        "--validate",
        dest="validate",
        action="store_true",
        default=False,
        help="Validate all JSON entries in db",
    )
    args = parser.parse_args()

    if args.generate:
        print(f"Writing JSON schemas to '{args.output}'...")
        with open(os.path.join(args.output, "economy-schema.json"), "w") as f:
            f.write(EconomyModel.schema_json(indent=2))
        with open(
            os.path.join(args.output, "encounter-schema.json"), "w"
        ) as f:
            f.write(EncounterModel.schema_json(indent=2))
        with open(
            os.path.join(args.output, "environment-schema.json"), "w"
        ) as f:
            f.write(EnvironmentModel.schema_json(indent=2))
        with open(
            os.path.join(args.output, "inventory-schema.json"), "w"
        ) as f:
            f.write(InventoryModel.schema_json(indent=2))
        with open(os.path.join(args.output, "item-schema.json"), "w") as f:
            f.write(ItemModel.schema_json(indent=2))
        with open(os.path.join(args.output, "monster-schema.json"), "w") as f:
            f.write(MonsterModel.schema_json(indent=2))
        with open(os.path.join(args.output, "music-schema.json"), "w") as f:
            f.write(MusicModel.schema_json(indent=2))
        with open(os.path.join(args.output, "npc-schema.json"), "w") as f:
            f.write(NpcModel.schema_json(indent=2))
        with open(os.path.join(args.output, "sound-schema.json"), "w") as f:
            f.write(SoundModel.schema_json(indent=2))
        with open(
            os.path.join(args.output, "technique-schema.json"), "w"
        ) as f:
            f.write(TechniqueModel.schema_json(indent=2))

    if args.validate:
        db.load(validate=True)
