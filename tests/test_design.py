import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
checker = module("check_design")
exporter = module("export_gpt")
def person(name="A", variant=0):
    return {"id": name, "axes": {k: vals[variant % len(vals)] for k, vals in checker.AXES.items()},
            "makeup": {"palette": "peach", "finish": "satin", "direction": "level", "placement": "central cheeks"}}
def plan():
    return {"schema_version": 1, "request": {"text": "Design different characters", "mode": "text",
            "explicit_image_request": False}, "roster_goal": "distinct", "same_makeup": True,
            "characters": [person("A"), person("B", 1), person("C", 2)]}
class DesignTests(unittest.TestCase):
    def test_distinct_all_pairs_and_uniform_makeup(self):
        result = checker.check(plan())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["pairs"]), 3)
    def test_only_decorations_cannot_make_different_faces(self):
        p = plan()
        p["characters"][1]["axes"] = copy.deepcopy(p["characters"][0]["axes"])
        p["characters"][1].update(skin="deep", hair="short", marker="mole")
        self.assertEqual(checker.check(p)["status"], "FAIL")
    def test_all_pairs_not_only_first(self):
        p = plan()
        p["characters"][2]["axes"] = copy.deepcopy(p["characters"][1]["axes"])
        r = checker.check(p)
        self.assertTrue(any("B/C" in x for x in r["errors"]))
    def test_many_eye_changes_are_one_group(self):
        p = plan()
        p["characters"] = [person("A"), person("B")]
        for k in p["characters"][1]["axes"]:
            if k.startswith("eyes."):
                p["characters"][1]["axes"][k] = checker.AXES[k][1]
        r = checker.check(p)
        self.assertEqual(r["pairs"][0]["groups"], ["eyes"])
        self.assertEqual(r["status"], "FAIL")
    def test_four_groups_require_two_core_groups(self):
        p = plan()
        p["characters"] = [person("A"), person("B")]
        for k in p["characters"][1]["axes"]:
            if k.split(".")[0] in ("jaw", "eyes", "lips", "brows"):
                p["characters"][1]["axes"][k] = checker.AXES[k][1]
        r = checker.check(p)
        self.assertEqual(len(r["pairs"][0]["groups"]), 4)
        self.assertEqual(r["status"], "FAIL")
    def test_lock_and_identity_changes_fail(self):
        p = plan()
        p["locks"] = {"jaw.chin": "round"}
        self.assertTrue(any("lock violation" in e for e in checker.check(p)["errors"]))
        p = plan()
        p["roster_goal"] = "identity"
        p["reference_axes"] = copy.deepcopy(p["characters"][0]["axes"])
        self.assertEqual(checker.check(p)["status"], "FAIL")
        p["characters"] = [p["characters"][0]]
        self.assertEqual(checker.check(p)["status"], "PASS")
    def test_generation_is_optional_and_explicit(self):
        p = plan()
        p["request"]["mode"] = "image"
        self.assertEqual(checker.check(p)["status"], "FAIL")
        p["request"]["explicit_image_request"] = True
        self.assertEqual(checker.check(p)["status"], "PASS")
    def test_makeup_and_input_contracts(self):
        p = plan()
        p["characters"][1]["makeup"]["direction"] = "up"
        self.assertEqual(checker.check(p)["status"], "FAIL")
        for value in (None, [], {"characters": [None]}, {"characters": "bad"}):
            self.assertEqual(checker.check(value)["status"], "FAIL")
    def test_unknown_missing_array_and_duplicate_axes(self):
        for value in ("synonym", ["short", "long"], None):
            p = plan()
            p["characters"][0]["axes"]["face.ratio"] = value
            self.assertEqual(checker.check(p)["status"], "FAIL")
        p = plan()
        del p["characters"][0]["axes"]["nose.width"]
        self.assertEqual(checker.check(p)["status"], "FAIL")
        p["characters"][0]["axes"]["bone"] = "sharp"
        self.assertEqual(checker.check(p)["status"], "FAIL")
        with self.assertRaises(ValueError):
            json.loads('{"face.ratio":"short","face.ratio":"long"}', object_pairs_hook=checker.unique_keys)
    def test_partial_reference_and_related_roster(self):
        p = plan()
        p.update(roster_goal="single", same_makeup=False, characters=[{"id": "A", "axes": {}}])
        self.assertEqual(checker.check(p)["status"], "PASS")
        p.update(roster_goal="related", characters=[person("A"), person("B")])
        self.assertEqual(checker.check(p)["status"], "PASS")
    def test_source_derived_export_and_enabled_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            exporter.export(tmp)
            out = Path(tmp)
            config = json.loads((out / "app-config.json").read_text())
            self.assertTrue(config["capabilities"]["image_generation"])
            instructions = (out / "instructions.txt").read_text()
            self.assertLessEqual(len(instructions), 8000)
            for name in exporter.RULES:
                self.assertIn((ROOT / name).read_text().strip(), instructions)
            manifest = json.loads((out / "export-manifest.json").read_text())
            for name, digest in manifest["output_sha256"].items():
                self.assertEqual(exporter.sha((out / name).read_bytes()), digest)
        with self.assertRaises(ValueError):
            exporter.export(ROOT / "dist")
if __name__ == "__main__":
    unittest.main()
