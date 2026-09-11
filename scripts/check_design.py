#!/usr/bin/env python3
"""Read-only checks for encoded design constraints, never image quality."""
import argparse
import itertools
import json
from pathlib import Path

AXES = {
    "face.ratio": ("short", "balanced", "long"),
    "face.midface": ("short", "balanced", "long"),
    "jaw.width": ("narrow", "medium", "wide"),
    "jaw.chin": ("round", "tapered", "square"),
    "eyes.length": ("short", "medium", "long"),
    "eyes.opening": ("small", "medium", "large"),
    "eyes.spacing": ("close", "medium", "wide"),
    "eyes.lid": ("single", "hooded", "double"),
    "eyes.tilt": ("down", "level", "up"),
    "nose.height": ("low", "medium", "high"),
    "nose.width": ("narrow", "medium", "wide"),
    "nose.tip": ("round", "defined", "broad"),
    "lips.width": ("narrow", "medium", "wide"),
    "lips.ratio": ("lower_fuller", "balanced", "upper_fuller"),
    "brows.arc": ("straight", "soft", "angled"),
    "brows.distance": ("close", "medium", "wide"),
}
GROUPS = ("face", "jaw", "eyes", "nose", "lips", "brows")
MAKEUP_KEYS = ("palette", "finish", "direction", "placement")

def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result

def check(plan):
    errors, pairs = [], []
    def problem(message):
        errors.append(message)
    def axes_map(value, label, complete=False):
        if not isinstance(value, dict):
            problem(label + " must be an object")
            return {}
        for key, val in value.items():
            if key not in AXES:
                problem(label + ": unknown axis " + key)
            elif not isinstance(val, str) or val not in AXES[key]:
                problem(label + ": invalid value for " + key)
        if complete and set(value) != set(AXES):
            problem(label + ": complete canonical axes required")
        return {k: v for k, v in value.items()
                if k in AXES and isinstance(v, str) and v in AXES[k]}
    if not isinstance(plan, dict):
        return {"status": "FAIL", "errors": ["plan must be an object"], "pairs": []}
    if type(plan.get("schema_version")) is not int or plan["schema_version"] != 1:
        problem("schema_version must be 1")
    req = plan.get("request")
    if not isinstance(req, dict):
        req = {}
        problem("request must be an object")
    if not isinstance(req.get("text"), str) or not req.get("text", "").strip():
        problem("request.text must retain the current request")
    if req.get("mode") not in ("text", "image"):
        problem("request.mode must be text or image")
    if type(req.get("explicit_image_request")) is not bool:
        problem("explicit_image_request must be a boolean")
    if req.get("mode") == "image" and req.get("explicit_image_request") is not True:
        problem("image mode lacks explicit current image request")
    goal = plan.get("roster_goal")
    if goal not in ("single", "distinct", "identity", "related"):
        problem("unknown roster_goal")
    same_makeup = plan.get("same_makeup", False)
    if type(same_makeup) is not bool:
        problem("same_makeup must be a boolean")
    locks = axes_map(plan.get("locks", {}), "locks")
    reference = axes_map(plan.get("reference_axes", {}), "reference_axes", goal == "identity")
    chars = plan.get("characters")
    if not isinstance(chars, list) or not chars:
        chars = []
        problem("characters must be a nonempty array")
    if goal == "distinct" and len(chars) < 2:
        problem("distinct requires at least two characters")
    if goal == "single" and len(chars) != 1:
        problem("single requires one character")
    ids, normalized, makeup_baseline = set(), [], None
    for index, char in enumerate(chars):
        label = "character[" + str(index) + "]"
        if not isinstance(char, dict):
            problem(label + " must be an object")
            continue
        ident = char.get("id")
        if not isinstance(ident, str) or not ident.strip() or ident in ids:
            problem(label + ": id must be unique and nonempty")
            ident = label
        ids.add(ident)
        axes = axes_map(char.get("axes"), ident + ".axes", goal in ("distinct", "identity"))
        local_locks = axes_map(char.get("locks", {}), ident + ".locks")
        for key in set(locks) & set(local_locks):
            if locks[key] != local_locks[key]:
                problem(ident + ": local/global lock conflict on " + key)
        for key, value in {**locks, **local_locks}.items():
            if axes.get(key) != value:
                problem(ident + ": lock violation on " + key)
        if goal == "identity" and axes != reference:
            problem(ident + ": identity differs from reference_axes")
        if same_makeup is True:
            makeup = char.get("makeup")
            if (not isinstance(makeup, dict)
                    or any(not isinstance(makeup.get(k), str) or not makeup[k].strip()
                           for k in MAKEUP_KEYS)):
                problem(ident + ": complete makeup contract required")
            else:
                contract = {k: makeup[k] for k in MAKEUP_KEYS}
                if makeup_baseline is None:
                    makeup_baseline = contract
                elif contract != makeup_baseline:
                    problem(ident + ": makeup contract differs")
        normalized.append((ident, axes))
    if goal == "distinct":
        for (a_id, a), (b_id, b) in itertools.combinations(normalized, 2):
            changed = sorted({k.split(".")[0] for k in set(a) & set(b) if a[k] != b[k]})
            core = sorted(set(changed) & {"face", "eyes", "nose"})
            pairs.append({"a": a_id, "b": b_id, "groups": changed, "core": core})
            if len(changed) < 4 or len(core) < 2:
                problem(a_id + "/" + b_id + ": insufficient independent structural differences")
    return {"status": "FAIL" if errors else "PASS", "errors": errors, "pairs": pairs,
            "scope": "encoded constraints only; semantics and images require review"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
        result = check(plan)
    except (OSError, UnicodeError, ValueError) as exc:
        result = {"status": "FAIL", "errors": ["Invalid input: " + str(exc)], "pairs": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
