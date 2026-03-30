---
name: computer-use-cli
description: Automate and test Linux desktop apps (Electron, Tauri, React Native Desktop) in an X11 session using CLI commands for screenshot + mouse + keyboard. Includes coordinate scaling so you can click/type based on a smaller “API-sized” screenshot.
compatibility: Requires Linux with X11 ($DISPLAY) plus xdotool + scrot + ImageMagick. Best in containers with Xvfb + a lightweight window manager.
allowed-tools: Bash(*)
metadata:
  author: Twill
  version: "1.0"
---

# Computer Use (CLI)

Use this skill to **drive and validate a Linux GUI** from the command line:

- **Take screenshots** to observe the current UI state
- **Click / type / scroll / drag** to exercise flows
- **Smoke-test desktop apps** (Electron / Tauri / React Native Desktop) inside a sandboxed X11 session

It’s most useful when you need GUI automation but only have shell access (no native UI automation framework available).

## Quick start

1. Ensure dependencies are installed (see “Dependencies”).
2. Point the commands at the active display (usually already set):
   - `export DISPLAY=:1` (or whatever your container uses)
3. Take a screenshot to establish the agent’s visual state:
   - `cu-screenshot --base64`
4. Perform actions in **API coordinate space** (the resized screenshot), then screenshot again:
   - `cu-click --x 512 --y 384 --base64`
   - `cu-type --text "hello" --base64`

Tip: start the app under the same display, for example:

```bash
(DISPLAY=:1 ./my-electron-app &) && sleep 2
cu-screenshot --base64
```

## Coordinate spaces (critical)

These commands support two coordinate spaces:

- **API space (default)**: coordinates refer to the **resized** screenshot (e.g. XGA 1024×768). This keeps vision tokens lower and matches “computer use” style interactions.
- **Screen space**: coordinates refer to the **real** display resolution.

By default, if scaling is enabled, inputs are treated as **API space** and are scaled up before calling `xdotool`.

Use:

- `--space api` (default) or `--space screen`
- `cu-info` to see screen size, chosen API size, and scale factors.

## Standard interaction loop (recommended)

Use this loop to keep actions grounded:

1. `cu-screenshot --base64` (observe)
2. Decide next action(s)
3. Run **one** action command (or a short chain) and **always** capture a new screenshot:
   - click/move/type/scroll/drag → screenshot
4. Repeat until done

## Commands

All commands print a single JSON object to stdout. Most accept:

- `--display :N` (defaults to `$DISPLAY` if set)
- `--base64` to include `screenshot_base64_png` (can be large)
- `--out PATH` for screenshot output (default: `$TWILL_SCREENSHOTS_DIR/...png`)
- `--no-screenshot` to skip the post-action screenshot (use sparingly)

### `scripts/cu-info`

Prints JSON describing the detected screen size, chosen API size, and scale factors.

### `scripts/cu-screenshot`

Takes a screenshot (optionally scaled down to a target like XGA). Use `--base64` when your agent needs the image content inline.

### `scripts/cu-move --x INT --y INT`

Moves the mouse pointer.

### `scripts/cu-click --x INT --y INT`

Left-click at a coordinate. Use `--button right|middle|left` or `scripts/cu-right-click`.

### `scripts/cu-double-click`, `scripts/cu-right-click`, `scripts/cu-middle-click`

Click variants.

### `scripts/cu-drag --x0 INT --y0 INT --x1 INT --y1 INT`

Drag from start to end coordinate.

### `scripts/cu-type --text STRING`

Types text using `xdotool type` with a small delay.

### `scripts/cu-key --keys STRING`

Sends a key chord (e.g. `ctrl+l`, `Return`, `Alt+F4`) via `xdotool key --`.

### `scripts/cu-scroll --dir up|down|left|right --amount INT [--x INT --y INT]`

Scrolls by repeated scroll wheel clicks (4/5/6/7). Optionally moves to a coordinate first.

### `scripts/cu-wait --seconds FLOAT`

Sleeps then returns a screenshot.

### `scripts/cu-cursor`

Returns current cursor position (in **API space** if scaling is enabled).

### `scripts/cu-zoom --x0 INT --y0 INT --x1 INT --y1 INT`

Returns a cropped screenshot of the region (like a “zoom” tool).

## Dependencies

Install these in your Ubuntu image:

```bash
apt-get update && apt-get install -y --no-install-recommends \
  xdotool \
  scrot \
  imagemagick \
  x11-utils \
  && rm -rf /var/lib/apt/lists/*
```

If you run a headless desktop in-container, you typically also need:

```bash
apt-get update && apt-get install -y --no-install-recommends \
  xvfb \
  mutter \
  x11vnc \
  && rm -rf /var/lib/apt/lists/*
```

## Notes and pitfalls

- Prefer a maximum screenshot size like **XGA (1024×768)** to reduce image tokens; scaling is automatic when the screen is larger and has a similar aspect ratio.
- If your window manager is missing, GUI apps may not render or focus correctly even though X11 is running.
- If actions seem “offset”, confirm the agent is using **API space** coordinates from the most recent screenshot and that scaling is enabled.
