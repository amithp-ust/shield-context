"""Exercise the six sibling stubs with synthetic data and their contracts."""

import argparse
import importlib.util
import json
from pathlib import Path
import sqlite3
from contextlib import closing

from jsonschema import Draft202012Validator, FormatChecker
import yaml

from validate import require, validate


def load_module(root, repo, relative):
    source = root / repo / relative
    spec = importlib.util.spec_from_file_location(repo.replace("-", "_"), source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def contract(root, repo, filename):
    with (root / repo / "contracts" / filename).open() as source:
        return yaml.safe_load(source)


def check(instance, schema):
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def verify(root):
    validate(root)
    rules = load_module(root, "shield-underwriting-rules", "src/underwriting/rules.py")
    policy_module = load_module(root, "shield-policy-service", "src/policy/service.py")
    fraud_module = load_module(root, "shield-fraud-scoring", "src/fraud/scoring.py")
    billing_module = load_module(root, "shield-billing-service", "src/billing/service.py")
    claims_module = load_module(root, "shield-claims-service", "src/claims/service.py")
    portal_module = load_module(root, "shield-customer-portal", "src/portal/dashboard.py")
    underwriting_api = contract(root, "shield-underwriting-rules", "underwriting-api.yaml")
    policy_api = contract(root, "shield-policy-service", "policy-api.yaml")
    fraud_api = contract(root, "shield-fraud-scoring", "fraud-api.yaml")
    billing_api = contract(root, "shield-billing-service", "billing-api.yaml")
    claims_api = contract(root, "shield-claims-service", "claims-api.yaml")
    portal_api = contract(root, "shield-customer-portal", "portal-api.yaml")
    with closing(sqlite3.connect(":memory:")) as policy_db, \
            closing(sqlite3.connect(":memory:")) as portal_db:
        policy_db.executescript(
            (root / "shield-policy-service/db/migrations/001_policy.sql").read_text()
        )
        policy = policy_module.PolicyService(policy_db, rules.evaluate)
        fraud = fraud_module.FraudScoring(policy_db)
        billing = billing_module.BillingService(policy.get_policy)
        claims = claims_module.ClaimsService(
            policy.get_policy, fraud.score, billing.create_payout
        )
        portal = portal_module.CustomerPortal(
            portal_db, policy.get_policy, claims.get_claim, billing.premium_schedule
        )
        issued = policy.issue_policy("P-DEMO", "C-DEMO", 35, 100000, 10000)
        view_schema = contract(root, "shield-policy-service", "shared/policy-risk-view.json")
        consumer_schema = contract(root, "shield-fraud-scoring", "policy-risk-view.json")
        require(consumer_schema["$ref"] == view_schema["$id"],
                "Fraud must link the canonical policy view schema")
        cursor = policy_db.execute("SELECT * FROM policy_risk_view WHERE policy_id = ?",
                                   ("P-DEMO",))
        columns = [column[0] for column in cursor.description]
        require(columns == view_schema["required"],
                "Migration view columns differ from the shared contract")
        check(dict(zip(columns, cursor.fetchone())), view_schema)
        check(issued["policy"], policy_api["components"]["schemas"]["Policy"])
        event_schema = json.loads(
            (root / "shield-policy-service/contracts/events/policy-issued.json").read_text()
        )
        check(issued["event"], event_schema)
        check(
            rules.evaluate(35, 100000),
            underwriting_api["paths"]["/underwriting/evaluate"]["post"]
            ["responses"]["200"]["content"]["application/json"]["schema"],
        )
        queries = []
        policy_db.set_trace_callback(queries.append)
        check(
            fraud.score("P-DEMO", 50000),
            fraud_api["paths"]["/fraud/score"]["post"]
            ["responses"]["200"]["content"]["application/json"]["schema"],
        )
        require(any("policy_risk_view" in query for query in queries),
                "Fraud scoring must exercise its SQL view read")
        result = claims.adjudicate("CL-DEMO", "P-DEMO", 50000)
        check(result, claims_api["components"]["schemas"]["Claim"])
        require(result["status"] == "partially_paid", "Expected partial payout")
        require(result["paid_cents"] == 40000, "Expected deductible-adjusted payout")
        require(claims.adjudicate("CL-DEMO", "P-DEMO", 50000) == result,
                "Claim retries must be idempotent")
        check(
            billing.create_payout("CL-DEMO", 40000),
            billing_api["paths"]["/payouts"]["post"]
            ["responses"]["200"]["content"]["application/json"]["schema"],
        )
        dashboard = portal.dashboard("CL-DEMO")
        check(
            dashboard,
            portal_api["paths"]["/dashboard/claims/{claim_id}"]["get"]
            ["responses"]["200"]["content"]["application/json"]["schema"],
        )
        require(dashboard["premium_schedule"]["annual_premium_cents"] == 5000,
                "Premium must come from the issued policy")
        require(
            portal_db.execute(
                "SELECT status, paid_cents FROM claim_status WHERE claim_id = ?",
                ("CL-DEMO",),
            ).fetchone() == ("partially_paid", 40000),
            "Portal must persist its local claim status",
        )
        policy_db.execute("DROP VIEW policy_risk_view")
        try:
            fraud.score("P-DEMO", 50000)
        except sqlite3.OperationalError as error:
            require("policy_risk_view" in str(error), "Unexpected database failure")
        else:
            raise ValueError("Fraud scoring incorrectly worked without its view")
    print("Shield fixture valid: policy issuance, scoring, partial payout, portal")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, default=Path(__file__).resolve().parents[2])
    verify(parser.parse_args().repos_root)
