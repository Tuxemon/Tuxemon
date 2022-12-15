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


def write_json_schema(output_dir):
    print(f"Writing JSON schemas to '{output_dir}'...")
    with open(os.path.join(output_dir, "economy-schema.json"), "w") as f:
        f.write(EconomyModel.schema_json(indent=2))
    with open(
        os.path.join(output_dir, "encounter-schema.json"), "w"
    ) as f:
        f.write(EncounterModel.schema_json(indent=2))
    with open(
        os.path.join(output_dir, "environment-schema.json"), "w"
    ) as f:
        f.write(EnvironmentModel.schema_json(indent=2))
    with open(
        os.path.join(output_dir, "inventory-schema.json"), "w"
    ) as f:
        f.write(InventoryModel.schema_json(indent=2))
    with open(os.path.join(output_dir, "item-schema.json"), "w") as f:
        f.write(ItemModel.schema_json(indent=2))
    with open(os.path.join(output_dir, "monster-schema.json"), "w") as f:
        f.write(MonsterModel.schema_json(indent=2))
    with open(os.path.join(output_dir, "music-schema.json"), "w") as f:
        f.write(MusicModel.schema_json(indent=2))
    with open(os.path.join(output_dir, "npc-schema.json"), "w") as f:
        f.write(NpcModel.schema_json(indent=2))
    with open(os.path.join(output_dir, "sound-schema.json"), "w") as f:
        f.write(SoundModel.schema_json(indent=2))
    with open(
        os.path.join(output_dir, "technique-schema.json"), "w"
    ) as f:
        f.write(TechniqueModel.schema_json(indent=2))


if __name__ == "__main__":
    parser = ArgumentParser()
    # JSON schema is not fit for purpose, as it doesn't support nullable values
    # https://github.com/pydantic/pydantic/issues/1270
    # parser.add_argument(
    #     "-g",
    #     "--generate",
    #     dest="generate",
    #     action="store_true",
    #     default=False,
    #     help="Generate JSON schemas",
    # )
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

    # if args.generate:
    #     write_json_schema(args.output)

    if args.validate:
        db.load(validate=True)
