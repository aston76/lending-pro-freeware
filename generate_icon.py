#!/usr/bin/env python3
"""Generate the branded macOS, Windows, and web icons for Lending Pro."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent
SOURCE_PATH = ROOT / "branding" / "lending-pro-icon-source.png"
ICONSET_DIR = ROOT / "AppIcon.iconset"
ICNS_PATH = ROOT / "icon.icns"
ICO_PATH = ROOT / "icon.ico"
WEB_ICON_PATH = ROOT / "web" / "assets" / "lending-pro-mark.png"


def _rounded_alpha_mask(size: int, radius_ratio: float = 0.205) -> Image.Image:
    """Return an antialiased rounded-square mask at the requested size."""
    scale = 4
    mask = Image.new("L", (size * scale, size * scale), 0)
    draw = ImageDraw.Draw(mask)
    radius = int(size * scale * radius_ratio)
    draw.rounded_rectangle(
        (0, 0, size * scale - 1, size * scale - 1),
        radius=radius,
        fill=255,
    )
    return mask.resize((size, size), Image.Resampling.LANCZOS)


def _prepare_master() -> Image.Image:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(f"Brand source not found: {SOURCE_PATH}")

    with Image.open(SOURCE_PATH) as source:
        image = source.convert("RGBA")
        side = min(image.size)
        left = (image.width - side) // 2
        top = (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        edge_trim = max(2, int(side * 0.008))
        image = image.crop(
            (edge_trim, edge_trim, side - edge_trim, side - edge_trim)
        )
        image = image.resize((1024, 1024), Image.Resampling.LANCZOS)

    # The generated source contains white outside its rounded square. Applying
    # a deterministic alpha mask removes only those corners while preserving
    # the white ledger and chart details inside the mark.
    image.putalpha(_rounded_alpha_mask(1024))
    return image


def generate_icons() -> None:
    master = _prepare_master()
    WEB_ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    master.resize((512, 512), Image.Resampling.LANCZOS).save(
        WEB_ICON_PATH,
        "PNG",
        optimize=True,
    )

    if ICONSET_DIR.exists():
        shutil.rmtree(ICONSET_DIR)
    ICONSET_DIR.mkdir(parents=True)

    icon_files = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for filename, size in icon_files.items():
        master.resize((size, size), Image.Resampling.LANCZOS).save(
            ICONSET_DIR / filename,
            "PNG",
            optimize=True,
        )

    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET_DIR), "-o", str(ICNS_PATH)],
        check=True,
    )
    master.save(
        ICO_PATH,
        "ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    shutil.rmtree(ICONSET_DIR)

    print(f"macOS icon: {ICNS_PATH}")
    print(f"Windows icon: {ICO_PATH}")
    print(f"Web brand mark: {WEB_ICON_PATH}")


if __name__ == "__main__":
    generate_icons()
