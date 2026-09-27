#!/usr/bin/env python3
"""Export GPT artifacts from the canonical Skill rules; no network or app writes."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ("SKILL.md", "references/decision-rules.md", "references/four-view-contract.md",
         "references/identity-and-era.md")
KNOWLEDGE = ("references/structure-and-compatibility.md", "references/lexicon.md",
             "references/turnaround-lexicon.json", "references/makeup-adaptation.md", "references/check-contract.md",
             "references/prompt-template.md", "references/acceptance-and-gpt.md", "references/sources.md")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def render():
    instructions = "\n\n".join((ROOT / name).read_text(encoding="utf-8").strip() for name in RULES) + "\n"
    if len(instructions) > 8000:
        raise ValueError("Instructions exceed the project 8000-character compatibility budget; do not truncate")
    knowledge = "\n\n".join((ROOT / name).read_text(encoding="utf-8").strip() for name in KNOWLEDGE) + "\n"
    config = {
        "name": "通用四视图人物定妆照设计师",
        "description": "任意性别、年龄与时代的写实定妆照；人像特写、正面全身、标准侧面全身与背面全身。默认文字，显式要求才生图。",
        "conversation_starters": [
            "为一个70岁的当代木匠写四视图定妆照提示词，保持自然体型和皱纹。",
            "为8岁的儿童设计适龄、自然无妆的四视图，不套用成人比例。",
            "设计一个性别不指定的未来研究员，给出人像特写与正侧背全身。",
            "以我的参考图为身份基准，只换成神话国王装束，其它保持不变。"
        ],
        "capabilities": {"web_search": True, "image_generation": True, "code_interpreter": False},
        "visibility": "only_me",
        "recommended_model": None
    }
    files = {
        "instructions.txt": instructions,
        "knowledge-lexicon.md": knowledge,
        "app-config.json": json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    }
    manifest = {
        "skill_version": "0.3.1",
        "source_sha256": {p: sha((ROOT / p).read_bytes()) for p in RULES + KNOWLEDGE},
        "output_sha256": {p: sha(s.encode("utf-8")) for p, s in files.items()},
        "instructions_characters": len(instructions),
        "image_generation": "optional and enabled; current explicit user request required",
        "scope": "export only; live app save, model behavior and images remain separately unverified"
    }
    files["export-manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return files


def export(out):
    out = Path(out).resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValueError("Export outside the Skill source directory")
    files = render()
    out.mkdir(parents=True, exist_ok=True)
    # Never follow an existing output symlink back into the source tree.
    for name in files:
        dest = out / name
        if dest.is_symlink() or (dest.exists() and not dest.is_file()):
            raise ValueError("Unsafe export destination: " + str(dest))
    for name, data in files.items():
        (out / name).write_text(data, encoding="utf-8")
    return list(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        names = export(args.out)
    except (OSError, ValueError) as exc:
        parser.exit(1, "Export failed: " + str(exc) + "\n")
    print(json.dumps({"status": "PASS", "files": names}, ensure_ascii=False))


if __name__ == "__main__":
    main()
