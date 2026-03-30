# Computer Use (CLI)

This skill packages a Linux desktop automation toolkit for agents that only have shell access.

It is useful for:

- smoke-testing Electron, Tauri, and other desktop apps
- interacting with GUI apps inside X11 containers
- taking screenshots, clicking, typing, scrolling, and dragging from the command line
- working in a reduced "API coordinate space" so screenshots and coordinates stay manageable

## Files

- `SKILL.md`: agent-facing usage guide
- `scripts/cu.py`: Python implementation for screenshot and input commands
- `scripts/cu-*`: shell wrappers for common actions

## Linux and X11 dependencies

Install the core packages first:

```bash
apt-get update && apt-get install -y --no-install-recommends \
  xdotool \
  scrot \
  imagemagick \
  x11-utils \
  && rm -rf /var/lib/apt/lists/*
```

If you are running a headless desktop inside a container, you will usually also want:

```bash
apt-get update && apt-get install -y --no-install-recommends \
  xvfb \
  mutter \
  x11vnc \
  && rm -rf /var/lib/apt/lists/*
```

You also need an active X11 display, for example:

```bash
export DISPLAY=:1
```

## Quick start

Launch your desktop app under the same display:

```bash
(DISPLAY=:1 ./my-electron-app &) && sleep 2
```

Inspect the screen:

```bash
scripts/cu-screenshot --base64
scripts/cu-info
```

Click and type using API-space coordinates:

```bash
scripts/cu-click --x 512 --y 384 --base64
scripts/cu-type --text "hello world" --base64
```

## Coordinate spaces

The toolkit supports two coordinate spaces:

- `api`: coordinates refer to the resized screenshot returned to the agent
- `screen`: coordinates refer to the real display resolution

By default, the wrappers use API-space coordinates and scale them up before calling `xdotool`.

That makes it easier to reason about screenshots while keeping image sizes smaller.

## Common wrappers

- `scripts/cu-screenshot`
- `scripts/cu-click`
- `scripts/cu-double-click`
- `scripts/cu-right-click`
- `scripts/cu-drag`
- `scripts/cu-type`
- `scripts/cu-key`
- `scripts/cu-scroll`
- `scripts/cu-wait`
- `scripts/cu-cursor`
- `scripts/cu-zoom`

Each command prints JSON so it can be consumed reliably by an agent or outer tool.

## Recommended interaction loop

1. Capture a screenshot.
2. Decide one action.
3. Run that action.
4. Capture the next screenshot.
5. Repeat until the workflow is complete.

This keeps clicks and typing grounded in the latest visual state.

## Notes

- If interactions look offset, verify you are using coordinates from the newest screenshot.
- If the app renders incorrectly, make sure a window manager is running.
- If screen detection fails, install `x11-utils` or provide `WIDTH` and `HEIGHT`.
