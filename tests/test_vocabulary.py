import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts import check_turnaround as checker
from scripts import build_prompt as builder
from scripts import randomized_smoke as randomized
from scripts import export_gpt as exporter


def plan(name="turnaround-plan.json"):
    return checker.load_plan(ROOT / "examples" / name)


class VocabularyTests(unittest.TestCase):
    def test_catalog_is_valid_unique_and_nonempty(self):
        c=checker.read_vocabulary()
        self.assertEqual(len(c["terms"]),25)
        self.assertEqual(len({t["id"] for t in c["terms"]}),25)

    def test_character_terms_never_default(self):
        c=checker.read_vocabulary()
        self.assertTrue(all(t["id"] not in c["default_ids"] for t in c["terms"] if t["scope"]=="character"))

    def test_original_lexicon_preserved_and_extension_linked(self):
        text=(ROOT/"references/lexicon.md").read_text()
        for heading in ("## 01 脸型与比例","## 17 妆发辅助","四视图摄影与全身词表扩展"):
            self.assertIn(heading,text)
        self.assertIn("turnaround-lexicon.json",text)

    def test_unknown_and_duplicate_term_fail(self):
        for ids in (["made.up"],["photo.realism","photo.realism"]):
            p=plan();p["vocabulary"]={"include":ids}
            self.assertEqual(checker.check(p)["status"],"FAIL")

    def test_wrong_vocabulary_types_fail_cleanly(self):
        for v in ([],None,True,{"include":"skin.microtexture"},{"include":[{}]},{"typo":[]}):
            p=plan();p["vocabulary"]=v
            self.assertEqual(checker.check(p)["status"],"FAIL")

    def test_include_exclude_conflict(self):
        p=plan();p["vocabulary"]={"include":["photo.realism"],"exclude":["photo.realism"]}
        self.assertEqual(checker.check(p)["status"],"FAIL")

    def test_adult_specific_terms_rejected_for_child(self):
        p=plan("turnaround-child.json");p["vocabulary"]={"include":["laborer.lean_strength"]}
        self.assertTrue(any("not applicable" in e for e in checker.check(p)["errors"]))

    def test_unspecified_age_not_assumed_adult(self):
        p=plan();p["character"]["age"]={"years":None,"life_stage":"unspecified","appearance":"未指定"}
        p["vocabulary"]={"include":["skin.weathered_dust"]}
        self.assertEqual(checker.check(p)["status"],"FAIL")

    def test_excluded_term_not_rendered(self):
        p=plan();p["vocabulary"]={"exclude":["hair.continuity"]}
        text=builder.render(p)
        entry=next(t for t in checker.read_vocabulary()["terms"] if t["id"]=="hair.continuity")
        self.assertNotIn(entry["text"],text)
        self.assertIn(p["character"]["appearance"]["hair"],text)

    def test_specific_preset_not_leaked(self):
        for name in ("turnaround-child.json","turnaround-elder.json","turnaround-future.json"):
            text=builder.render(plan(name))
            for forbidden in ("188","9 头身","粗亚麻短袍","仅此风霜角色"):
                self.assertNotIn(forbidden,text)

    def test_myth_preset_preserves_given_constraints(self):
        p=plan("myth-laborer-188.json")
        self.assertEqual(checker.check(p)["status"],"PASS")
        text=builder.render(p)
        for value in ("188 厘米","9 头身","自身左侧的脸颊","米灰色粗亚麻短袍","双脚赤足","不怒吼"):
            self.assertIn(value,text)
        self.assertIsNone(p["character"]["age"]["years"])

    def test_marks_side_must_be_valid(self):
        p=plan("myth-laborer-188.json");p["character"]["marks"][0]["side"]="screen-left"
        self.assertEqual(checker.check(p)["status"],"FAIL")

    def test_mark_side_drift_breaks_lock(self):
        p=plan("myth-laborer-188.json");p["character"]["marks"][0]["side"]="right"
        self.assertTrue(any("lock violation" in e for e in checker.check(p)["errors"]))

    def test_duplicate_or_wrong_marks_fail(self):
        for val in ("scar",[None],[{"id":"missing"}]):
            p=plan();p["character"]["marks"]=val
            self.assertEqual(checker.check(p)["status"],"FAIL")
        p=plan("myth-laborer-188.json");p["character"]["marks"]*=2
        self.assertEqual(checker.check(p)["status"],"FAIL")

    def test_expression_lock(self):
        p=plan("myth-laborer-188.json");p["character"]["expression"]="露齿大笑"
        self.assertTrue(any("lock violation" in e for e in checker.check(p)["errors"]))

    def test_portrait_does_not_demand_feet(self):
        for p in (plan(),plan("myth-laborer-188.json")):
            text=builder.render(p,"portrait")
            self.assertIn("不要求手脚入画",text)
            for forbidden in ("脚部裁切","head to toe","全身采用中长焦"):
                self.assertNotIn(forbidden,text)

    def test_profile_allows_natural_occlusion(self):
        self.assertIn("远侧手脚被身体自然遮挡",builder.render(plan(),"side"))

    def test_infant_never_forced_into_standing_terms(self):
        p=plan("turnaround-infant.json")
        ids=[t["id"] for t in checker.selected_terms(p)]
        self.assertNotIn("standing.neutral",ids)
        self.assertNotIn("back.no_turn",ids)
        self.assertIn("PARTIAL",builder.render(p))

    def test_natural_and_explicit_ratio_are_exclusive(self):
        for name,want,unwanted in (("turnaround-plan.json","body.natural","body.explicit_ratio"),("myth-laborer-188.json","body.explicit_ratio","body.natural")):
            ids=[t["id"] for t in checker.selected_terms(plan(name))]
            self.assertIn(want,ids);self.assertNotIn(unwanted,ids)

    def test_negative_terms_deduplicated(self):
        words=builder.negative_prompt(plan("myth-laborer-188.json")).split("，")
        self.assertEqual(len(words),len(set(words)))

    def test_positive_only_excludes_negative_section(self):
        text=builder.render(plan(),include_negative=False)
        self.assertNotIn("【负向提示词】",text)
        self.assertIn("【人物身份与面部】",text)

    def test_natural_short_limbs_not_universally_forbidden(self):
        text=builder.negative_prompt(plan("turnaround-infant.json"))
        self.assertNotIn("大头短身",text)
        self.assertNotIn("短腿",text)
        self.assertIn("与角色年龄不符",text)

    def test_cli_negative_only(self):
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/build_prompt.py"),str(ROOT/"examples/turnaround-plan.json"),"--view","portrait","--negative-only"],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertNotIn("【人物身份",proc.stdout)
        self.assertNotIn("脚部裁切",proc.stdout)

    def test_random_generation_reproducible_and_seed_sensitive(self):
        a=randomized.make_plans(20260925,24)
        self.assertEqual(a,randomized.make_plans(20260925,24))
        self.assertNotEqual(a,randomized.make_plans(20260926,24))
        self.assertEqual(len({p["character"]["id"] for p in a}),24)
        self.assertEqual(len({p["character"]["age"]["life_stage"] for p in a}),6)

    def test_seeded_regression(self):
        r=randomized.run(20260925,24)
        self.assertEqual(r["status"],"PASS")
        self.assertEqual(r["prompt_count"],120)
        self.assertEqual(r["rejected_mutations"],192)
        self.assertTrue(all(c["image_review"]=="UNVERIFIED" for c in r["cases"]))

    def test_random_invalid_counts(self):
        for count in (0,-1,1001,True,"24"):
            with self.assertRaises(ValueError):randomized.make_plans(count=count)

    def test_random_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/"keep.txt").write_text("keep")
            with self.assertRaises(ValueError):randomized.run(count=1,out=tmp)
            self.assertEqual((Path(tmp)/"keep.txt").read_text(),"keep")

    def test_export_contains_machine_vocabulary_and_version(self):
        files=exporter.render()
        self.assertIn("laborer.lean_strength",files["knowledge-lexicon.md"])
        self.assertEqual(json.loads(files["export-manifest.json"])["skill_version"],"0.3.1")
        self.assertLessEqual(len(files["instructions.txt"]),8000)


if __name__=="__main__":unittest.main()
