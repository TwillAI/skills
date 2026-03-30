#!/usr/bin/env python3
"""Build a webreel.config.json from a JSON argument."""
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: twill-video-build-config '<json>'", file=sys.stderr)
        print(
            "JSON fields: url, output, viewport (optional), steps (array)",
            file=sys.stderr,
        )
        return 1

    try:
        data = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        return 1

    url = data.get("url")
    if not url:
        print("Error: 'url' is required", file=sys.stderr)
        return 1

    steps = data.get("steps")
    if not steps or not isinstance(steps, list):
        print("Error: 'steps' must be a non-empty array", file=sys.stderr)
        return 1

    output = data.get("output", "verification.mp4")
    viewport = data.get("viewport", {"width": 1920, "height": 1080})
    zoom = data.get("zoom", 1)
    wait_for = data.get("waitFor")
    base_url = data.get("baseUrl")
    video_config: dict = {
        "url": url,
        "output": output,
        "steps": steps,
    }
    if zoom != 1:
        video_config["zoom"] = zoom
    if wait_for:
        video_config["waitFor"] = wait_for
    config: dict = {
        "$schema": "https://webreel.dev/schema/v1.json",
        "viewport": viewport,
        "videos": {
            "verification": video_config,
        },
    }
    if base_url:
        config["baseUrl"] = base_url

    config_path = Path("webreel.config.json")
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    print(json.dumps({"config": str(config_path.resolve()), "video": "verification"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
