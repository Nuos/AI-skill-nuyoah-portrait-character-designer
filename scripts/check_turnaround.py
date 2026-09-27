#!/usr/bin/env python3
"""Validate schema-v2 four-view plans, not images. Python standard library only."""
import argparse
import json
import math
from pathlib import Path

VIEW_IDS = ("portrait", "front", "side", "back")
APPEARANCE_KEYS = ("skin", "hair", "makeup", "costume", "accessories")
MISSING = object()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("Non-finite JSON number: " + value)


def load_plan(path):
    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=unique_keys, parse_constant=reject_constant)


def resolve(value, path):
    """Resolve a dotted object path without evaluating code or reading files."""
    if not isinstance(path, str) or not path:
        return MISSING
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return value


def equal(a, b):
    """Exact typed equality: a JSON boolean is not a numeric lock value."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def changed_paths(before, after, prefix=""):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after), key=str):
            path = prefix + "." + str(key) if prefix else str(key)
            result.extend(changed_paths(before.get(key, MISSING), after.get(key, MISSING), path))
        return result
    return [] if equal(before, after) else [prefix]


def read_vocabulary():
    """Read the project-owned vocabulary; no external path or network inputs."""
    data = load_plan(Path(__file__).resolve().parents[1] / "references/turnaround-lexicon.json")
    terms = data.get("terms")
    if data.get("schema_version") != 1 or not isinstance(terms, list):
        raise ValueError("Invalid vocabulary catalog")
    ids = [t.get("id") for t in terms if isinstance(t, dict)]
    if len(ids) != len(terms) or not all(isinstance(x, str) and x for x in ids) or len(set(ids)) != len(ids):
        raise ValueError("Vocabulary IDs must be nonempty and unique")
    for t in terms:
        if (t.get("scope") not in ("universal", "conditional", "character")
                or t.get("when") not in ("always", "standing", "natural_ratio", "explicit_ratio", "unsupported", "adult", "adult_standing")
                or not isinstance(t.get("text"), str) or not t["text"].strip()
                or not isinstance(t.get("views"), list) or not t["views"]
                or any(v not in ("sheet",) + VIEW_IDS for v in t["views"])
                or not isinstance(t.get("negative"), list)
                or any(not isinstance(x, str) or not x.strip() for x in t["negative"])):
            raise ValueError("Invalid vocabulary entry: " + t["id"])
    defaults = data.get("default_ids")
    if not isinstance(defaults, list) or any(x not in ids for x in defaults) or len(set(defaults)) != len(defaults):
        raise ValueError("Invalid vocabulary defaults")
    if any(t["scope"] == "character" and t["id"] in defaults for t in terms):
        raise ValueError("Character-specific terms cannot be global defaults")
    return data


def eligible(term, plan):
    c = plan.get("character", {})
    if not isinstance(c, dict):
        return False
    pose, body, age = (c.get(k, {}) for k in ("pose", "body", "age"))
    if not all(isinstance(x, dict) for x in (pose, body, age)):
        return False
    posture, years, stage = pose.get("posture"), age.get("years"), age.get("life_stage")
    adult = stage not in ("infant", "child", "adolescent") and (
        (type(years) in (int, float) and years >= 18) or
        (years is None and stage in ("adult", "older_adult")))
    conditions = {
        "always": True,
        "standing": posture == "standing",
        "unsupported": isinstance(posture, str) and not posture.startswith("supported_"),
        "natural_ratio": body.get("head_body_ratio") is None,
        "explicit_ratio": body.get("proportion_mode") == "explicit" and body.get("head_body_ratio") is not None,
        "adult": adult,
        "adult_standing": adult and posture == "standing",
    }
    return conditions.get(term["when"], False)


def selected_terms(plan, view="sheet"):
    """Return eligible entries in catalog order. Caller validates the plan first."""
    catalog = read_vocabulary()
    selection = plan.get("vocabulary", {})
    ids = set(catalog["default_ids"] + selection.get("include", [])) - set(selection.get("exclude", []))
    return [t for t in catalog["terms"] if t["id"] in ids and view in t["views"] and eligible(t, plan)]


def check(plan):
    errors, warnings = [], []

    def problem(path, message):
        errors.append(path + ": " + message)

    def obj(value, path, required=(), optional=()):
        if not isinstance(value, dict):
            problem(path, "must be an object")
            return {}
        for key in required:
            if key not in value:
                problem(path + "." + key, "required")
        for key in value:
            if key not in required and key not in optional:
                problem(path, "unknown field " + repr(key))
        return value

    def text(value, path):
        if not isinstance(value, str) or not value.strip():
            problem(path, "must be a nonempty string")
            return False
        return True

    def strings(value, path):
        if not isinstance(value, list):
            problem(path, "must be an array of strings")
            return []
        for i, item in enumerate(value):
            text(item, path + "[" + str(i) + "]")
        return value

    def number(value, path, minimum=0, nullable=False, integer=False, exclusive=False):
        if value is None and nullable:
            return True
        valid = type(value) is int or (type(value) is float and math.isfinite(value))
        if integer:
            valid = valid and type(value) is int
        if not valid or value < minimum or (exclusive and value == minimum):
            problem(path, "must be a finite " + ("integer" if integer else "number") +
                    (" > " if exclusive else " >= ") + str(minimum))
            return False
        return True

    def choice(value, choices, path):
        if not isinstance(value, str) or value not in choices:
            problem(path, "must be one of " + ", ".join(choices))

    def character(value, path):
        c = obj(value, path, ("id", "asset_version", "gender", "age", "era", "identity_anchor",
                              "body", "appearance", "pose", "reference"), ("notes", "expression", "marks"))
        for key in ("id", "asset_version", "gender", "identity_anchor"):
            text(c.get(key), path + "." + key)
        if "notes" in c:
            text(c["notes"], path + ".notes")
        if "expression" in c:
            text(c["expression"], path + ".expression")
        if "marks" in c:
            marks = c["marks"]
            if not isinstance(marks, list):
                problem(path + ".marks", "must be an array")
                marks = []
            seen_marks = set()
            for index, value in enumerate(marks):
                label = path + ".marks[" + str(index) + "]"
                mark = obj(value, label, ("id", "side", "location", "description"))
                for key in ("id", "location", "description"):
                    text(mark.get(key), label + "." + key)
                ident = mark.get("id")
                if isinstance(ident, str):
                    if ident in seen_marks:
                        problem(label + ".id", "must be unique")
                    seen_marks.add(ident)
                choice(mark.get("side"), ("left", "right", "midline", "bilateral"), label + ".side")
        age = obj(c.get("age"), path + ".age", ("years", "appearance", "life_stage"))
        number(age.get("years"), path + ".age.years", nullable=True)
        text(age.get("appearance"), path + ".age.appearance")
        choice(age.get("life_stage"), ("unspecified", "infant", "child", "adolescent", "adult", "older_adult"), path + ".age.life_stage")
        era = obj(c.get("era"), path + ".era", ("setting", "culture", "accuracy", "source_urls"))
        for key in ("setting", "culture"):
            text(era.get(key), path + ".era." + key)
        choice(era.get("accuracy"), ("unspecified", "inspired", "verified"), path + ".era.accuracy")
        sources = strings(era.get("source_urls"), path + ".era.source_urls")
        if era.get("accuracy") == "verified":
            if not sources:
                problem(path + ".era.source_urls", "historical verification requires sources")
            for source in sources:
                if isinstance(source, str) and not source.startswith(("https://", "http://")):
                    problem(path + ".era.source_urls", "source must be an HTTP(S) URL")
            warnings.append(path + ".era: source presence is not historical verification; review the sources")
        body = obj(c.get("body"), path + ".body", ("description", "height_cm", "head_body_ratio", "proportion_mode"))
        text(body.get("description"), path + ".body.description")
        for key in ("height_cm", "head_body_ratio"):
            number(body.get(key), path + ".body." + key, nullable=True, exclusive=True)
        choice(body.get("proportion_mode"), ("natural", "reference", "explicit"), path + ".body.proportion_mode")
        if body.get("head_body_ratio") is not None and body.get("proportion_mode") != "explicit":
            problem(path + ".body.head_body_ratio", "numeric head/body ratio requires explicit mode; never invent a universal ratio")
        if body.get("proportion_mode") == "explicit" and body.get("head_body_ratio") is None:
            problem(path + ".body.head_body_ratio", "explicit mode requires a user-specified ratio")
        appearance = obj(c.get("appearance"), path + ".appearance", APPEARANCE_KEYS)
        for key in APPEARANCE_KEYS:
            text(appearance.get(key), path + ".appearance." + key)
        pose = obj(c.get("pose"), path + ".pose", ("posture", "description", "support"))
        choice(pose.get("posture"), ("standing", "seated", "supported_seated", "supported_reclining", "other"), path + ".pose.posture")
        text(pose.get("description"), path + ".pose.description")
        text(pose.get("support"), path + ".pose.support")
        if pose.get("posture") in ("supported_seated", "supported_reclining") and pose.get("support") in ("none", "无"):
            problem(path + ".pose.support", "supported poses require a described support")
        years = age.get("years")
        infant = age.get("life_stage") == "infant" or (type(years) in (int, float) and 0 <= years < 1)
        if infant and pose.get("posture") not in ("supported_seated", "supported_reclining"):
            problem(path + ".pose.posture", "infant plans require safe supported poses, not forced standing")
        if infant:
            warnings.append(path + ": review age-appropriate proportions, support, and occluded back anatomy; never remove support to expose a view")
        ref = obj(c.get("reference"), path + ".reference", ("mode", "assets", "visible_features", "unknown_features"))
        choice(ref.get("mode"), ("original", "identity", "style_only"), path + ".reference.mode")
        for key in ("assets", "visible_features", "unknown_features"):
            strings(ref.get(key), path + ".reference." + key)
        if ref.get("mode") in ("identity", "style_only") and not ref.get("assets"):
            problem(path + ".reference.assets", "reference mode requires a supplied asset identifier")
        if ref.get("mode") == "identity" and not ref.get("visible_features"):
            problem(path + ".reference.visible_features", "record observed identity evidence without inventing hidden features")
        if body.get("proportion_mode") == "reference" and ref.get("mode") != "identity":
            problem(path + ".body.proportion_mode", "reference proportions require an identity reference")
        return c

    p = obj(plan, "plan", ("schema_version", "request", "character", "sheet", "locks", "safety"), ("edit", "vocabulary"))
    if type(p.get("schema_version")) is not int or p["schema_version"] != 2:
        problem("schema_version", "must be integer 2")
    request = obj(p.get("request"), "request", ("text", "mode", "explicit_image_request"))
    text(request.get("text"), "request.text")
    choice(request.get("mode"), ("text", "image"), "request.mode")
    if type(request.get("explicit_image_request")) is not bool:
        problem("request.explicit_image_request", "must be boolean")
    if request.get("mode") == "image" and request.get("explicit_image_request") is not True:
        problem("request.mode", "image mode requires an explicit current image request")
    c = character(p.get("character"), "character")
    sheet = obj(p.get("sheet"), "sheet", ("layout", "width_px", "height_px", "aspect_ratio", "portrait_fraction",
                     "side", "background", "lighting", "same_identity", "same_costume", "same_pose", "views"))
    choice(sheet.get("layout"), ("portrait_front_side_back",), "sheet.layout")
    for key in ("background", "lighting"):
        text(sheet.get(key), "sheet." + key)
    w, h = sheet.get("width_px"), sheet.get("height_px")
    width_ok = number(w, "sheet.width_px", integer=True, exclusive=True)
    height_ok = number(h, "sheet.height_px", integer=True, exclusive=True)
    ratio = sheet.get("aspect_ratio")
    try:
        parts = ratio.split(":") if isinstance(ratio, str) else []
        if len(parts) != 2 or not all(s.isdecimal() for s in parts):
            raise ValueError()
        rw, rh = map(int, parts)
        if rw <= 0 or rh <= 0 or (width_ok and height_ok and w * rh != h * rw):
            raise ValueError()
    except ValueError:
        problem("sheet.aspect_ratio", "must be positive W:H matching pixel dimensions")
    fraction = sheet.get("portrait_fraction")
    if number(fraction, "sheet.portrait_fraction", exclusive=True) and fraction >= 1:
        problem("sheet.portrait_fraction", "must be < 1; remaining width is shared by three full-body panels")
    if width_ok and height_ok and w < h:
        warnings.append("sheet: a portrait canvas may crowd four columns; review face detail and full-body proportions")
    choice(sheet.get("side"), ("left", "right"), "sheet.side")
    for key in ("same_identity", "same_costume", "same_pose"):
        if sheet.get(key) is not True:
            problem("sheet." + key, "must be true")
    views = sheet.get("views")
    if not isinstance(views, list) or len(views) != 4:
        problem("sheet.views", "must contain exactly portrait, front, side, back in this order")
        views = []
    full_views = []
    for i, value in enumerate(views):
        path = "sheet.views[" + str(i) + "]"
        view = obj(value, path, ("id", "framing", "angle_degrees", "character_id", "asset_version", "scale", "baseline"))
        expected_id = VIEW_IDS[i]
        if view.get("id") != expected_id:
            problem(path + ".id", "must be " + expected_id)
        expected_framing = "head_to_clavicle" if i == 0 else "full_body"
        if view.get("framing") != expected_framing:
            problem(path + ".framing", "must be " + expected_framing)
        expected_angle = (0, 0, 90, 180)[i]
        if type(view.get("angle_degrees")) is not int or view["angle_degrees"] != expected_angle:
            problem(path + ".angle_degrees", "must be " + str(expected_angle))
        for key, target in (("character_id", "id"), ("asset_version", "asset_version")):
            if not equal(view.get(key), c.get(target)):
                problem(path + "." + key, "must match character." + target)
        if i == 0:
            if view.get("scale") is not None or view.get("baseline") is not None:
                problem(path, "portrait has its own crop; scale and baseline must be null")
        else:
            number(view.get("scale"), path + ".scale", exclusive=True)
            baseline = view.get("baseline")
            if number(baseline, path + ".baseline", exclusive=True) and baseline >= 1:
                problem(path + ".baseline", "must be < 1 in normalized panel coordinates")
            full_views.append(view)
    if len(full_views) == 3:
        for key in ("scale", "baseline"):
            if not all(equal(full_views[0].get(key), v.get(key)) for v in full_views[1:]):
                problem("sheet.views", "full-body " + key + " must be identical")
    locks = p.get("locks")
    if not isinstance(locks, dict):
        problem("locks", "must be an object mapping existing dotted paths to exact values")
    else:
        for path, value in locks.items():
            actual = resolve(p, path)
            if not isinstance(path, str) or not path.startswith(("character.", "sheet.")) or actual is MISSING:
                problem("locks", "unknown or disallowed path " + repr(path))
            elif not equal(actual, value):
                problem("locks." + path, "lock violation")
        if resolve(c, "reference.mode") == "identity" and "character.identity_anchor" not in locks:
            problem("locks", "identity reference requires character.identity_anchor lock")
    try:
        catalog = read_vocabulary()
        entries = {t["id"]: t for t in catalog["terms"]}
        selection = obj(p.get("vocabulary", {}), "vocabulary", (), ("include", "exclude"))
        selected = {}
        for key in ("include", "exclude"):
            values = strings(selection.get(key, []), "vocabulary." + key)
            values = [x for x in values if isinstance(x, str)]
            if len(values) != len(set(values)):
                problem("vocabulary." + key, "duplicate term")
            for ident in values:
                if ident not in entries:
                    problem("vocabulary." + key, "unknown term " + ident)
                elif key == "include" and not eligible(entries[ident], p):
                    problem("vocabulary.include", "term not applicable to character: " + ident)
            selected[key] = set(values)
        if selected["include"] & selected["exclude"]:
            problem("vocabulary", "a term cannot be both included and excluded")
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        problem("vocabulary", "catalog unavailable or invalid: " + str(exc))
    safety = obj(p.get("safety"), "safety", ("age_appropriate", "non_sexual"))
    for key in ("age_appropriate", "non_sexual"):
        if safety.get(key) is not True:
            problem("safety." + key, "must be true for neutral costume reference sheets")
    if "edit" in p:
        edit = obj(p["edit"], "edit", ("baseline_character", "allowed_paths"))
        baseline = character(edit.get("baseline_character"), "edit.baseline_character")
        allowed = strings(edit.get("allowed_paths"), "edit.allowed_paths")
        allowed = [x for x in allowed if isinstance(x, str) and x]
        for path in allowed:
            if path == "id" or (resolve(c, path) is MISSING and resolve(baseline, path) is MISSING):
                problem("edit.allowed_paths", "invalid or identity-changing path " + repr(path))
        for path in changed_paths(baseline, c):
            if not any(path == item or path.startswith(item + ".") for item in allowed):
                problem("edit." + path, "changed outside allowed_paths")
        if not equal(c.get("id"), baseline.get("id")):
            problem("edit.character.id", "character identity ID must remain unchanged")
        if changed_paths(baseline, c) and c.get("asset_version") == baseline.get("asset_version"):
            warnings.append("edit: advance asset_version and update every view when approving a changed design")
    return {"status": "FAIL" if errors else "PASS", "errors": errors, "warnings": warnings,
            "pairs": [], "image_review": "UNVERIFIED",
            "scope": "encoded plan only; authorization, age/era semantics, identity and pixels require separate review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()
    try:
        result = check(load_plan(args.plan))
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        result = {"status": "FAIL", "errors": ["Invalid input: " + str(exc)], "image_review": "UNVERIFIED"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
