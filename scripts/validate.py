"""Validate Shield context and, optionally, sibling component contracts."""

import argparse
import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate as validate_openapi


ROOT = Path(__file__).resolve().parents[1]


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


def validate(repos_root=None):
    components = load("context/component-map.yaml")["components"]
    terms = load("context/glossary.yaml")["terms"]
    scope = load("context/scope.yaml")
    profile = load("i2s.profile.yaml")
    component_ids = unique_ids(components, "components")
    term_ids = unique_ids(terms, "glossary")
    regions = unique_ids(scope["regions"], "regions")
    data_classes = unique_ids(scope["data_classes"], "data classes")
    unique_ids(scope["regulation_register"], "regulations")
    require(len(components) == 6, "Expected six components")
    require(len({c["repo"] for c in components}) == 6, "Expected six distinct repos")
    require(
        {c["application"] for c in components}
        == {"policy-admin", "claims", "billing-customer"},
        "Expected the three Shield applications",
    )
    owned = set()
    for component in components:
        name = component["id"]
        for field in ("paths", "contracts", "data_classes", "regions", "owner_team"):
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
    for regulation in scope["regulation_register"]:
        require(set(regulation["regions"]) <= regions, "Unknown regulation region")
        require(set(regulation["data_classes"]) <= data_classes,
                "Unknown regulation data class")
    approved = profile["approved_models"]
    require(len(approved) == len(set(approved)), "Duplicate approved models")
    judge = profile["judge"]
    require(not judge["enabled"] or judge["model"] in approved,
            "Enabled judge must use an approved model")
    require(judge["model"] is None or judge["model"] in approved,
            "Configured judge model must be approved")
    unique_ids(profile["tool_register"], "tools")
    for tool in profile["tool_register"]:
        require(tool["approval"] in {"approved", "requires-human-approval", "denied"},
                f"{tool['id']}: unknown approval state")
    for standard in ("api", "data", "security", "naming"):
        require((ROOT / "context" / "standards" / f"{standard}.md").is_file(),
                f"Missing {standard} standard")
    print("Shield context valid: 3 applications, 6 components, 1 context repository")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path)
    args = parser.parse_args()
    validate(args.repos_root)
