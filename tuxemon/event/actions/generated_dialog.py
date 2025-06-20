# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2014-2025 William Edwards <shadowapex@gmail.com>, Benjamin Bean <superman2k5@gmail.com>
from __future__ import annotations

import ast
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, cast, final

import requests
import yaml

from tuxemon.constants import paths
from tuxemon.db import DialogueModel, db
from tuxemon.event.eventaction import EventAction
from tuxemon.graphics import get_avatar, string_to_colorlike
from tuxemon.locale import T
from tuxemon.session import Session
from tuxemon.tools import open_dialog

logger = logging.getLogger(__name__)

style_cache: dict[str, DialogueModel] = {}


def load_yaml(filepath: Path) -> Any:
    try:
        with filepath.open() as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Config file not found: {filepath}")
        raise
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        raise exc


CONFIG = load_yaml(paths.mods_folder / "dialogue_config.yaml")
backend = CONFIG["llm"]["backend"]
if backend == "mistral":
    MISTRAL_API_KEY = os.getenv(CONFIG["llm"]["mistral"]["api_key_env"])
else:
    MISTRAL_API_KEY = None


@final
@dataclass
class GeneratedDialogAction(EventAction):
    """
    Open a dialog window using a prompt key passed via `raw_parameters`.
    The key will be used to retrieve a predefined prompt from a YAML config file.
    The prompt text will then be used to generate dialog dynamically via a
    language model.

    Note:
    The YAML config must contain meaningful narrative or character context
    for each prompt key to ensure the model can generate appropriate dialog.
    Script parameters will not be treated as translation keys.

    Script usage:
        .. code-block::

            generated_dialog <prompt>[,avatar][,position][,style]

    Script parameters:
        prompt: Prompt of the dialog.
        avatar: Monster avatar. If it is a number, the monster is the
            corresponding monster slot in the player's party.
            If it is a string, we're referring to a monster by name.
        position: Position of the dialog box. Can be 'top', 'bottom', 'center',
            'topleft', 'topright', 'bottomleft', 'bottomright', 'right', 'left'.
            Default 'bottom'.
        alignment: Alignment of text in the dialog box, it can be 'left', 'center'
            or 'right'. Default 'left'.
        vertical_alignment: Alignment of text in the dialog box, it can be 'bottom',
            'middle' or 'top'. Default 'top'.
        style: a predefined style in db/dialogue/dialogue.json
    """

    name = "generated_dialog"
    prompt: str
    avatar: Optional[str] = None
    position: Optional[str] = None
    alignment: Optional[str] = None
    v_alignment: Optional[str] = None
    style: Optional[str] = None

    def start(self, session: Session) -> None:
        language = T.get_current_language().lower()
        current = T.translate(language)
        name_player = session.player.name.upper()
        prompt = get_prompt(self.prompt)
        key = generate_dialog(prompt, current, name_player)

        avatar_sprite = None
        if self.avatar:
            avatar_sprite = get_avatar(session, self.avatar)

        dialogue = self.style if self.style else "default"
        alignment = self.alignment if self.alignment else "left"
        v_alignment = self.v_alignment if self.v_alignment else "top"
        style = _get_style(dialogue)
        box_style: dict[str, Any] = {
            "bg_color": string_to_colorlike(style.bg_color),
            "font_color": string_to_colorlike(style.font_color),
            "font_shadow": string_to_colorlike(style.font_shadow_color),
            "border": style.border_path,
            "alignment": alignment,
            "v_alignment": v_alignment,
        }
        position = self.position if self.position else "bottom"

        open_dialog(
            client=session.client,
            text=key,
            avatar=avatar_sprite,
            box_style=box_style,
            position=position,
        )

    def update(self, session: Session) -> None:
        try:
            session.client.get_state_by_name("DialogState")
        except ValueError:
            self.stop()


def _get_style(cache_key: str) -> DialogueModel:
    if cache_key in style_cache:
        return style_cache[cache_key]
    else:
        try:
            style = DialogueModel.lookup(cache_key, db)
            style_cache[cache_key] = style
            return style
        except KeyError:
            raise RuntimeError(f"Dialogue {cache_key} not found")


def get_prompt(prompt_key: str) -> str:
    return str(CONFIG["prompts"].get(prompt_key, prompt_key))


def generate_dialog(prompt: str, language: str, player_name: str) -> list[str]:
    backend = CONFIG["llm"]["backend"]

    try:
        if backend == "mistral":
            config = CONFIG["llm"]["mistral"]
            url = config["api_url"]
            headers = {
                "Authorization": f"Bearer {os.getenv(config['api_key_env'])}",
                "Content-Type": "application/json",
            }
            body = {
                "model": config["model"],
                "messages": [
                    {
                        "role": "user",
                        "content": config["template"].format(
                            prompt=prompt,
                            language=language,
                            player_name=player_name,
                        ),
                    }
                ],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"],
            }

        elif backend == "ollama":
            config = CONFIG["llm"]["ollama"]
            url = config["api_url"]
            headers = {"Content-Type": "application/json"}
            body = {
                "model": config["model"],
                "prompt": config["template"].format(
                    prompt=prompt, language=language, player_name=player_name
                ),
                "stream": False,
            }

        elif backend == "openai":
            config = CONFIG["llm"]["openai"]
            headers = {
                "Authorization": f"Bearer {os.getenv(config['api_key_env'])}",
                "Content-Type": "application/json",
            }
            body = {
                "model": config["model"],
                "temperature": config["temperature"],
                "max_tokens": config["max_tokens"],
                "messages": [
                    {
                        "role": "user",
                        "content": config["template"].format(
                            prompt=prompt,
                            language=language,
                            player_name=player_name,
                        ),
                    }
                ],
            }
            response = requests.post(
                config["api_url"], headers=headers, json=body
            )
            response.raise_for_status()
            content = (
                response.json()
                .get("choices", [{}])[0]
                .get("message", {})
                .get("content")
            )

        elif backend == "test":
            config = CONFIG["llm"]["test"]
            content = config["response"].format(
                player_name=player_name,
                language=language,
                prompt=prompt,
            )
            try:
                parsed = ast.literal_eval(content.strip())
                return cast(list[str], parsed)
            except Exception:
                return [content.strip()]

        elif backend == "gemini":
            config = CONFIG["llm"]["gemini"]
            url = config["api_url"]
            api_key = os.getenv(config["api_key_env"])
            headers = {"Content-Type": "application/json"}
            user_prompt = config["template"].format(
                prompt=prompt, language=language, player_name=player_name
            )
            body = {"contents": [{"parts": [{"text": user_prompt}]}]}
            response = requests.post(
                f"{url}?key={api_key}", headers=headers, json=body
            )
            response.raise_for_status()
            content = (
                response.json()
                .get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

        else:
            raise ValueError(f"Unsupported LLM backend: {backend}")

        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        content = (
            response.json()
            .get("choices", [{}])[0]
            .get("message", {})
            .get("content")
            if backend == "mistral"
            else response.json().get("response", "")
        )

        parsed = ast.literal_eval(content.strip())
        if not isinstance(parsed, list) or not all(
            isinstance(line, str) for line in parsed
        ):
            raise ValueError("Generated output is not a list of strings.")
        return cast(list[str], parsed)

    except Exception as e:
        logger.error(e)
        return ["[ERROR] Failed to generate dialog lines."]
