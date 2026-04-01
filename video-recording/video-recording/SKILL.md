---
name: video-recording
description: "Record high-quality browser verification videos using WebReel. Two-phase workflow: test with agent-browser to collect CSS selectors, then record with WebReel for polished output."
compatibility: Requires agent-browser and webreel.
allowed-tools: Bash(*)
metadata:
  author: Twill
  version: "3.0"
---

# Video Recording (WebReel)

Record polished browser verification videos using a **two-phase workflow**:

1. **Phase 1 — Test & collect selectors** (agent-browser): Run your scenario interactively, validate every element, and collect CSS selectors.
2. **Phase 2 — Record** (WebReel): Build a config from your selectors, then render a scripted video with smooth cursor, timing, and encoding.

For WebReel config format, step types, config patterns, and troubleshooting, load the `webreel` skill. **You MUST follow the config patterns defined in the `webreel` skill** — especially moveTo before every click, pause 5x multiplier, charDelay 120+, and clickDwell 500.

---

## Phase 1: Test & Collect Selectors (agent-browser)

Before recording, you MUST run the full verification scenario with agent-browser and collect CSS selectors for every element you will interact with in the video.

### 1. Navigate and test

```bash
agent-browser open http://localhost:3000
agent-browser click @e1
agent-browser wait 500
agent-browser scroll down 300
```

### 2. Discover CSS selectors for each interactive element

For every element you click, type into, hover, or scroll, find a stable CSS selector:

```bash
agent-browser eval "JSON.stringify((() => { const el = document.querySelector('[data-testid=submit-btn]'); return el ? {tag: el.tagName, text: el.textContent?.trim()} : null })())"
```

**Selector priority** (most stable → least stable):

1. `[data-testid="..."]` — test IDs are the most reliable
2. `[role="..."] + text` — ARIA roles with text matching
3. Semantic HTML — `button`, `a[href="..."]`, `input[name="..."]`
4. Stable classes — `.nav-item`, `.submit-button` (avoid generated hashes like `.css-1a2b3c`)
5. Scoped selectors with `within` — for repeated components

### 3. Track selectors as you go

Keep a running list of selectors as you test. Example:

```
- Login button:     button[data-testid="login-btn"]
- Email input:      input[name="email"]
- Password input:   input[name="password"]
- Submit:           form .submit-button
- Dashboard nav:    nav a[href="/dashboard"]
```

### 4. Validate selectors

Before moving to Phase 2, verify each selector resolves:

```bash
agent-browser eval "document.querySelector('button[data-testid=login-btn]')?.tagName ?? 'NOT FOUND'"
```

---

## Phase 2: Record with WebReel

Once your test passes and you have all selectors, build a WebReel config and record.

### 1. Build config

**IMPORTANT:** Load the `webreel` skill and follow its config patterns. You MUST use moveTo before every click, 5x pause multiplier, charDelay 120+, and clickDwell 500. Configs that skip these produce unwatchable videos.

```bash
scripts/twill-video-build-config '{
  "url": "http://localhost:3000",
  "output": "verification.mp4",
  "viewport": { "width": 1920, "height": 1080 },
  "clickDwell": 500,
  "steps": [
    { "action": "pause", "ms": 5000, "description": "Initial view (~1s on screen)" },
    { "action": "moveTo", "selector": "button[data-testid=login-btn]" },
    { "action": "pause", "ms": 3000, "description": "Cursor dwells (~0.6s)" },
    { "action": "click", "selector": "button[data-testid=login-btn]" },
    { "action": "pause", "ms": 5000, "description": "Show form (~1s)" },
    { "action": "type", "text": "user@example.com", "selector": "input[name=email]", "charDelay": 120 },
    { "action": "type", "text": "password123", "selector": "input[name=password]", "charDelay": 120 },
    { "action": "moveTo", "selector": "form .submit-button" },
    { "action": "pause", "ms": 3000 },
    { "action": "click", "selector": "form .submit-button" },
    { "action": "wait", "selector": "nav a[href=\"/dashboard\"]", "timeout": 5000 },
    { "action": "pause", "ms": 10000, "description": "Show dashboard (~2s on screen)" }
  ]
}'
```

### 2. Preview (optional)

```bash
webreel preview
```

### 3. Record

```bash
scripts/twill-video-record webreel.config.json $TWILL_SCREENSHOTS_DIR
```

This runs `webreel record`, copies the output to `$TWILL_SCREENSHOTS_DIR`, and prints the final path as JSON.

### 4. Upload and share

## NEVER record a video without sharing it

**If you record a video, you MUST upload it AND include it in your final answer. No exceptions.** A video that is recorded but not shared is wasted work — the user never sees it, integrations never receive it, and the recording was pointless.

### Upload

```bash
curl -s -X POST -H "Authorization: Bearer $TWILL_API_KEY" \
  -F "file=@$TWILL_SCREENSHOTS_DIR/verification.mp4" \
  "$TWILL_SCREENSHOT_UPLOAD_URL"
```

The response is JSON: `{ "url": "<public-url>" }`. Save the URL — you need it for both outputs below.

### Include in your final answer (REQUIRED)

ALWAYS include the video in your final answer using markdown image syntax — the Twill UI renders `.mp4` URLs as inline video players. This is how the user and integrations (GitHub, Slack, Linear) see your work:

```
![Screen recording](<uploaded-url>)
```

### Include in the PR description (REQUIRED if opening/updating a PR)

Paste the `.mp4` URL as a **bare URL on its own line** — no markdown syntax. GitHub only renders inline video players from bare URLs:

```
https://storage.googleapis.com/.../verification.mp4
```

Do NOT use `![](url)` or `[](url)` in the PR body — GitHub renders those as broken images.

### Self-check before finishing

Before writing your final answer, verify:

- [ ] Video was uploaded (you have a public URL)
- [ ] Video appears in the final answer as `![Screen recording](url)`
- [ ] If a PR was created/updated, video URL is in the PR body as a bare URL on its own line
