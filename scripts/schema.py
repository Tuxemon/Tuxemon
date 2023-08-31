#!/usr/bin/python

import os
from argparse import ArgumentParser
from tuxemon.db import (
    db,
    EconomyModel,
    EncounterModel,
    EnvironmentModel,
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
        f.write(EconomyModel.model_json_schema(indent=2))
    with open(
        os.path.join(output_dir, "encounter-schema.json"), "w"
    ) as f:
        f.write(EncounterModel.model_json_schema(indent=2))
    with open(
        os.path.join(output_dir, "environment-schema.json"), "w"
    ) as f:
        f.write(EnvironmentModel.model_json_schema(indent=2))
    with open(os.path.join(output_dir, "item-schema.json"), "w") as f:
        f.write(ItemModel.model_json_schema(indent=2))
    with open(os.path.join(output_dir, "monster-schema.json"), "w") as f:
        f.write(MonsterModel.model_json_schema(indent=2))
    with open(os.path.join(output_dir, "music-schema.json"), "w") as f:
        f.write(MusicModel.model_json_schema(indent=2))
    with open(os.path.join(output_dir, "npc-schema.json"), "w") as f:
        f.write(NpcModel.model_json_schema(indent=2))
    with open(os.path.join(output_dir, "sound-schema.json"), "w") as f:
        f.write(SoundModel.model_json_schema(indent=2))
    with open(
        os.path.join(output_dir, "technique-schema.json"), "w"
    ) as f:
        f.write(TechniqueModel.model_json_schema(indent=2))


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
