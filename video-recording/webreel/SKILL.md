---
name: webreel
description: WebReel CLI reference — config format, step types, human-like recording patterns, and troubleshooting. webreel is pre-installed globally in the sandbox.
allowed-tools: Bash(*)
metadata:
  author: Twill
  version: "1.0"
---

# webreel

webreel is a CLI for recording scripted browser demonstrations as MP4, GIF, or WebM files. It drives a headless Chrome instance, captures frames at ~60fps, and encodes them with ffmpeg. Cursor animation, keystroke HUD overlays, and sound effects are built in.

## IMPORTANT: Sandbox installation

`webreel` is **pre-installed globally** in this sandbox (custom build with bug fixes).

- Do **NOT** run `npm install webreel`, `npx webreel`, or any other installation command.
- Use the `webreel` CLI directly: `webreel record`, `webreel preview`, `webreel validate`.
- Chrome and ffmpeg are also pre-installed. Do NOT run `webreel install`.

## Commands

| Command                      | Description                              |
| ---------------------------- | ---------------------------------------- |
| `webreel record [videos...]` | Record video(s) from config              |
| `webreel preview [video]`    | Run in visible browser without recording |
| `webreel validate`           | Check config for errors                  |
| `webreel record --verbose`   | Log each step as it executes             |
| `webreel record --dry-run`   | Print resolved config without recording  |

---

# Configuration

Videos are defined in a `webreel.config.json` file:

```json
{
  "$schema": "https://webreel.dev/schema/v1.json",
  "viewport": { "width": 1920, "height": 1080 },
  "clickDwell": 500,
  "videos": {
    "demo": {
      "url": "http://localhost:3000",
      "output": "demo.mp4",
      "zoom": 2,
      "waitFor": ".loaded",
      "steps": [...]
    }
  }
}
```

### Top-level fields

| Field        | Type                | Description                                                 |
| ------------ | ------------------- | ----------------------------------------------------------- |
| `$schema`    | string              | Schema URL for IDE autocompletion                           |
| `viewport`   | `{ width, height }` | Default viewport dimensions                                 |
| `clickDwell` | number              | **Set to 500.** Milliseconds cursor holds before each click |
| `theme`      | object              | Cursor and HUD customization                                |
| `videos`     | object              | Map of video name → video config (required)                 |

### Per-video fields

| Field      | Type   | Description                                                      |
| ---------- | ------ | ---------------------------------------------------------------- |
| `url`      | string | Target URL (absolute or relative to baseUrl)                     |
| `output`   | string | Output filename (extension determines format: .mp4, .gif, .webm) |
| `viewport` | object | Override viewport for this video                                 |
| `zoom`     | number | CSS zoom level (e.g., 2 for 2x)                                  |
| `waitFor`  | string | CSS selector to wait for before starting steps                   |
| `steps`    | array  | Array of step objects (required)                                 |

---

# Element targeting

Several steps target DOM elements. Use ONE of:

| Field      | Description                                                 |
| ---------- | ----------------------------------------------------------- |
| `text`     | Match by visible text content                               |
| `selector` | Match by CSS selector                                       |
| `within`   | (optional) CSS selector to scope search to a parent element |

Use `text` OR `selector`, not both. `within` is always optional.

---

# Step types reference

Every step requires an `action` field. Optional common fields:

- `description` (string) — human-readable note (not used at runtime, but useful for pause timing comments)

**Do NOT use `delay` or `defaultDelay`** — see config patterns below.

## pause

Wait for a fixed duration. **Use 5x multiplier** (see config patterns).

| Field | Type   | Required |
| ----- | ------ | -------- |
| `ms`  | number | yes      |

```json
{ "action": "pause", "ms": 5000, "description": "~1s on screen" }
```

## click

Click a DOM element. **MUST be preceded by moveTo + pause** (see config patterns).

| Field       | Type     | Required |
| ----------- | -------- | -------- |
| `text`      | string   | no       |
| `selector`  | string   | no       |
| `within`    | string   | no       |
| `modifiers` | string[] | no       |

