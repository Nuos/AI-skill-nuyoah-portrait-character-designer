#!/usr/bin/env python3
"""Build/check a deterministic source inventory. Excludes manifest itself and generated caches."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "dist", "build"}
SOURCE_DIRS = {"agents", "references", "scripts", "tests", "examples", "evals", ".github"}
SOURCE_ROOT_FILES = {".gitignore", "LICENSE", "README.md", "SKILL.md", "CHANGELOG.md"}


def inventory(root=ROOT):
    root = Path(root)
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        if (len(rel.parts) == 1 and rel.name not in SOURCE_ROOT_FILES) or (len(rel.parts) > 1 and rel.parts[0] not in SOURCE_DIRS):
            continue
        if path.is_symlink():
            raise ValueError("Source symlinks are not bundled: " + rel.as_posix())
        if not path.is_file():
            continue
        raw = path.read_bytes()
        files.append({"path": rel.as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return files


def digest(files):
    return hashlib.sha256(json.dumps(files, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def render(root=ROOT):
    files = inventory(root)
    return {
        "schemaVersion": 1,
        "name": "nuyoah-portrait-character-designer",
        "displayName": "通用四视图人物定妆照设计师",
        "version": "0.3.1",
        "license": "MIT",
        "source": "https://github.com/Nuos/AI-skill-nuyoah-portrait-character-designer",
        "homepage": "https://github.com/Nuos/AI-skill-nuyoah-portrait-character-designer",
        "upstream": "https://github.com/nuyoah-ai-works/nuyoah-portrait-character-designer",
        "baseCommit": "99b9a2c90e5b09507c6a61b5c27b9e2740ddb63d",
        "versionDate": "2026-09-25",
        "releaseDigest": digest(files),
        "digestScope": "SHA256 of canonical UTF-8 JSON files array; excludes manifest.json to avoid self-reference",
        "files": files,
        "installInstructions": "https://github.com/Nuos/AI-skill-nuyoah-portrait-character-designer/blob/main/README.md"
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = ROOT / "manifest.json"
    try:
        expected = render()
        if args.check:
            actual = json.loads(path.read_text(encoding="utf-8"))
            if actual != expected:
                raise ValueError("Manifest differs from source; run scripts/build_manifest.py after auditing changes")
        else:
            if path.is_symlink():
                raise ValueError("Refusing to overwrite a symlink manifest")
            path.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, "Manifest failed: " + str(exc) + "\n")
    print(json.dumps({"status": "PASS", "files": len(expected["files"]), "releaseDigest": expected["releaseDigest"]}))


if __name__ == "__main__":
    main()
