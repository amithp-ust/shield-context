import contextlib
import copy
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.documents = {
            name: validate.load(name) for name in (
                "context/component-map.yaml", "context/glossary.yaml",
                "context/scope.yaml", "i2s.profile.yaml",
            )
        }

    def check(self):
        with patch.object(validate, "load", side_effect=self.documents.__getitem__):
            with contextlib.redirect_stdout(io.StringIO()):
                validate.validate()

    def test_unconfigured_profile_is_valid_metadata_not_model_approval(self):
        self.check()
        profile = self.documents["i2s.profile.yaml"]
        self.assertEqual(profile["judge"]["model"], "unconfigured")
        self.assertEqual(profile["judge"]["cli_version"], "")
        self.assertEqual(profile["model_policy"]["approved_judges"], [])
        self.assertEqual(profile["model_policy"]["approved_session_models"], [])
        self.assertEqual(profile["tool_review"]["status"], "unconfirmed")

    def test_rejects_missing_names_owners_and_status(self):
        original = copy.deepcopy(self.documents)
        for filename, collection, field in (
            ("context/component-map.yaml", "components", "name"),
            ("context/glossary.yaml", "terms", "owner"),
            ("context/glossary.yaml", "terms", "status"),
        ):
            with self.subTest(field=field):
                self.documents = copy.deepcopy(original)
                self.documents[filename][collection][0][field] = ""
                with self.assertRaises(ValueError):
                    self.check()

    def test_canonical_specs_repository_is_declared(self):
        self.check()
        profile = self.documents["i2s.profile.yaml"]
        self.assertEqual(profile["specs_repo"], "amithp-ust/Intent-to-spec")
        self.assertEqual(profile["context_repo"], "amithp-ust/shield-context")
        self.assertNotIn("app_repo", profile)

    def test_rejects_missing_or_noncanonical_specs_repository(self):
        profile = self.documents["i2s.profile.yaml"]
        profile.pop("specs_repo")
        with self.assertRaisesRegex(ValueError, "specs_repo must be"):
            self.check()
        for repository in (
            "", None, "Intent-to-spec", "other/Intent-to-spec",
            "amithp-ust/shield-policy-service", "amithp-ust/shield-context",
        ):
            with self.subTest(repository=repository):
                profile["specs_repo"] = repository
                with self.assertRaisesRegex(ValueError, "specs_repo must be"):
                    self.check()

    def test_rejects_replacing_context_source(self):
        self.documents["i2s.profile.yaml"]["context_repo"] = "amithp-ust/Intent-to-spec"
        with self.assertRaisesRegex(ValueError, "context_repo must remain"):
            self.check()

    def test_rejects_moving_component_ownership_to_specs_repository(self):
        self.documents["context/component-map.yaml"]["components"][0]["repo"] = "Intent-to-spec"
        with self.assertRaisesRegex(ValueError, "Component ownership must remain"):
            self.check()

    def test_rejects_missing_fraud_dependency(self):
        fraud = next(c for c in self.documents["context/component-map.yaml"]["components"]
                     if c["id"] == "CM-FRAUD")
        fraud["depends_on"] = []
        with self.assertRaisesRegex(ValueError, "SQL-view dependency"):
            self.check()

    def test_rejects_unapproved_model(self):
        self.documents["i2s.profile.yaml"]["judge"]["model"] = "not-approved"
        with self.assertRaisesRegex(ValueError, "must be approved"):
            self.check()

    def test_regulations_remain_unverified_with_provenance(self):
        scope = self.documents["context/scope.yaml"]
        self.check()
        for regulation in scope["regulations"]:
            self.assertEqual(regulation["status"], "unverified")
            self.assertIn("candidate", regulation["source"])
            self.assertIn("prior_id", scope["regulation_provenance"][regulation["id"]])

    def test_rejects_cli_version_as_backend_version(self):
        self.documents["i2s.profile.yaml"]["judge"]["version"] = "1.2.3"
        with self.assertRaisesRegex(ValueError, "CLI version"):
            self.check()


if __name__ == "__main__":
    unittest.main()
