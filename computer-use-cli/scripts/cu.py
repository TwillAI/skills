#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

OUTPUT_DIR = Path(os.environ.get("TWILL_SCREENSHOTS_DIR", "/tmp/outputs"))
TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50
ASPECT_RATIO_TOLERANCE = 0.02

Space = Literal["api", "screen"]


class CuError(RuntimeError):
    pass


@dataclass(frozen=True)
class Size:
    width: int
    height: int


@dataclass(frozen=True)
class ScaleInfo:
    screen: Size
    api: Size
    enabled: bool
    x_factor: float  # api -> screen
    y_factor: float
    target_name: str | None = None


MAX_SCALING_TARGETS: dict[str, Size] = {
    "XGA": Size(width=1024, height=768),  # 4:3
    "WXGA": Size(width=1280, height=800),  # 16:10
    "FWXGA": Size(width=1366, height=768),  # ~16:9
}


def which(cmd: str) -> str | None:
    return shutil.which(cmd)


def run(
    cmd: list[str],
    *,
    env: dict[str, str],
    timeout_s: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise CuError(f"Command timed out after {timeout_s}s: {cmd!r}") from e


def display_env(display: str | None) -> dict[str, str]:
    env = dict(os.environ)
    if display:
        env["DISPLAY"] = display
    if not env.get("DISPLAY"):
        raise CuError("DISPLAY is not set. Use --display :N or export DISPLAY=:N.")
    return env


def detect_screen_size(env: dict[str, str]) -> Size:
    w = os.getenv("WIDTH")
    h = os.getenv("HEIGHT")
    if w and h and w.isdigit() and h.isdigit():
        ww = int(w)
        hh = int(h)
        if ww > 0 and hh > 0:
            return Size(width=ww, height=hh)

    if not which("xdpyinfo"):
        raise CuError(
            "Cannot detect screen size. Set WIDTH/HEIGHT env vars or install x11-utils (xdpyinfo)."
        )
    cp = run(["xdpyinfo"], env=env, timeout_s=10.0)
    if cp.returncode != 0:
        raise CuError(f"xdpyinfo failed: {cp.stderr.strip()}")
    for line in cp.stdout.splitlines():
        line = line.strip()
        if line.startswith("dimensions:"):
            # "dimensions:    1024x768 pixels (..)"
            for tok in line.split():
                if "x" in tok and tok.replace("x", "").isdigit():
                    try:
                        ww_s, hh_s = tok.split("x", 1)
                        return Size(width=int(ww_s), height=int(hh_s))
                    except Exception:
                        pass
    raise CuError("Could not parse screen size from xdpyinfo.")


def compute_scale(screen: Size, *, scaling: bool) -> ScaleInfo:
    if not scaling:
        return ScaleInfo(
            screen=screen,
            api=screen,
            enabled=False,
            x_factor=1.0,
            y_factor=1.0,
            target_name=None,
        )

    ratio = screen.width / screen.height
    target: Size | None = None
    target_name: str | None = None
    for name, size in MAX_SCALING_TARGETS.items():
        if abs((size.width / size.height) - ratio) < ASPECT_RATIO_TOLERANCE:
            if size.width < screen.width:
                target = size
                target_name = name
            break

    if target is None:
        return ScaleInfo(
            screen=screen,
            api=screen,
            enabled=False,
            x_factor=1.0,
            y_factor=1.0,
            target_name=None,
        )

    return ScaleInfo(
        screen=screen,
        api=target,
        enabled=True,
        x_factor=screen.width / target.width,
        y_factor=screen.height / target.height,
        target_name=target_name,
    )


def scale_point(x: int, y: int, *, space: Space, scale: ScaleInfo) -> tuple[int, int]:
    if space == "screen" or not scale.enabled:
        if x < 0 or y < 0 or x > scale.screen.width or y > scale.screen.height:
            raise CuError(f"Screen coordinates out of bounds: ({x}, {y})")
        return x, y

    if x < 0 or y < 0 or x > scale.api.width or y > scale.api.height:
        raise CuError(f"API coordinates out of bounds: ({x}, {y}) for api={scale.api}")
    return (round(x * scale.x_factor), round(y * scale.y_factor))


def unscale_point(x: int, y: int, *, scale: ScaleInfo) -> tuple[int, int]:
    if not scale.enabled:
        return x, y
    return (round(x / scale.x_factor), round(y / scale.y_factor))


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def take_screenshot(
    env: dict[str, str],
    *,
    scale: ScaleInfo,
    out: Path | None,
    include_base64: bool,
) -> dict[str, object]:
    ensure_output_dir()
    path = out or (OUTPUT_DIR / f"screenshot_{uuid.uuid4().hex}.png")

    if which("gnome-screenshot"):
        cp = run(["gnome-screenshot", "-f", str(path), "-p"], env=env, timeout_s=30.0)
        if cp.returncode != 0:
            raise CuError(f"gnome-screenshot failed: {cp.stderr.strip()}")
    else:
        if not which("scrot"):
            raise CuError("No screenshot tool found. Install gnome-screenshot or scrot.")
        cp = run(["scrot", "-p", str(path)], env=env, timeout_s=30.0)
        if cp.returncode != 0:
            raise CuError(f"scrot failed: {cp.stderr.strip()}")

    if scale.enabled:
        if not which("convert"):
            raise CuError("ImageMagick 'convert' not found. Install imagemagick.")
        cp2 = run(
            [
                "convert",
                str(path),
                "-resize",
                f"{scale.api.width}x{scale.api.height}!",
                str(path),
            ],
            env=env,
            timeout_s=30.0,
        )
        if cp2.returncode != 0:
            raise CuError(f"convert resize failed: {cp2.stderr.strip()}")

    payload: dict[str, object] = {"screenshot_path": str(path)}
    if include_base64:
        payload["screenshot_base64_png"] = base64.b64encode(path.read_bytes()).decode()
    return payload


def xdotool(env: dict[str, str], args: list[str], *, timeout_s: float = 30.0) -> None:
    if not which("xdotool"):
        raise CuError("xdotool not found. Install xdotool.")
    cp = run(["xdotool", *args], env=env, timeout_s=timeout_s)
    if cp.returncode != 0:
        raise CuError((cp.stderr or cp.stdout or "xdotool failed").strip())


def chunk_text(s: str, n: int) -> list[str]:
    return [s[i : i + n] for i in range(0, len(s), n)]


def json_out(obj: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.write("\n")


def add_common_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--display", default=None, help="X11 display, e.g. :1 (defaults to $DISPLAY)"
    )
    p.add_argument(
        "--space",
        choices=["api", "screen"],
        default="api",
        help="Coordinate space for inputs (default: api).",
    )
    p.add_argument(
        "--no-scaling",
        action="store_true",
        help="Disable screenshot/coordinate scaling.",
    )
    p.add_argument(
        "--base64",
        action="store_true",
        help="Include screenshot_base64_png in output JSON.",
    )
    p.add_argument(
        "--no-screenshot",
        action="store_true",
        help="Skip post-action screenshot (not recommended).",
    )
    p.add_argument(
        "--screenshot-delay",
        type=float,
        default=2.0,
        help="Seconds to wait before taking post-action screenshot.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="cu")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_info = sub.add_parser("info")
    add_common_flags(p_info)

    p_shot = sub.add_parser("screenshot")
    add_common_flags(p_shot)
    p_shot.add_argument("--out", default=None, help="Output path for screenshot PNG.")

    p_move = sub.add_parser("move")
    add_common_flags(p_move)
    p_move.add_argument("--x", type=int, required=True)
    p_move.add_argument("--y", type=int, required=True)

    p_click = sub.add_parser("click")
    add_common_flags(p_click)
    p_click.add_argument("--x", type=int, required=True)
    p_click.add_argument("--y", type=int, required=True)
    p_click.add_argument(
        "--button", choices=["left", "right", "middle"], default="left"
    )
    p_click.add_argument(
        "--count", type=int, default=1, help="Click count (default: 1)."
    )

    p_drag = sub.add_parser("drag")
    add_common_flags(p_drag)
    p_drag.add_argument("--x0", type=int, required=True)
    p_drag.add_argument("--y0", type=int, required=True)
    p_drag.add_argument("--x1", type=int, required=True)
    p_drag.add_argument("--y1", type=int, required=True)

    p_type = sub.add_parser("type")
    add_common_flags(p_type)
    p_type.add_argument("--text", required=True)

    p_key = sub.add_parser("key")
    add_common_flags(p_key)
    p_key.add_argument("--keys", required=True, help='Example: "ctrl+l" or "Return"')

    p_scroll = sub.add_parser("scroll")
    add_common_flags(p_scroll)
    p_scroll.add_argument(
        "--dir", choices=["up", "down", "left", "right"], required=True
    )
    p_scroll.add_argument("--amount", type=int, required=True)
    p_scroll.add_argument("--x", type=int, default=None)
    p_scroll.add_argument("--y", type=int, default=None)

    p_wait = sub.add_parser("wait")
    add_common_flags(p_wait)
    p_wait.add_argument("--seconds", type=float, required=True)

    p_cursor = sub.add_parser("cursor")
    add_common_flags(p_cursor)

    p_zoom = sub.add_parser("zoom")
    add_common_flags(p_zoom)
    p_zoom.add_argument("--x0", type=int, required=True)
    p_zoom.add_argument("--y0", type=int, required=True)
    p_zoom.add_argument("--x1", type=int, required=True)
    p_zoom.add_argument("--y1", type=int, required=True)

    args = parser.parse_args()

    try:
        env = display_env(args.display)
        scaling = not bool(getattr(args, "no_scaling", False))
        screen = detect_screen_size(env)
        scale = compute_scale(screen, scaling=scaling)

        base = {
            "ok": True,
            "cmd": args.cmd,
            "display": env["DISPLAY"],
            "scale": {
                "enabled": scale.enabled,
                "screen": {"width": scale.screen.width, "height": scale.screen.height},
                "api": {"width": scale.api.width, "height": scale.api.height},
                "x_factor": scale.x_factor,
                "y_factor": scale.y_factor,
                "target": scale.target_name,
            },
        }

        if args.cmd == "info":
            json_out(base)
            return 0

        include_base64 = bool(getattr(args, "base64", False))
        if args.cmd == "screenshot":
            out = Path(args.out) if args.out else None
            base["result"] = take_screenshot(
                env, scale=scale, out=out, include_base64=include_base64
            )
            json_out(base)
            return 0

        space: Space = args.space

        # Actions
        if args.cmd == "move":
            x, y = scale_point(args.x, args.y, space=space, scale=scale)
            xdotool(env, ["mousemove", "--sync", str(x), str(y)])

        elif args.cmd == "click":
            x, y = scale_point(args.x, args.y, space=space, scale=scale)
            btn = {"left": "1", "middle": "2", "right": "3"}[args.button]
            if args.count < 1 or args.count > 10:
                raise CuError("--count must be between 1 and 10")
            xdotool(
                env,
                [
                    "mousemove",
                    "--sync",
                    str(x),
                    str(y),
                    "click",
                    "--repeat",
                    str(args.count),
                    "--delay",
                    "10",
                    btn,
                ],
            )

        elif args.cmd == "drag":
            x0, y0 = scale_point(args.x0, args.y0, space=space, scale=scale)
            x1, y1 = scale_point(args.x1, args.y1, space=space, scale=scale)
            xdotool(
                env,
                [
                    "mousemove",
                    "--sync",
                    str(x0),
                    str(y0),
                    "mousedown",
                    "1",
                    "mousemove",
                    "--sync",
                    str(x1),
                    str(y1),
                    "mouseup",
                    "1",
                ],
            )

        elif args.cmd == "type":
            for chunk in chunk_text(args.text, TYPING_GROUP_SIZE):
                xdotool(
                    env,
                    ["type", "--delay", str(TYPING_DELAY_MS), "--", chunk],
                    timeout_s=60.0,
                )

        elif args.cmd == "key":
            xdotool(env, ["key", "--", args.keys])

        elif args.cmd == "scroll":
            if args.amount < 0 or args.amount > 200:
                raise CuError("--amount must be between 0 and 200")
            if (args.x is None) ^ (args.y is None):
                raise CuError("Provide both --x and --y, or neither.")
            if args.x is not None and args.y is not None:
                x, y = scale_point(args.x, args.y, space=space, scale=scale)
                xdotool(env, ["mousemove", "--sync", str(x), str(y)])
            scroll_btn = {"up": "4", "down": "5", "left": "6", "right": "7"}[args.dir]
            xdotool(env, ["click", "--repeat", str(args.amount), scroll_btn])

        elif args.cmd == "wait":
            if args.seconds < 0 or args.seconds > 100:
                raise CuError("--seconds must be between 0 and 100")
            time.sleep(args.seconds)

        elif args.cmd == "cursor":
            cp = run(
                ["xdotool", "getmouselocation", "--shell"], env=env, timeout_s=10.0
            )
            if cp.returncode != 0:
                raise CuError(
                    (cp.stderr or cp.stdout or "xdotool cursor failed").strip()
                )
            x = int(cp.stdout.split("X=")[1].splitlines()[0])
            y = int(cp.stdout.split("Y=")[1].splitlines()[0])
            ax, ay = unscale_point(x, y, scale=scale)
            base["result"] = {
                "x": ax,
                "y": ay,
                "space": "api" if scale.enabled else "screen",
            }
            json_out(base)
            return 0

        elif args.cmd == "zoom":
            if not which("convert"):
                raise CuError("ImageMagick 'convert' not found. Install imagemagick.")
            # Crop must happen in *image space*.
            # Our screenshots are resized to API size when scaling is enabled.
            if scale.enabled and space == "screen":
                x0, y0 = unscale_point(args.x0, args.y0, scale=scale)
                x1, y1 = unscale_point(args.x1, args.y1, scale=scale)
            else:
                x0, y0 = args.x0, args.y0
                x1, y1 = args.x1, args.y1

            img_w = scale.api.width if scale.enabled else scale.screen.width
            img_h = scale.api.height if scale.enabled else scale.screen.height
            if not (
                0 <= x0 <= img_w
                and 0 <= x1 <= img_w
                and 0 <= y0 <= img_h
                and 0 <= y1 <= img_h
            ):
                raise CuError(
                    f"Region out of bounds for image {img_w}x{img_h}: ({x0},{y0})-({x1},{y1})"
                )
            if x1 <= x0 or y1 <= y0:
                raise CuError("Invalid region: x1/y1 must be greater than x0/y0")
            shot = take_screenshot(env, scale=scale, out=None, include_base64=False)
            src = Path(str(shot["screenshot_path"]))
            out = OUTPUT_DIR / f"zoom_{uuid.uuid4().hex}.png"
            w = x1 - x0
            h = y1 - y0
            cpz = run(
                [
                    "convert",
                    str(src),
                    "-crop",
                    f"{w}x{h}+{x0}+{y0}",
                    "+repage",
                    str(out),
                ],
                env=env,
                timeout_s=30.0,
            )
            if cpz.returncode != 0:
                raise CuError(f"convert crop failed: {cpz.stderr.strip()}")
            payload: dict[str, object] = {"screenshot_path": str(out)}
            if include_base64:
                payload["screenshot_base64_png"] = base64.b64encode(
                    out.read_bytes()
                ).decode()
            base["result"] = payload
            json_out(base)
            return 0

        else:
            raise CuError(f"Unknown cmd: {args.cmd}")

        # Post-action screenshot (default)
        if not bool(getattr(args, "no_screenshot", False)):
            time.sleep(float(getattr(args, "screenshot_delay", 0.0)))
            base["result"] = take_screenshot(
                env, scale=scale, out=None, include_base64=include_base64
            )
        else:
            base["result"] = {"note": "no_screenshot=true"}

        json_out(base)
        return 0

    except CuError as e:
        json_out({"ok": False, "error": str(e)})
        return 2
    except Exception as e:  # last resort
        json_out({"ok": False, "error": f"unexpected: {e.__class__.__name__}: {e}"})
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
