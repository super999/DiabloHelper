"""AVIF -> PNG batch converter.

Usage:
  python tools/avif_to_png.py <path> [--out <out_dir>] [--recursive] [--overwrite]

- <path> can be a file or a directory.
- If a directory is provided, this scans for AVIF by:
    1) file extension .avif (case-insensitive), OR
    2) ISO-BMFF header brand 'avif' (so files mislabeled as .png will also be detected)

Notes about "PNG looks more gray":
- Many "looks gray" issues come from missing/ignored ICC color profiles.
- This tool tries to convert embedded ICC profiles to sRGB before saving PNG.

Dependencies:
- Pillow
- pillow-avif-plugin (enables AVIF decoding in Pillow)

Install (recommended):
  pip install Pillow pillow-avif-plugin
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ConvertResult:
    src: Path
    dst: Path
    ok: bool
    reason: str = ""


def _is_probably_avif(path: Path) -> bool:
    """Detect AVIF either by extension or by ISO-BMFF header brand."""
    if path.suffix.lower() == ".avif":
        return True

    try:
        head = path.read_bytes()[:32]
    except Exception:
        return False

    # ISO-BMFF: bytes[4:8] == b"ftyp", brand at bytes[8:12]
    if len(head) >= 12 and head[4:8] == b"ftyp":
        brand = head[8:12]
        return brand == b"avif"

    return False


def _iter_candidates(input_path: Path, recursive: bool) -> Iterable[Path]:
    if input_path.is_file():
        yield input_path
        return

    if not input_path.is_dir():
        return

    if recursive:
        yield from (p for p in input_path.rglob("*") if p.is_file())
    else:
        yield from (p for p in input_path.glob("*") if p.is_file())


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _convert_one(
    src: Path,
    dst: Path,
    *,
    overwrite: bool,
    color_manage: bool,
) -> ConvertResult:
    if not overwrite and dst.exists():
        return ConvertResult(src=src, dst=dst, ok=False, reason="dst exists")

    try:
        from PIL import Image  # type: ignore
    except Exception:
        return ConvertResult(
            src=src,
            dst=dst,
            ok=False,
            reason="missing Pillow (pip install Pillow pillow-avif-plugin)",
        )

    # Ensure AVIF plugin is registered (import side-effect)
    try:
        import pillow_avif  # type: ignore  # noqa: F401
    except Exception:
        # Without plugin, Image.open will usually fail on AVIF
        return ConvertResult(
            src=src,
            dst=dst,
            ok=False,
            reason="missing pillow-avif-plugin (pip install pillow-avif-plugin)",
        )

    try:
        with Image.open(src) as im:
            im.load()

            icc_profile = im.info.get("icc_profile")

            # Convert to sRGB if ICC present (helps with "looks gray" mismatches)
            if color_manage and icc_profile:
                try:
                    from PIL import ImageCms  # type: ignore

                    srgb = ImageCms.createProfile("sRGB")
                    src_prof = ImageCms.ImageCmsProfile(io=icc_profile)
                    im = ImageCms.profileToProfile(im, src_prof, srgb, outputMode=im.mode)
                except Exception:
                    # If color management fails, continue without it
                    pass

            # PNG supports RGB/RGBA well
            if im.mode not in ("RGB", "RGBA"):
                # Preserve alpha when possible
                if "A" in im.getbands():
                    im = im.convert("RGBA")
                else:
                    im = im.convert("RGB")

            _ensure_parent_dir(dst)
            im.save(dst, format="PNG")

    except Exception as e:
        return ConvertResult(src=src, dst=dst, ok=False, reason=f"convert failed: {e!r}")

    return ConvertResult(src=src, dst=dst, ok=True)


def _default_out_path(src: Path, out_dir: Path | None, base_dir: Path | None) -> Path:
    # If out_dir is provided, preserve relative structure from base_dir (if any)
    if out_dir is not None:
        if base_dir is not None:
            try:
                rel = src.relative_to(base_dir)
            except Exception:
                rel = src.name
        else:
            rel = src.name

        rel_path = Path(rel)
        # If the source is mislabeled .png but is AVIF, avoid overwriting by adding suffix
        if rel_path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            out_name = rel_path.with_suffix("").name + ".from_avif.png"
            rel_path = rel_path.with_name(out_name)
        else:
            rel_path = rel_path.with_suffix(".png")

        return out_dir / rel_path

    # No out_dir: write next to source, but avoid overwriting if extension isn't .avif
    if src.suffix.lower() == ".avif":
        return src.with_suffix(".png")

    return src.with_suffix("").with_name(src.stem + ".from_avif.png")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Scan and convert AVIF files to PNG")
    parser.add_argument("path", help="A file path or directory")
    parser.add_argument(
        "--out",
        dest="out_dir",
        default=None,
        help="Output directory. If omitted, outputs next to source files.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively scan subdirectories (when path is a directory)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files",
    )
    parser.add_argument(
        "--no-color-management",
        action="store_true",
        help="Disable ICC->sRGB conversion",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.path)
    out_dir = Path(args.out_dir) if args.out_dir else None
    if out_dir is not None:
        out_dir = out_dir.resolve()

    if not input_path.exists():
        print(f"ERROR: path not found: {input_path}", file=sys.stderr)
        return 2

    base_dir = input_path if input_path.is_dir() else input_path.parent

    candidates = list(_iter_candidates(input_path, recursive=bool(args.recursive)))
    if not candidates:
        print("No files found.")
        return 0

    to_convert = [p for p in candidates if _is_probably_avif(p)]
    if not to_convert:
        print("No AVIF files detected (by extension or header).")
        return 0

    ok = 0
    skipped = 0
    failed = 0

    for src in to_convert:
        dst = _default_out_path(src, out_dir=out_dir, base_dir=base_dir)
        res = _convert_one(
            src,
            dst,
            overwrite=bool(args.overwrite),
            color_manage=not bool(args.no_color_management),
        )

        if res.ok:
            ok += 1
            print(f"OK   {res.src} -> {res.dst}")
        else:
            if res.reason == "dst exists":
                skipped += 1
                print(f"SKIP {res.src} -> {res.dst} ({res.reason})")
            else:
                failed += 1
                print(f"FAIL {res.src} -> {res.dst} ({res.reason})")

    print(f"Done. ok={ok} skipped={skipped} failed={failed} total={len(to_convert)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
