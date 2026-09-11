#!/usr/bin/env python3
"""Export GPT artifacts from Skill rules; no network or app writes."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ("references/decision-rules.md", "references/structure-and-compatibility.md",
         "references/makeup-adaptation.md")
KNOWLEDGE = ("references/lexicon.md", "references/sources.md")
def sha(data):
    return hashlib.sha256(data).hexdigest()
def render():
    instructions = "\n\n".join((ROOT / name).read_text(encoding="utf-8").strip() for name in RULES)
    if len(instructions) > 8000:
        raise ValueError("Instructions exceed GPT editor limit; compact the source rules")
    knowledge = "\n\n".join((ROOT / name).read_text(encoding="utf-8").strip() for name in KNOWLEDGE)
    config = {
        "name": "南鸢·人像角色设定师",
        "description": "把人物气质转成具体脸部结构、适配妆容与完整中文提示词。支持同妆不同脸、固定人物换妆和局部反推；明确要求时可生成图片。",
        "conversation_starters": [
            "我想要设计一个日系昭和感的女性角色形象。",
            "同一套桃粉妆，设计五个不同脸的成年角色。",
            "保留同一个人物，只把唇妆改成柔雾红唇。",
            "我有一张参考图，只拆解妆容，不沿用参考人物的脸。"
        ],
        "capabilities": {"web_search": True, "image_generation": True, "code_interpreter": False},
        "visibility": "only_me",
        "recommended_model": None
    }
    files = {
        "instructions.txt": instructions + "\n",
        "knowledge-lexicon.md": knowledge + "\n",
        "app-config.json": json.dumps(config, ensure_ascii=False, indent=2) + "\n"
    }
    manifest = {
        "source_sha256": {p: sha((ROOT / p).read_bytes()) for p in RULES + KNOWLEDGE},
        "output_sha256": {p: sha(s.encode("utf-8")) for p, s in files.items()},
        "instructions_characters": len(files["instructions.txt"]),
        "image_generation": "optional and enabled",
        "scope": "export only; live app save and behavior require separate verification"
    }
    files["export-manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return files
def export(out):
    out = Path(out).resolve()
    if out == ROOT or ROOT in out.parents:
        raise ValueError("Export outside the Skill source directory")
    files = render()
    out.mkdir(parents=True, exist_ok=True)
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