Provide `text` or `selector` (at least one).

```json
{ "action": "click", "text": "Submit" }
{ "action": "click", "selector": "#save-btn" }
{ "action": "click", "text": "Item 3", "modifiers": ["shift"] }
{ "action": "click", "text": "Delete", "within": ".modal" }
```

## type

Type text into an input. **Set charDelay: 120 or higher.**

| Field       | Type   | Required                        |
| ----------- | ------ | ------------------------------- |
| `text`      | string | yes                             |
| `selector`  | string | no                              |
| `within`    | string | no                              |
| `charDelay` | number | no (but **always set to 120+**) |

```json
{
  "action": "type",
  "text": "user@example.com",
  "selector": "#email",
  "charDelay": 120
}
```

## key

Press a keyboard shortcut.

| Field    | Type                    | Required |
| -------- | ----------------------- | -------- |
| `key`    | string                  | yes      |
| `target` | string or ElementTarget | no       |

Key combo syntax: `"cmd+s"`, `"ctrl+shift+p"`, `"Enter"`, `"Escape"`, `"ArrowDown"`.

```json
{ "action": "key", "key": "cmd+s" }
{ "action": "key", "key": "Enter" }
```

## moveTo

Move cursor to an element without clicking. **Use before every click.**

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| `text`     | string | no       |
| `selector` | string | no       |
| `within`   | string | no       |

```json
{ "action": "moveTo", "text": "Settings" }
{ "action": "moveTo", "selector": "#submit-btn" }
```

## hover

Hover over an element (triggers CSS :hover and mouseenter).

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| `text`     | string | no       |
| `selector` | string | no       |
| `within`   | string | no       |

```json
{ "action": "hover", "selector": ".tooltip-trigger" }
```

## scroll

Scroll the page or a specific element.

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| `x`        | number | no       |
| `y`        | number | no       |
| `text`     | string | no       |
| `selector` | string | no       |
| `within`   | string | no       |

```json
{ "action": "scroll", "y": 400 }
{ "action": "scroll", "y": 300, "selector": ".scrollable-panel" }
```

## wait

Wait for an element to appear in the DOM.

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| `selector` | string | no       |
| `text`     | string | no       |
| `within`   | string | no       |
| `timeout`  | number | no       |

```json
{ "action": "wait", "selector": ".results-loaded", "timeout": 5000 }
{ "action": "wait", "text": "Success" }
```

## navigate

Navigate to a new URL.

| Field | Type   | Required |
| ----- | ------ | -------- |
| `url` | string | yes      |

```json
{ "action": "navigate", "url": "/settings" }
```

## drag

Drag from one element to another.

| Field  | Type          | Required |
| ------ | ------------- | -------- |
| `from` | ElementTarget | yes      |
| `to`   | ElementTarget | yes      |

```json
{
  "action": "drag",
  "from": { "text": "Task A", "within": ".column-todo" },
  "to": { "selector": ".card-list", "within": ".column-done" }
}
```

## select

Select a value in a `<select>` dropdown.

| Field      | Type   | Required |
| ---------- | ------ | -------- |
| `selector` | string | no       |
| `text`     | string | no       |
| `within`   | string | no       |
| `value`    | string | yes      |

```json
{ "action": "select", "selector": "#country", "value": "us" }
```

## screenshot

Capture a PNG screenshot.

| Field    | Type   | Required |
| -------- | ------ | -------- |
| `output` | string | yes      |

```json
{ "action": "screenshot", "output": "screenshots/final-state.png" }
```

---

# Config patterns (REQUIRED)

**You MUST follow ALL rules below when building a WebReel config. Configs that violate these rules produce unwatchable robot-like videos. Validate your config against every rule before recording.**

## Pre-flight checklist

Before running `webreel record`, verify your config passes ALL of these checks:

