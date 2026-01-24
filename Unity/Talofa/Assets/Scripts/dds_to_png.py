#!/usr/bin/env python3
"""
dds_to_png.py
Batch-convert .dds files to .png using Pillow.

Install dependency:
  pip install Pillow

Usage examples:
  python dds_to_png.py /path/to/file.dds
  python dds_to_png.py /path/to/folder --recursive
  python dds_to_png.py /path/to/folder --out /path/to/output --recursive
  python dds_to_png.py a.dds b.dds c.dds --out ./pngs
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Missing dependency: Pillow\nInstall with: pip install Pillow", file=sys.stderr)
    raise


def is_dds(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() == ".dds"


def iter_dds_inputs(inputs: list[Path], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for p in inputs:
        if p.is_file():
            if is_dds(p):
                files.append(p)
        elif p.is_dir():
            if recursive:
                for f in p.rglob("*"):
                    if is_dds(f):
                        files.append(f)
            else:
                for f in p.iterdir():
                    if is_dds(f):
                        files.append(f)

    # de-dupe while preserving order
    seen = set()
    out = []
    for f in files:
        fp = f.resolve()
        if fp not in seen:
            seen.add(fp)
            out.append(f)
    return out


def out_path_for(src: Path, out_dir: Path | None, base_dir: Path | None) -> Path:
    """
    If out_dir is provided and base_dir is provided, preserve relative structure under base_dir.
    Otherwise:
      - out_dir provided: write into out_dir with same filename (png)
      - out_dir not provided: write next to source file
    """
    if out_dir is None:
        return src.with_suffix(".png")

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if base_dir is not None:
        try:
            rel = src.resolve().relative_to(base_dir.resolve())
            return (out_dir / rel).with_suffix(".png")
        except ValueError:
            # src not under base_dir
            return (out_dir / src.name).with_suffix(".png")

    return (out_dir / src.name).with_suffix(".png")


def convert_one(src: Path, dst: Path, overwrite: bool) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)

    if dst.exists() and not overwrite:
        print(f"SKIP (exists): {dst}")
        return True

    try:
        with Image.open(src) as im:
            # Ensure a sane mode for PNG (keeps alpha if present)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA") if "A" in im.getbands() else im.convert("RGB")
            im.save(dst, format="PNG")
        print(f"OK: {src} -> {dst}")
        return True
    except Exception as e:
        print(f"FAIL: {src} ({e})", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert .dds files to .png")
    ap.add_argument("inputs", nargs="+", help="DDS file(s) and/or folder(s)")
    ap.add_argument("--out", "-o", default=None, help="Output folder (optional)")
    ap.add_argument("--recursive", "-r", action="store_true", help="Recurse into folders")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing PNGs")
    ap.add_argument(
        "--preserve-structure",
        action="store_true",
        help="When converting a folder, preserve folder structure under --out",
    )
    args = ap.parse_args()

    in_paths = [Path(x) for x in args.inputs]
    out_dir = Path(args.out) if args.out else None

    dds_files = iter_dds_inputs(in_paths, args.recursive)
    if not dds_files:
        print("No .dds files found.", file=sys.stderr)
        return 2

    # If preserving structure, pick a base_dir when a single directory input is given
    base_dir = None
    if args.preserve_structure and out_dir is not None:
        dir_inputs = [p for p in in_paths if p.is_dir()]
        if len(dir_inputs) == 1:
            base_dir = dir_inputs[0]

    ok = 0
    for src in dds_files:
        dst = out_path_for(src, out_dir, base_dir)
        ok += 1 if convert_one(src, dst, args.overwrite) else 0

    total = len(dds_files)
    failed = total - ok
    if failed:
        print(f"\nDone: {ok}/{total} converted, {failed} failed.", file=sys.stderr)
        return 1

    print(f"\nDone: {ok}/{total} converted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
