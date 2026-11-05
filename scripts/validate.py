"""Validate Shield context and, optionally, sibling component contracts."""

import argparse
import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate as validate_openapi


ROOT = Path(__file__).resolve().parents[1]
SPECS_REPOSITORY = "amithp-ust/Intent-to-spec"
COMPONENT_REPOSITORIES = {
    "CM-POLICY": "shield-policy-service",
    "CM-UW-RULES": "shield-underwriting-rules",
    "CM-CLAIMS": "shield-claims-service",
    "CM-FRAUD": "shield-fraud-scoring",
    "CM-BILLING": "shield-billing-service",
    "CM-PORTAL": "shield-customer-portal",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(relative):
    with (ROOT / relative).open() as source:
        value = yaml.safe_load(source)
    require(isinstance(value, dict), f"{relative}: expected a mapping")
    require(value.get("schema_version") == 1, f"{relative}: unsupported schema")
    return value


def unique_ids(entries, label):
    values = [entry["id"] for entry in entries]
    require(len(values) == len(set(values)), f"{label}: duplicate IDs")
    return set(values)


def validate(repos_root=None, schemas_root=None):
    components = load("context/component-map.yaml")["components"]
    terms = load("context/glossary.yaml")["terms"]
    scope = load("context/scope.yaml")
    profile = load("i2s.profile.yaml")
    if schemas_root is not None:
        for filename, document in (
            ("component-map", {"components": components}),
            ("glossary", {"terms": terms}),
            ("scope", scope),
            ("profile", profile),
        ):
            schema = json.loads((schemas_root / f"{filename}.schema.json").read_text())
            Draft202012Validator.check_schema(schema)
            Draft202012Validator(schema).validate(document)
    component_ids = unique_ids(components, "components")
    term_ids = unique_ids(terms, "glossary")
    regions = unique_ids(scope["regions"], "regions")
    data_classes = unique_ids(scope["data_classes"], "data classes")
    require(set(scope["regulated_data_classes"]) <= data_classes,
            "Unknown regulated data class")
    unique_ids(scope["regulations"], "regulations")
    require(len(components) == 6, "Expected six components")
    require(len({c["repo"] for c in components}) == 6, "Expected six distinct repos")
    require({c["id"]: c["repo"] for c in components} == COMPONENT_REPOSITORIES,
            "Component ownership must remain in the six Shield application repos")
    require(
        {c["application"] for c in components}
        == {"policy-admin", "claims", "billing-customer"},
        "Expected the three Shield applications",
    )
    owned = set()
    for component in components:
        name = component["id"]
        require(re.fullmatch(r"CM-[A-Z0-9]+(?:-[A-Z0-9]+)*", name),
                f"{name}: invalid component ID")
        for field in ("name", "paths", "contracts", "data_classes", "regions", "owner_team"):
            require(bool(component[field]), f"{name}: missing {field}")
        dependencies = component["depends_on"]
        require(set(dependencies) <= component_ids, f"{name}: unknown dependency")
        require(name not in dependencies, f"{name}: self dependency")
        require(len(dependencies) == len(set(dependencies)), f"{name}: duplicate dependency")
        require(set(component["regions"]) <= regions, f"{name}: unknown region")
        require(
            set(component["data_classes"]) <= data_classes,
            f"{name}: unknown data class",
        )
        owns = set(component["owns"])
        require(owns <= term_ids, f"{name}: unknown glossary term")
        require(not owned & owns, f"{name}: duplicate glossary ownership")
        owned.update(owns)
        for relative in component["paths"] + component["contracts"]:
            path = Path(relative)
            require(not path.is_absolute() and ".." not in path.parts,
                    f"{name}: unsafe repository path")
            if repos_root is not None:
                target = repos_root / component["repo"] / path
                require(target.exists(), f"{name}: missing {target}")
                if relative in component["contracts"]:
                    with target.open() as source:
                        contract = (json.load(source) if target.suffix == ".json"
                                    else yaml.safe_load(source))
                    if target.suffix == ".json":
                        require("$schema" in contract, f"{target}: missing JSON Schema")
                        Draft202012Validator.check_schema(contract)
                    else:
                        require(contract.get("openapi") == "3.1.0",
                                f"{target}: expected OpenAPI 3.1")
                        require(bool(contract.get("paths")), f"{target}: no API paths")
                        validate_openapi(contract, base_uri=target.resolve().as_uri())
    require(owned == term_ids, "Every glossary term needs an owner")
    for term in terms:
        require(re.fullmatch(r"GL-\d{4}", term["id"]), "Invalid glossary ID")
        for field in ("term", "definition", "owner"):
            require(bool(term.get(field)), f"{term['id']}: missing {field}")
        require(term.get("status") in {"draft", "approved", "deprecated"},
                f"{term['id']}: invalid status")
        owner = next(c["owner_team"] for c in components if term["id"] in c["owns"])
        require(term["owner"] == owner or term["owner"].startswith("Pending:"),
                f"{term['id']}: glossary owner differs from component owner")
    visiting, visited = set(), set()
    by_id = {component["id"]: component for component in components}

    def visit(name):
        require(name not in visiting, f"Dependency cycle at {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in by_id[name]["depends_on"]:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)

    for name in component_ids:
        visit(name)
    require("CM-POLICY" in by_id["CM-FRAUD"]["depends_on"],
            "CM-FRAUD must declare its CM-POLICY SQL-view dependency")
    require("contracts/shared/policy-risk-view.json" in by_id["CM-POLICY"]["contracts"],
            "CM-POLICY must publish the shared view contract")
    require("contracts/policy-risk-view.json" in by_id["CM-FRAUD"]["contracts"],
            "CM-FRAUD must link the shared view contract")
    if repos_root is not None:
        provider = json.loads(
            (repos_root / by_id["CM-POLICY"]["repo"]
             / "contracts/shared/policy-risk-view.json").read_text()
        )
        consumer = json.loads(
            (repos_root / by_id["CM-FRAUD"]["repo"]
             / "contracts/policy-risk-view.json").read_text()
        )
        require(consumer.get("$ref") == provider.get("$id") and bool(provider.get("$id")),
                "Fraud shared-view link must reference the canonical policy schema")
    for regulation in scope["regulations"]:
        require(re.fullmatch(r"REG-[A-Z]{2}-\d{2}", regulation["id"]),
                "Invalid regulation ID")
        require(regulation["region"] in regions, "Unknown regulation region")
        require(set(regulation["data_classes"]) <= data_classes,
                "Unknown regulation data class")
        require(regulation.get("status") in {"unverified", "verified"},
                "Invalid regulation status")
        require(bool(regulation.get("owner")) and bool(regulation.get("source")),
                "Regulation needs owner and provenance")
    require(bool(profile.get("client")), "Missing profile client")
    require(profile.get("specs_repo") == SPECS_REPOSITORY,
            f"specs_repo must be the canonical repository {SPECS_REPOSITORY}")
    require(profile.get("context_repo") == "amithp-ust/shield-context",
            "context_repo must remain amithp-ust/shield-context")
    require(bool(profile.get("surfaces")) and
            set(profile["surfaces"]) <= {"copilot", "claude-code", "kiro"},
            "Invalid profile surfaces")
    require(profile.get("handoff") in {"copilot-coding-agent", "claude-code", "kiro"},
            "Invalid profile handoff")
    approved = profile["model_policy"]["approved_judges"]
    approved_pairs = [(entry["provider"], entry["model"]) for entry in approved]
    require(len(approved_pairs) == len(set(approved_pairs)), "Duplicate approved judges")
    session_approved = profile["model_policy"]["approved_session_models"]
    require(len(session_approved) == len(set(session_approved)),
            "Duplicate approved session models")
    judge = profile["judge"]
    for field in ("provider", "model", "version"):
        require(isinstance(judge.get(field), str) and bool(judge[field]),
                f"Judge needs {field}")
    require(judge.get("allow_mock") is False, "Shield must not enable mock judging")
    require(judge["model"] == "unconfigured" or
            (judge["provider"], judge["model"]) in approved_pairs,
            "Configured judge model must be approved")
    if judge["provider"] == "copilot":
        require(judge["version"] == "service-managed",
                "Copilot backend version must not be a CLI version")
        require(judge.get("allow_unpinned_model") is True,
                "Copilot needs the explicit model-version-pinning exception")
        require(isinstance(judge.get("cli_version"), str),
                "Copilot CLI version must be separately recorded")
    require(set(profile.get("session_models", {}).values()) <= set(session_approved),
            "Session models must be approved")
    tools = profile["tool_register"]
    require(all(isinstance(tool, str) and tool for tool in tools),
            "Tool register must contain string IDs")
    require(len(tools) == len(set(tools)), "Duplicate tools")
    for standard in ("api", "data", "security", "naming"):
        require((ROOT / "context" / "standards" / f"{standard}.md").is_file(),
                f"Missing {standard} standard")
    print(f"Shield context valid: 3 applications, 6 components, specs in {SPECS_REPOSITORY}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path)
    parser.add_argument("--schemas-root", type=Path,
                        help="Accelerator src/i2s/schemas directory")
    args = parser.parse_args()
    validate(args.repos_root, args.schemas_root)