- [ ] Every `click` step is preceded by a `moveTo` to the same target (NO bare clicks)
- [ ] Every `moveTo` is followed by a `pause` (2500–4000ms) before the action
- [ ] Every action is followed by a `pause` (5000–12000ms) so viewers see the result
- [ ] All pause `ms` values use the 5x multiplier (intended screen time × 5)
- [ ] `clickDwell: 500` is set at the video level
- [ ] All `type` steps have `charDelay: 120` or higher
- [ ] No `delay` fields or `defaultDelay` — only explicit `pause` steps

## NEVER use a bare click

**NEVER write a `click` step without a `moveTo` + `pause` before it.** This is the #1 mistake. Without `moveTo`, the cursor teleports instantly to the target — viewers cannot follow what is happening.

BAD (cursor teleports):

```json
{ "action": "click", "text": "Filters" }
```

GOOD (cursor travels, dwells, then clicks):

```json
{ "action": "moveTo", "text": "Filters" },
{ "action": "pause", "ms": 3000, "description": "Cursor dwells (~0.6s)" },
{ "action": "click", "text": "Filters" }
```

This pattern applies to EVERY click in the config, no exceptions.

## Step cadence (required for every interaction)

Every user-visible interaction MUST follow this cadence:

1. **moveTo** the target — cursor visibly travels
2. **pause** 2500–4000ms — cursor dwells, viewer reads the target
3. **click / type / key** — the action
4. **pause** 5000–12000ms — viewer sees the result

## Pause compression (5x rule)

WebReel compresses idle time by ~5x. A `{ "action": "pause", "ms": 5000 }` produces ~1 second of video.

**Rule:** Multiply intended screen time by 5 for the `ms` value. Add a `description` noting the intended time:

```json
{
  "action": "pause",
  "ms": 10000,
  "description": "Show results (~2s on screen)"
}
```

Interactive steps (click, type, scroll, hover, moveTo) are captured at ~1:1 real-time. Only `pause` is compressed.

## No `delay` or `defaultDelay`

The `delay` field and `defaultDelay` are subject to the same compression and do NOT reliably add screen time. Use explicit `{ "action": "pause" }` steps instead.

## Typing must be readable

Set `charDelay: 120` (or higher) on every `type` step. The default is too fast.

## clickDwell at video level

Set `"clickDwell": 500` at the video level. This adds a brief cursor hold before each click.

---

# Examples

All examples follow the required config patterns (moveTo + pause before clicks, 5x pause multiplier, charDelay, clickDwell).

## Form filling

```json
{
  "$schema": "https://webreel.dev/schema/v1.json",
  "clickDwell": 500,
  "videos": {
    "form-filling": {
      "url": "http://localhost:3000/login",
      "viewport": { "width": 1920, "height": 1080 },
      "zoom": 2,
      "waitFor": "#email",
      "steps": [
        { "action": "pause", "ms": 5000, "description": "Show form (~1s)" },
        {
          "action": "type",
          "text": "user@example.com",
          "selector": "#email",
          "charDelay": 120
        },
        {
          "action": "type",
          "text": "supersecret123",
          "selector": "#password",
          "charDelay": 120
        },
        { "action": "pause", "ms": 3000, "description": "Pause before submit" },
        { "action": "moveTo", "text": "Sign In" },
        {
          "action": "pause",
          "ms": 3000,
          "description": "Cursor dwells (~0.6s)"
        },
        { "action": "click", "text": "Sign In" },
        { "action": "pause", "ms": 10000, "description": "Show result (~2s)" }
      ]
    }
  }
}
```

## Page navigation with scroll

