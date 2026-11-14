"""Sync static PWA assets from docs/ into Android app assets/www/."""

from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SRC_DOCS = ROOT / "docs"
DST_WWW = ROOT / "android" / "app" / "src" / "main" / "assets" / "www"
EXCLUDED_DIRS = {"download", "__pycache__"}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db"}


def sync_assets(src_dir: Path = SRC_DOCS, dst_dir: Path = DST_WWW) -> int:
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for item in src_dir.rglob("*"):
        rel = item.relative_to(src_dir)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if item.name in EXCLUDED_FILES:
            continue
        target = dst_dir / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            copied += 1
    return copied


if __name__ == "__main__":
    count = sync_assets()
    print(f"Synced {count} files from {SRC_DOCS} to {DST_WWW}")
