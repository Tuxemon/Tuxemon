# Tuxemon CLI API

The CLI interface is a convenient way to debug and develop maps.  
When enabled, the game exposes a local HTTP API that allows you to run commands while the game is running.  
You can give yourself items, add monsters to your party, change game variables, inspect time data, or run any action or condition available in map scripts.  
A live dashboard is also available for real‑time inspection of the game state.

## Setting up

Enable the CLI API by setting `cli_enabled` to `True` in the `tuxemon.yaml` file:

```
[game]
cli_enabled = True
```

When enabled, the game starts a local API server at:

```
http://127.0.0.1:8000
```

The server exposes REST endpoints, a WebSocket stream, and a browser dashboard.

---

## Endpoints

### Command Endpoints

#### `GET /help`  
Lists all available commands.

#### `POST /run`  
Executes a command.

Body:

```
{
  "line": "<command>"
}
```

---

### Debug Endpoints

#### `POST /test`  
Parses and evaluates a condition expression.

#### `GET /session/vars/print`  
Prints one or more game variables.  
Accepts multiple variables separated by `:`.

Examples:

```
/session/vars/print?variables=foo
/session/vars/print?variables=foo:bar:baz
/session/vars/print
```

---

### Session Endpoints

#### `GET /session/player`  
Returns player identity, map, tile position, money, and party size.

#### `GET /session/party`  
Returns the player’s party with stats and moves.

#### `GET /session/snapshot`  
Returns the current in‑game time snapshot (hour, date, season, stage of day).

---

## Live Data

The API provides a real‑time WebSocket feed for monitoring the game state.

### `WS /live/session`

Streams:

- Player name  
- Current map  
- Tile position  
- Money  
- Party size  
- Time snapshot  

Updates once per second.

Example message:

```json
{
  "player": {
    "name": "Player",
    "map": "overworld",
    "tile_pos": [10, 14],
    "money": 120,
    "party_size": 3
  },
  "time": {
    "hour": 14,
    "day": 10,
    "month": 4,
    "year": 2026,
    "season": "spring",
    "stage_of_day": "day"
  }
}
```

---

## Dashboard

A built‑in dashboard is available for visualizing live data in the browser.

### `GET /dashboard`

Serves an HTML page that connects to the WebSocket feed and displays:

- Player information  
- Map  
- Tile position  
- Money  
- Party size  
- Time snapshot  

Open it in your browser:

```
http://127.0.0.1:8000/dashboard
```

The dashboard updates automatically as the game runs.

---

## Commands

The command syntax is identical to the previous terminal‑based CLI.

Examples:

- `help`  
- `action <action_name> [params]`  
- `test <condition_name> [params]`  
- `random_encounter`  
- `trainer_battle <npc_slug>`  
- `quit`  
- `whereami`  

---

## Using the API

Open the API documentation:

```
http://127.0.0.1:8000
```

Run commands:

```
POST /run
{
  "line": "action random_monster 11"
}
```

Test a condition:

```
POST /run
{
  "line": "test has_item player,potion"
}
```

Start a wild encounter:

```
POST /run
{
  "line": "random_encounter"
}
```

---

## Notes

The CLI API is intended for use while the game is running on the world map.  
Errors may be minimal.  
Refer to the scripting reference for available actions and conditions:

https://tuxemon.readthedocs.io/en/latest/handcrafted/scripting.html