```json
{
  "$schema": "https://webreel.dev/schema/v1.json",
  "clickDwell": 500,
  "videos": {
    "browse-features": {
      "url": "http://localhost:3000",
      "viewport": { "width": 1920, "height": 1080 },
      "zoom": 2,
      "waitFor": ".hero",
      "steps": [
        { "action": "pause", "ms": 5000, "description": "Show hero (~1s)" },
        { "action": "scroll", "y": 400 },
        { "action": "pause", "ms": 5000, "description": "Show features (~1s)" },
        { "action": "moveTo", "text": "Learn More" },
        { "action": "pause", "ms": 3000 },
        { "action": "click", "text": "Learn More" },
        { "action": "wait", "text": "Documentation", "timeout": 5000 },
        {
          "action": "pause",
          "ms": 10000,
          "description": "Show docs page (~2s)"
        }
      ]
    }
  }
}
```

## Keyboard shortcuts

```json
{
  "$schema": "https://webreel.dev/schema/v1.json",
  "clickDwell": 500,
  "videos": {
    "keyboard-shortcuts": {
      "url": "http://localhost:3000/editor",
      "viewport": { "width": 1920, "height": 1080 },
      "zoom": 2,
      "waitFor": ".editor",
      "steps": [
        { "action": "pause", "ms": 5000, "description": "Show editor (~1s)" },
        { "action": "moveTo", "selector": ".editor" },
        { "action": "pause", "ms": 3000 },
        { "action": "click", "selector": ".editor" },
        { "action": "key", "key": "cmd+a" },
        { "action": "pause", "ms": 3000 },
        { "action": "key", "key": "cmd+b" },
        {
          "action": "pause",
          "ms": 5000,
          "description": "Show bold text (~1s)"
        },
        { "action": "key", "key": "cmd+s" },
        { "action": "pause", "ms": 5000, "description": "Show saved (~1s)" }
      ]
    }
  }
}
```

---

# Troubleshooting

**NEVER fall back to agent-browser's built-in recording.** WebReel produces far better videos with cursor animation and compositing. When webreel fails, debug it — don't switch tools.

## Debug systematically

1. **Determine if the issue is step execution or frame capture.** If steps run but you get ENOENT on the temp mp4 rename, that means 0 frames were captured — the problem is Chrome or ffmpeg, not your config.

2. **Check ffmpeg availability.** WebReel looks for ffmpeg at `~/.webreel/bin/ffmpeg/ffmpeg`. If missing, symlink the system one:

   ```bash
   mkdir -p ~/.webreel/bin/ffmpeg && ln -sf /usr/bin/ffmpeg ~/.webreel/bin/ffmpeg/ffmpeg
   ```

3. **Check Chrome flags.** In webreel 0.1.4 with Chrome 146+, the `--enable-begin-frame-control` flag in `@webreel/core/dist/chrome.js` causes `Page.captureScreenshot` to hang indefinitely (webreel never calls `HeadlessExperimental.beginFrame`). Fix:

   ```bash
   CHROME_JS=$(find /opt/webreel -name "chrome.js" -path "*/core/*" 2>/dev/null | head -1)
   if [ -n "$CHROME_JS" ]; then
     sed -i 's/--enable-begin-frame-control//g; s/--run-all-compositor-stages-before-draw//g' "$CHROME_JS"
   fi
   ```

4. **Add debug logging.** If the capture loop hangs, add logging to `recorder.js` to see where it gets stuck: before `timeline.tick()`, before `captureScreenshot`, after `captureScreenshot`. Check `frameCount` in `stop()`.

## Common failures and fixes

- **Text matching failures / "Element not found"**: May not be real — if Chrome can't render frames, the page appears empty to webreel's element finder. Fix the rendering/frame capture issue first (steps 1–4 above).
- **Sheet/modal not appearing after click**: Check if the click actually fired. Use a minimal 2-step config to isolate. Once frame capture works, interactive elements usually work too.
- **Navigation waits**: Use `{ "action": "wait", "text": "SomeUniqueText" }` to wait for the destination page to load after clicking a link.
- **Selector not found**: Re-validate the selector with agent-browser. The DOM may have changed between testing and recording.
- **Wrong URL**: Check `$TWILL_ENTRYPOINT_LOG_DIR/url-mapping.txt` for the correct URL.
