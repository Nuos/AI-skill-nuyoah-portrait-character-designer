import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import check_turnaround as checker
from scripts import build_prompt as builder
from scripts import build_manifest as manifest
from scripts import export_gpt as exporter


def plan():
    return checker.load_plan(ROOT / "examples" / "turnaround-plan.json")


class TurnaroundTests(unittest.TestCase):
    def assert_invalid(self, value, fragment=None):
        result = checker.check(value)
        self.assertEqual(result["status"], "FAIL", result)
        if fragment:
            self.assertTrue(any(fragment in e for e in result["errors"]), result)

    def test_supported_pose_does_not_require_visible_occluded_back(self):
        p = checker.load_plan(ROOT / "examples" / "turnaround-infant.json")
        text = builder.render(p, "back")
        self.assertIn("保留必要支撑及自然遮挡", text)
        self.assertIn("PARTIAL", text)

    def test_examples_pass_with_images_unverified(self):
        files = list((ROOT / "examples").glob("turnaround-*.json"))
        self.assertEqual(len(files), 6)
        for file in files:
            with self.subTest(file=file.name):
                result = checker.check(checker.load_plan(file))
                self.assertEqual(result["status"], "PASS", result)
                self.assertEqual(result["image_review"], "UNVERIFIED")

    def test_gender_age_era_are_not_admission_gates(self):
        for gender in ("男性", "女性", "非二元", "未指定", "用户自定义性别描述"):
            for age in (None, 8, 16, 38, 82, 140):
                for era in ("古代", "近现代", "当代", "未来", "神话", "架空", "未指定"):
                    p = plan()
                    p["character"].update(gender=gender, age={"years": age, "appearance": "用户明确的年龄外观", "life_stage": "unspecified"})
                    p["character"]["era"]["setting"] = era
                    self.assertEqual(checker.check(p)["status"], "PASS")

    def test_optional_age_height_and_ratio_not_invented(self):
        p = plan(); p["character"]["age"]["years"] = None
        before = copy.deepcopy(p)
        text = builder.render(p)
        self.assertEqual(p, before)
        self.assertIsNone(p["character"]["body"]["height_cm"])
        self.assertIsNone(p["character"]["body"]["head_body_ratio"])
        self.assertNotIn("9 头身", text)
        self.assertNotIn("角色设定身高", text)

    def test_bad_roots_fail_without_exceptions(self):
        for value in (None, [], "bad", 2, True, {}):
            with self.subTest(value=value):
                self.assert_invalid(value)

    def test_required_nested_fields(self):
        for path in ("request", "character", "character.age", "character.body", "character.reference", "sheet", "sheet.views", "locks", "safety"):
            p = plan(); target = p
            parts = path.split(".")
            for key in parts[:-1]: target = target[key]
            del target[parts[-1]]
            self.assert_invalid(p)

    def test_unknown_fields_fail(self):
        for path in ("", "character", "character.age", "sheet", "request"):
            p = plan(); target = p if not path else checker.resolve(p, path)
            target["typo_field"] = "ignored?"
            self.assert_invalid(p, "unknown field")

    def test_wrong_nested_types_fail(self):
        for path in ("character.age", "character.pose", "character.appearance", "character.reference", "sheet.views", "request", "locks", "safety"):
            for bad in (None, "bad", 3, False, []):
                p=plan(); parts=path.split("."); target=p
                for key in parts[:-1]: target=target[key]
                target[parts[-1]]=bad
                self.assert_invalid(p)

    def test_image_requires_explicit_authorization(self):
        p = plan(); p["request"]["mode"] = "image"
        self.assert_invalid(p, "explicit current")
        p["request"]["explicit_image_request"] = True
        self.assertEqual(checker.check(p)["status"], "PASS")

    def test_authorization_must_be_boolean(self):
        for value in (1, "true", None):
            p = plan(); p["request"]["explicit_image_request"] = value
            self.assert_invalid(p, "boolean")

    def test_bool_is_not_schema_or_number(self):
        p = plan(); p["schema_version"] = True; self.assert_invalid(p)
        for key in ("height_cm", "head_body_ratio"):
            p = plan(); p["character"]["body"][key] = True
            self.assert_invalid(p)
        p = plan(); p["sheet"]["width_px"] = True; self.assert_invalid(p)

    def test_invalid_finite_and_negative_numbers(self):
        for bad in (-1, float("nan"), float("inf"), "70", [], {}):
            p = plan(); p["character"]["age"]["years"] = bad
            self.assert_invalid(p)

    def test_large_integer_does_not_crash(self):
        p = plan(); p["character"]["body"]["height_cm"] = 10 ** 400
        self.assertEqual(checker.check(p)["status"], "PASS")
        # This is a validator robustness test, not a physically plausible person.

    def test_no_global_numeric_ratio(self):
        p = plan(); p["character"]["body"]["head_body_ratio"] = 9
        self.assert_invalid(p, "explicit mode")
        p["character"]["body"]["proportion_mode"] = "explicit"
        self.assertEqual(checker.check(p)["status"], "PASS")
        self.assertIn("9 头身", builder.render(p))

    def test_explicit_ratio_must_exist(self):
        p = plan(); p["character"]["body"]["proportion_mode"] = "explicit"
        self.assert_invalid(p, "requires a user-specified ratio")

    def test_infant_requires_support(self):
        p = plan(); p["character"]["age"] = {"years": 0.5, "appearance": "六个月婴儿", "life_stage": "infant"}
        self.assert_invalid(p, "safe supported poses")
        p["character"]["pose"] = {"posture": "supported_reclining", "description": "安全受托仰卧", "support": "宽阔稳定承托垫，支持头颈躯干"}
        result = checker.check(p)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["warnings"])

    def test_supported_pose_cannot_have_no_support(self):
        p = plan(); p["character"]["pose"]["posture"] = "supported_seated"
        self.assert_invalid(p, "described support")

    def test_historical_verified_requires_sources(self):
        p = plan(); p["character"]["era"]["accuracy"] = "verified"
        self.assert_invalid(p, "requires sources")
        p["character"]["era"]["source_urls"] = ["https://example.invalid/fixture-only"]
        result = checker.check(p)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(any("not historical verification" in w for w in result["warnings"]))

    def test_reference_requires_real_input_declarations(self):
        p = plan(); p["character"]["reference"]["mode"] = "identity"
        self.assert_invalid(p, "supplied asset")
        p["character"]["reference"].update(assets=["TEST_FIXTURE_NOT_A_REAL_IMAGE"], visible_features=["测试记录，不代表实际观察"])
        self.assertEqual(checker.check(p)["status"], "PASS")
        p["locks"] = {}
        self.assert_invalid(p, "identity_anchor lock")

    def test_reference_proportions_require_identity_reference(self):
        p = plan(); p["character"]["body"]["proportion_mode"] = "reference"
        self.assert_invalid(p, "identity reference")

    def test_four_views_exact_number(self):
        for count in (0, 1, 3, 5):
            p = plan(); p["sheet"]["views"] = [p["sheet"]["views"][0]] * count
            self.assert_invalid(p, "exactly")

    def test_view_order_and_framing(self):
        p = plan(); p["sheet"]["views"][0]["framing"] = "full_body"
        self.assert_invalid(p, "head_to_clavicle")
        p = plan(); p["sheet"]["views"].reverse()
        self.assert_invalid(p)

    def test_angles_are_strict(self):
        for index in (0, 1, 2, 3):
            p = plan(); p["sheet"]["views"][index]["angle_degrees"] = 45
            self.assert_invalid(p, "angle_degrees")
        p = plan(); p["sheet"]["views"][0]["angle_degrees"] = False
        self.assert_invalid(p)

    def test_left_right_profile_wording(self):
        p = plan(); text = builder.render(p, "side")
        self.assertIn("自身左侧", text); self.assertIn("鼻尖朝画面左方", text)
        p["sheet"]["side"] = "right"; text = builder.render(p, "side")
        self.assertIn("自身右侧", text); self.assertIn("鼻尖朝画面右方", text)
        p["sheet"]["side"] = "both"; self.assert_invalid(p)

    def test_same_identity_and_version_every_view(self):
        for key in ("character_id", "asset_version"):
            p = plan(); p["sheet"]["views"][2][key] = "OTHER"
            self.assert_invalid(p, "must match")

    def test_same_scale_and_baseline(self):
        for key in ("scale", "baseline"):
            p = plan(); p["sheet"]["views"][2][key] = 0.8
            self.assert_invalid(p, "must be identical")

    def test_portrait_not_subject_to_full_body_scale(self):
        p = plan(); p["sheet"]["views"][0]["scale"] = 1
        self.assert_invalid(p, "own crop")

    def test_same_costume_and_pose_required(self):
        for key in ("same_identity", "same_costume", "same_pose"):
            for value in (False, 1, "true"):
                p = plan(); p["sheet"][key] = value
                self.assert_invalid(p, "must be true")

    def test_canvas_ratio_matches_dimensions(self):
        for ratio in ("4:3", "0:9", "16:0", "16/9", "", "nan:9", "16:9:1", None):
            p = plan(); p["sheet"]["aspect_ratio"] = ratio
            self.assert_invalid(p, "aspect_ratio")
        p = plan(); p["sheet"].update(width_px=2048,height_px=1152)
        self.assertEqual(checker.check(p)["status"], "PASS")

    def test_portrait_fraction_open_interval(self):
        for value in (0, 1, -0.2, 1.1, True, None):
            p = plan(); p["sheet"]["portrait_fraction"] = value
            self.assert_invalid(p)

    def test_locks_are_typed_existing_paths(self):
        p = plan(); p["locks"]["character.body.height_cm"] = 190
        self.assert_invalid(p, "lock violation")
        p = plan(); p["locks"]["character.typo"] = "x"
        self.assert_invalid(p, "unknown or disallowed")
        p = plan(); p["locks"]["request.mode"] = "text"
        self.assert_invalid(p, "disallowed")

    def test_edit_allows_costume_only(self):
        p = plan(); before = copy.deepcopy(p["character"])
        p["edit"] = {"baseline_character": before, "allowed_paths": ["appearance.costume"]}
        p["character"]["appearance"]["costume"] = "另一套无品牌完整服装"
        self.assertEqual(checker.check(p)["status"], "PASS")
        p["character"]["age"]["years"] = 25
        self.assert_invalid(p, "outside allowed_paths")

    def test_edit_rejects_unpermitted_face_and_body_changes(self):
        for path in ("identity_anchor", "body.description", "appearance.skin", "appearance.hair"):
            p=plan(); before=copy.deepcopy(p["character"])
            p["edit"]={"baseline_character":before,"allowed_paths":["appearance.costume"]}
            target=p["character"]; parts=path.split(".")
            for key in parts[:-1]: target=target[key]
            target[parts[-1]]="unapproved change"
            self.assert_invalid(p)

    def test_edit_version_and_identity(self):
        p=plan(); before=copy.deepcopy(p["character"])
        p["edit"]={"baseline_character":before,"allowed_paths":["asset_version"]}
        p["character"]["asset_version"]="v0.2.0"
        for view in p["sheet"]["views"]: view["asset_version"]="v0.2.0"
        self.assertEqual(checker.check(p)["status"],"PASS")
        p["edit"]["allowed_paths"].append("id")
        self.assert_invalid(p,"identity-changing")

    def test_malformed_edit_baseline(self):
        p=plan();p["edit"]={"baseline_character":[],"allowed_paths":"appearance.costume"}
        self.assert_invalid(p)

    def test_safety_declarations_not_optional(self):
        for key in ("age_appropriate", "non_sexual"):
            p=plan();p["safety"][key]=False
            self.assert_invalid(p)

    def test_compiler_repeats_full_anchor_in_each_view(self):
        p=plan()
        for view in ("sheet","portrait","front","side","back"):
            text=builder.render(p,view)
            self.assertIn(p["character"]["identity_anchor"],text)
            for value in p["character"]["appearance"].values(): self.assertIn(value,text)
            if view!="sheet": self.assertNotIn("横向四列",text)
            self.assertNotIn("其它同上",text)

    def test_compiler_rejects_invalid_plans_and_views(self):
        with self.assertRaises(ValueError): builder.render({})
        with self.assertRaises(ValueError): builder.render(plan(),"unknown")

    def test_duplicate_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"bad.json"
            for raw in ('{"schema_version":2,"schema_version":1}', '{"x":NaN}', '{"x":Infinity}'):
                path.write_text(raw)
                with self.assertRaises(ValueError): checker.load_plan(path)

    def test_v2_dispatch_works_with_original_import_style(self):
        spec=importlib.util.spec_from_file_location("standalone_checker",ROOT/"scripts/check_design.py")
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.assertEqual(module.check(plan())["status"],"PASS")

    def test_cli_from_other_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc=subprocess.run([sys.executable,str(ROOT/"scripts/check_design.py"),str(ROOT/"examples/turnaround-plan.json")],cwd=tmp,capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["status"],"PASS")
            proc=subprocess.run([sys.executable,str(ROOT/"scripts/build_prompt.py"),str(ROOT/"examples/turnaround-plan.json"),"--view","side"],cwd=tmp,capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            self.assertIn("标准侧面全身",proc.stdout)

    def test_cli_bad_input_clean_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"bad.json";path.write_text('{"schema_version":2,"character":null}')
            for script in ("check_design.py","check_turnaround.py","build_prompt.py"):
                proc=subprocess.run([sys.executable,str(ROOT/"scripts"/script),str(path)],capture_output=True,text=True)
                self.assertEqual(proc.returncode,1)
                self.assertNotIn("Traceback",proc.stdout+proc.stderr)

    def test_export_has_four_view_and_age_rules(self):
        files=exporter.render()
        self.assertIn("schema_version=2",files["instructions.txt"])
        self.assertIn("不默认年轻、女性、成年人",files["instructions.txt"])
        self.assertIn("标准侧面",files["instructions.txt"])
        self.assertLessEqual(len(files["instructions.txt"]),8000)

    def test_export_refuses_symlink_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/"keep.txt";source.write_text("keep")
            out=root/"out";out.mkdir();(out/"instructions.txt").symlink_to(source)
            with self.assertRaises(ValueError): exporter.export(out)
            self.assertEqual(source.read_text(),"keep")

    def test_manifest_deterministic_and_sensitive_to_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"README.md").write_text("first")
            a=manifest.render(root);b=manifest.render(root)
            self.assertEqual(a,b)
            (root/"README.md").write_text("second")
            self.assertNotEqual(a["releaseDigest"],manifest.render(root)["releaseDigest"])
            (root/"manifest.json").write_text("not hashed")
            self.assertEqual(len(manifest.inventory(root)),1)

    def test_manifest_refuses_source_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/"outside.txt").write_text("x");(root/"README.md").symlink_to(root/"outside.txt")
            with self.assertRaises(ValueError): manifest.inventory(root)


if __name__ == "__main__":
    unittest.main()
