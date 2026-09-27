#!/usr/bin/env python3
"""One-time, branch-scoped restoration of the user's v0.3.1 delivery.

Regenerate deterministic text artifacts and restore deduplicated historical
records exactly. Historical log bytes are not presented as new test results.
Fresh tests run independently below. No image service is called. No merge,
force-push, main-branch write, or credential discovery is performed here.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPOSITORY = "Nuos/AI-skill-nuyoah-portrait-character-designer"
BRANCH = "update/four-view-v0.3.1-20260927"
EXPECTED_TREE = "8a0ad5ca0f91fa751979c4abe2432670efe4f65f"
EXPECTED_SOURCE_DIGEST = "3b64f1cab96163b4f900cdd2d7f74c0ec0ec1fb172bbecdc384ebf6ea1e8e56c"

# Lossless deduplication data extracted from the previously delivered logs.
# These are historical suffixes, not the output of this workflow's fresh tests.
HISTORICAL_LOGS = {
    "validation/v0.3.1/baseline-tests.txt": {
        "prefix": "",
        "test_lines": 57,
        "suffix": "\n----------------------------------------------------------------------\nRan 57 tests in 2.880s\n\nOK\n",
        "sha256": "c36fa831050da0a6823a009be0da53e5228eae9f503d5f1c5bb3076c0a74e49f"
    },
    "validation/v0.3.1/distribution-tests.txt": {
        "prefix": "$ /opt/pyvenv/bin/python3 -m unittest discover -s tests -v\n",
        "test_lines": 85,
        "suffix": "\n----------------------------------------------------------------------\nRan 85 tests in 3.453s\n\nOK\n\nExit code: 0\n\n$ /opt/pyvenv/bin/python3 scripts/build_manifest.py --check\n{\"status\": \"PASS\", \"files\": 45, \"releaseDigest\": \"3b64f1cab96163b4f900cdd2d7f74c0ec0ec1fb172bbecdc384ebf6ea1e8e56c\"}\n\nExit code: 0\n\n$ /opt/pyvenv/bin/python3 scripts/check_design.py examples/myth-laborer-188.json\n{\n  \"status\": \"PASS\",\n  \"errors\": [],\n  \"warnings\": [],\n  \"pairs\": [],\n  \"image_review\": \"UNVERIFIED\",\n  \"scope\": \"encoded plan only; authorization, age/era semantics, identity and pixels require separate review\"\n}\n\nExit code: 0\n\nFresh ZIP extraction and all 45 source SHA256 checks: PASS\n",
        "sha256": "02cf3d5e9572fa504bcd9116710a88283be98ee3a00d74a8f274b9f32873159e"
    },
    "validation/v0.3.1/submission-20260926/verification.txt": {
        "prefix": "$ python3 -m unittest discover -s tests -v\n",
        "test_lines": 85,
        "suffix": "\n----------------------------------------------------------------------\nRan 85 tests in 4.705s\n\nOK\n\nExit code: 0\n\n$ python3 scripts/build_manifest.py --check\n{\"status\": \"PASS\", \"files\": 45, \"releaseDigest\": \"3b64f1cab96163b4f900cdd2d7f74c0ec0ec1fb172bbecdc384ebf6ea1e8e56c\"}\n\nExit code: 0\n\n$ python3 scripts/check_design.py examples/myth-laborer-188.json\n{\n  \"status\": \"PASS\",\n  \"errors\": [],\n  \"warnings\": [],\n  \"pairs\": [],\n  \"image_review\": \"UNVERIFIED\",\n  \"scope\": \"encoded plan only; authorization, age/era semantics, identity and pixels require separate review\"\n}\n\nExit code: 0\n\n$ python3 scripts/randomized_smoke.py --seed 20260925 --count 24 --out /mnt/data/nuyoah-submit-verification/randomized\n{\n  \"schema_version\": 1,\n  \"seed\": 20260925,\n  \"sampling\": \"seeded stratified age coverage; other fields pseudorandom, not population statistics\",\n  \"plan_count\": 24,\n  \"prompt_count\": 120,\n  \"rejected_mutations\": 192,\n  \"status\": \"PASS\",\n  \"scope\": \"offline structured plans and compiled text; not model inference or image validation\"\n}\n\nExit code: 0\n\n$ python3 scripts/export_gpt.py --out /mnt/data/nuyoah-submit-verification/gpt-export\n{\"status\": \"PASS\", \"files\": [\"instructions.txt\", \"knowledge-lexicon.md\", \"app-config.json\", \"export-manifest.json\"]}\n\nExit code: 0\n",
        "sha256": "6f3950d6d4070cf955e5df425ff852cf6fb6d89cfc1fac603207f627cd279017"
    }
}


def write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def regenerate(root):
    sys.path.insert(0, str(root))
    from scripts import randomized_smoke, build_prompt, check_turnaround, export_gpt, build_manifest

    preset = check_turnaround.load_plan(root / "examples/myth-laborer-188.json")
    write(root, "examples/sources/myth-laborer-user-prompt.txt", preset["request"]["text"] + "\n")
    intro = "# 神话劳作者四视图：188厘米专用示例\n\n本例来自用户提供的角色提示词。中年男性、188厘米、九头身、左脸旧伤、灰亚麻短袍与赤足仅属于此例，不是全局默认。目标尺寸采用本次测试用2048×1152，不声称已经原生生成。\n\n```text\n"
    write(root, "examples/myth-laborer-188-optimized.md", intro + build_prompt.render(preset) + "```\n")

    # The caller supplies a clean snapshot. Existing deterministic outputs can
    # be verified byte-for-byte, never silently kept or overwritten on mismatch.
    with tempfile.TemporaryDirectory() as fresh:
        output = Path(fresh) / "randomized"
        report = randomized_smoke.run(seed=20260925, count=24, out=output)
        for path in sorted(output.rglob("*")):
            if path.is_file():
                rel = Path("validation/v0.3.1/randomized") / path.relative_to(output)
                old = root / rel
                if old.exists() and old.read_bytes() != path.read_bytes():
                    raise ValueError("Generated artifact differs: " + str(rel))
                write(root, rel, path.read_text(encoding="utf-8"))
    summary = {k: v for k, v in report.items() if k != "cases"}
    summary["cases"] = []
    for case in report["cases"]:
        row = {k: case[k] for k in ("id", "gender", "age", "era", "side", "plan_status", "image_review")}
        row["sheet_sha256"] = case["prompt_sha256"]["sheet"]
        summary["cases"].append(row)
    write(root, "evals/randomized-v0.3.1.json", json_text(summary))
    write(root, "validation/v0.3.1/submission-20260926/randomized-report.json", json_text(report))

    # Preserve the prior 144-file comparison record. Its exact content is
    # protected by EXPECTED_TREE; a fresh deterministic comparison was above.
    relative_files = sorted(p.relative_to(root / "validation/v0.3.1/randomized").as_posix()
                            for p in (root / "validation/v0.3.1/randomized").rglob("*")
                            if p.is_file() and p.name != "report.json")
    if len(relative_files) != 144:
        raise ValueError("Expected 144 character plan/prompt files")
    historical_comparison = [{"path": p, "same_bytes": True} for p in relative_files]
    write(root, "validation/v0.3.1/submission-20260926/reproducibility.json", json_text(historical_comparison))
    write(root, "validation/v0.3.1/original-delivery/audit-v0.3.1.md",
          (root / "references/audit-v0.3.1.md").read_text(encoding="utf-8"))

    source_lines = (root / "tests/run-v0.3.1.txt").read_text(encoding="utf-8").splitlines(keepends=True)
    for rel, record in HISTORICAL_LOGS.items():
        text = record["prefix"] + "".join(source_lines[:record["test_lines"]]) + record["suffix"]
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != record["sha256"]:
            raise ValueError("Historical record failed exact byte verification: " + rel)
        write(root, rel, text)

    for name, text in export_gpt.render().items():
        write(root, "exports/gpt/v0.3.1/" + name, text)
    manifest = build_manifest.render()
    if manifest["releaseDigest"] != EXPECTED_SOURCE_DIGEST:
        print(json_text(manifest), flush=True)
        raise ValueError("Source inventory differs from the 45-file delivery inventory")
    write(root, "manifest.json", json_text(manifest))
    return report


def tree_for(root, files, database):
    subprocess.run(["git", "init", "--bare", str(database)], check=True, stdout=subprocess.DEVNULL)
    env = dict(os.environ, GIT_DIR=str(database), GIT_WORK_TREE=str(root))
    env.pop("GIT_INDEX_FILE", None)
    subprocess.run(["git", "add", "--", *files], env=env, check=True)
    tree = subprocess.check_output(["git", "write-tree"], env=env, text=True).strip()
    if tree != EXPECTED_TREE:
        subprocess.run(["git", "ls-tree", "-r", tree], env=env, check=True)
        raise ValueError("Expected " + EXPECTED_TREE + "; got " + tree)
    return tree


def main():
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY or os.environ.get("GITHUB_REF") != "refs/heads/" + BRANCH:
        raise SystemExit("This one-time job is restricted to the authorized feature branch")
    checkout = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
    if head != os.environ.get("GITHUB_SHA"):
        raise SystemExit("Checkout does not match the triggering commit")
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    with tempfile.TemporaryDirectory() as temp:
        temp = Path(temp)
        snapshot = temp / "delivery"
        shutil.copytree(checkout, snapshot, ignore=shutil.ignore_patterns(".git", ".github", "__pycache__"))
        report = regenerate(snapshot)
        print("Fresh tests on restored delivery (historical log files were preserved separately):", flush=True)
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=snapshot, check=True)
        subprocess.run([sys.executable, "scripts/build_manifest.py", "--check"], cwd=snapshot, check=True)
        files = sorted(p.relative_to(snapshot).as_posix() for p in snapshot.rglob("*")
                       if p.is_file() and "__pycache__" not in p.parts)
        if len(files) != 204:
            raise ValueError("Expected 204 delivery files, got " + str(len(files)))
        tree = tree_for(snapshot, files, temp / "verified.git")
        print("VERIFIED_DELIVERY_TREE=" + tree, flush=True)
        print(json_text({k: v for k, v in report.items() if k != "cases"}), flush=True)
        for rel in files:
            destination = checkout / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snapshot / rel, destination)
        subprocess.run(["git", "add", "--", *files], cwd=checkout, check=True)
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=checkout, check=True)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=checkout, check=True)
        subprocess.run(["git", "commit", "-m", "build: restore and verify all 204 v0.3.1 delivery files"], cwd=checkout, check=True)
        # Compare-and-push the same branch only. A concurrent update aborts;
        # there is deliberately no force-push, merge, or write to main here.
        remote = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/" + BRANCH], cwd=checkout, text=True).split()
        if not remote or remote[0] != head:
            raise ValueError("Feature branch changed during validation; refusing to overwrite")
        subprocess.run(["git", "push", "origin", "HEAD:refs/heads/" + BRANCH], cwd=checkout, check=True)
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write("## Verified v0.3.1 delivery\n\n204 files match the handoff tree `" + tree + "`.\n\nFresh tests: 85 passed. Randomized plans: 24; prompts: 120; rejected mutations: 192.\n\nHistorical records remain unchanged. Generated images: 0; image quality UNVERIFIED.\n\nArtifacts committed only to `" + BRANCH + "`; main requires the separately authorized pull-request merge.\n")


if __name__ == "__main__":
    main()
