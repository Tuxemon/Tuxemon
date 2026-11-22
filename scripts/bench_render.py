#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure drawn frames per second.")
    parser.add_argument("--resolution", default="1280x720")
    parser.add_argument("--upscaler", choices=("cpu", "gpu"), default="cpu")
    parser.add_argument("--render-scale", type=int, default=None)
    parser.add_argument("--map", default="cotton_town.tmx")
    parser.add_argument(
        "--position", type=int, nargs=2, default=(10, 17), metavar=("X", "Y")
    )
    parser.add_argument("--warmup", type=float, default=6.0)
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument(
        "--screenshot",
        default=None,
        help="save the last frame the game drew (before any GPU stretch)",
    )
    parser.add_argument(
        "--window-capture",
        default=None,
        help="grab the window as shown on screen (needs Pillow, Windows/macOS)",
    )
    return parser.parse_args()


def capture_window(path: str) -> None:
    import warnings

    from PIL import ImageGrab
    from pygame._sdl2.video import Window

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        window = Window.from_display_module()
    x, y = window.position
    w, h = window.size
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(path)


def main() -> None:
    args = parse_args()
    width, height = (int(v) for v in args.resolution.lower().split("x"))

    from tuxemon.platform import platform

    platform.init()

    from tuxemon.user_config import CONFIG

    display = CONFIG.config_model.display
    display.resolution_x = width
    display.resolution_y = height
    display.vsync = False
    display.splash = False
    display.fullscreen = False
    display.fps = 60.0
    if hasattr(display, "upscaler"):
        display.upscaler = args.upscaler
        if args.render_scale is not None:
            display.gpu_render_scale = args.render_scale
    elif args.upscaler != "cpu":
        sys.exit("This branch has no GPU upscaler option yet.")

    from tuxemon.prepare import pygame_init

    context = pygame_init()

    import pygame

    from tuxemon import main as tuxemon_main
    from tuxemon.database.runtime import db
    from tuxemon.launcher import GameLauncher
    from tuxemon.session import local_session

    def start_new_game(client, config, load_slot=None) -> None:
        meta = db.mod_metadata.get_mod_metadata(config.mods[0])
        meta = meta.model_copy(
            update={
                "starting_map": args.map,
                "starting_position": list(args.position),
            }
        )
        client.push_state("BackgroundState")
        GameLauncher(client).launch(
            session=local_session, meta=meta, remove_states=[]
        )

    tuxemon_main.configure_game_states = start_new_game

    real_update = pygame.display.update
    started = time.perf_counter()
    window: dict[str, float] = {"frames": 0, "begin": 0.0}
    result: dict[str, float] = {}

    def counting_update(*a, **kw):
        real_update(*a, **kw)
        now = time.perf_counter() - started
        if now < args.warmup:
            return
        if not window["begin"]:
            window["begin"] = now
        window["frames"] += 1
        elapsed = now - window["begin"]
        if elapsed >= args.seconds and not result:
            result["fps"] = window["frames"] / elapsed
            if args.screenshot:
                pygame.image.save(pygame.display.get_surface(), args.screenshot)
            if args.window_capture:
                capture_window(args.window_capture)
            local_session.client.quit()

    pygame.display.update = counting_update

    config = CONFIG.copy()
    tuxemon_main.main(config=config, context=context)

    mode = args.upscaler
    if mode == "gpu":
        mode += f" (render scale {context.scale})"
    internal = "x".join(str(v) for v in context.resolution)
    print(
        f"window {width}x{height} | {mode} | internal {internal} | "
        f"{result.get('fps', 0):.1f} FPS"
    )


if __name__ == "__main__":
    main()
