# Tuxemon CLI Interface

This document describes the in‑game command‑line interface used for debugging, development, and direct game manipulation.

---

## Overview

The CLI interface allows direct execution of actions, conditions, and debugging commands while the game is running.  
It can modify game state, spawn items or monsters, and inspect map data.

Any action or condition available in map scripts is also available in the CLI.

---

## Enabling the CLI

Enable the CLI by setting `cli_enabled = True` in `tuxemon.yaml`:

```
[game]
cli_enabled = True
```

---

## Commands

| Command | Description |
|--------|-------------|
| `help [command_name]` | Lists all commands or details for a specific command |
| `action <action_name> [params]` | Executes an EventAction (same syntax as map scripts) |
| `test <condition_name> [params]` | Tests an EventCondition |
| `random_encounter` | Starts a wild tuxemon battle |
| `trainer_battle <npc_slug>` | Starts a trainer battle |
| `quit` | Quits the game |
| `whereami` | Prints the current map filename |
| `shell` | Opens a Python shell for advanced manipulation |

---

## Examples

### List all commands

```
> help
Available Options
=================
action  help  quit  random_encounter  shell  test  trainer_battle  whereami

Enter 'help [command]' for more info.
```

### Get help for a specific action

```
> help action teleport

    Teleport the player to a particular map and tile coordinates.

    Script usage:
        .. code-block::

            teleport <map_name>,<x>,<y>

    Script parameters:
        map_name: Name of the map to teleport to.
        x: X coordinate of the map to teleport to.
        y: Y coordinate of the map to teleport to.
```

### Test a condition and give an item

```
> test has_item player,potion
False
> action add_item potion,1
> test has_item player,potion
True
```

---

## Notes

The CLI interface is new and error messages may be limited.  
Use commands while the game is running and the player is on the world map.

For a full list of actions and conditions, see the scripting reference:

[https://tuxemon.readthedocs.io/en/latest/handcrafted/scripting.html](https://tuxemon.readthedocs.io/en/latest/handcrafted/scripting.html)
