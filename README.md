# Shield Insurance context

Shared context for three applications and six component repositories.

| Application | Components |
| --- | --- |
| Policy Administration (`policy-admin`) | `shield-policy-service`, `shield-underwriting-rules` |
| Claims (`claims`) | `shield-claims-service`, `shield-fraud-scoring` |
| Billing & Customer (`billing-customer`) | `shield-billing-service`, `shield-customer-portal` |

`context/component-map.yaml` records declared dependencies. Verify these declarations
against implementation evidence when assessing a change; the map is not proof of
the absence of other relationships.

## Context

- `i2s.profile.yaml`: accelerator-compatible Copilot surface and handoff configuration.
  The demo operator approved `claude-sonnet-5.5` for the interview and isolated judge,
  with local Copilot CLI `1.0.105`. This approval is limited to synthetic demo data;
  local CLI login and the isolated judge live canary succeeded on 2026-11-06.
  Repeat `doctor --live-judge` on each session environment.
  Metadata validation does not prove a working judge. Accelerator `doctor` must REFUSE
  model execution if client authentication or CLI/tool setup fails. No mock judge
  is enabled. `version: service-managed` describes the backend,
  not the CLI. `allow_unpinned_model: true` records only the user-approved isolated
  Copilot design exception (model ID/CLI pinning without an immutable backend
  revision); it does not approve additional client models. Local CLI/tool use is approved only
  for this synthetic demo; production organization policies and terms need a separate review.
- `context/glossary.yaml`: shared domain identifiers and definitions.
  Accountable owners come from the component map; all terms remain drafts.
- `context/scope.yaml`: regions, data classes, and candidate regulations requiring
  compliance-owner review, not a legal determination.
  `REG-US-01` and `REG-US-02` retain prior IDs and candidate applicability in
  `regulation_provenance`; both remain `unverified`.
- `context/standards/`: API, data, security, and naming conventions.

## Central specification source

[`amithp-ust/Intent-to-spec`](https://github.com/amithp-ust/Intent-to-spec) is the
sole canonical authoring, specifications, and requirement-metrics repository,
declared by `specs_repo` in this profile. The personal namespace simulates the
client organization; it does not confer client approval. Full Spec Kit,
authoring agents, gate workflows, and metrics run only in that central repo.
This context repository remains authoritative for glossary, component map,
scope, standards, and client policy; the six application repositories retain
their real implementation and component ownership.

For an intent such as "show why a claim was partly paid on the portal", keep the
full `spec.md`, `interview.md`, `plan.md`, and `tasks.md` together in one intent
package under `amithp-ust/Intent-to-spec/specs/`. Record claims and portal
requirement/component IDs in that package, not primary-app specs or copied
secondary slices. This is an example, not an approved or published feature.

Application issues and code PRs must link the approved canonical spec using its
full immutable commit SHA, exact path, and requirement IDs, with the reviewed
context revision. Branch URLs are for discovery only, not approval evidence.
Code PRs require human review; central gate or fixture success does not authorize
a merge. Empty app `specs/.gitkeep` directories are legacy placeholders, not
publication targets. Preserve historical content; migrate any existing authoring
material through a separately reviewed change rather than deleting it blindly.

## Validation

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate.py
# Optional: with the six sibling checkouts present:
python scripts/validate.py --repos-root ..
python scripts/verify_fixture.py --repos-root ..
```

CI checks metadata, dependency references, glossary ownership, the exact
`amithp-ust/Intent-to-spec` canonical target, real app repository ownership,
and profile configuration. The optional sibling check also verifies component paths and
contract files, including OpenAPI and JSON Schema validation. The fixture check
wires all six components together with synthetic data and checks response shapes
against contracts. Run each component's unit tests from its own checkout with
`python -m unittest discover -s tests`.
Stubs use only the Python standard library and are not production services;
they do not start HTTP servers.

Run context regression tests with `python -m unittest discover -s tests`.
To additionally check the accelerator's actual JSON schemas, use
`python scripts/validate.py --repos-root .. --schemas-root <accelerator-checkout>/src/i2s/schemas`.
The optional schema path is read-only; no accelerator files are copied or changed.

## Shared policy risk view

`CM-FRAUD` depends on `CM-POLICY` through the injected `policy_database` SQLite
connection, not an HTTP API. The canonical row schema is
[`shield-policy-service/contracts/shared/policy-risk-view.json`](https://github.com/amithp-ust/shield-policy-service/blob/main/contracts/shared/policy-risk-view.json);
fraud's `contracts/policy-risk-view.json` is a linked consumer slice.
`db/migrations/001_policy.sql` creates the four-column view; fraud queries
`coverage_cents`, `deductible_cents`, and `status` by `policy_id`.
The sibling fixture checks the link, actual migration columns, and row schema
offline. This records existing behavior, not approval of production database
sharing. No service code or specification package is generated.

## Client setup still required

- Review draft glossary ownership and candidate regulations with accountable
  business/compliance owners; do not mark them approved or verified by inference.
- Approve the actual client judge/session model IDs and populate their allowlists;
  record the exact installed official Copilot CLI version in `judge.cli_version`.
  Confirm client-issued credentials (without committing secrets), isolated judge
  operation, and the recorded backend-pinning exception.
  The synthetic Sonnet/demo CLI approval and successful local canary are recorded. Each new
  environment still needs its own authenticated live check.
- Confirm tool terms/policies and enable the required Copilot CLI policy only
  after client review; do not treat this inventory as an approval.
- Bootstrap authoring, gate, and metrics workflows only in the central
  `amithp-ust/Intent-to-spec` repo, with an explicitly reviewed accelerator
  `--accelerator-ref` set to a full 40-character commit SHA, not a branch or tag,
  or use an approved committed vendor copy and `--vendored` in a private specs repository.
  Wait for the reviewed accelerator release commit; no client workflow is
  installed in the context or application repos. Apps use only linked consumer
  instructions and standard-library unit-test CI, not an authoring installation.
- Before enabling central client workflows, set central-repository variables
  `I2S_CONTEXT_REPOSITORY` and `I2S_CONTEXT_REF` (the approved context revision),
  and configure secrets `I2S_ACCELERATOR_TOKEN` and `I2S_CONTEXT_TOKEN` with
  least-privilege repository access. Never put token values in this profile,
  documentation, or specifications.
  The vendored private demo needs no accelerator secret; public Shield context/apps can use
  the workflow's `github.token` fallback. Do not make the vendored specs repository public.
- Use `gate status --require-build-ready` for production readiness: it rejects
  mock judging, absent application source, unassessed dependencies, and deferred
  regions. Passing the synthetic fixture or metadata validation is not a
  production-readiness approval.
- Supply current `--context` and profile when using `handoff --execute`.
  Context/profile fingerprints bind gate evidence to the reviewed inputs;
  rerun the gate when either changes rather than reusing stale evidence.
- Have repository administrators configure protected branches and required
  checks separately. These changes do not modify branch protection or merge PRs.

## Coordinated pull requests

- [Context compatibility](https://github.com/amithp-ust/shield-context/pull/1)
- [Canonical policy view contract](https://github.com/amithp-ust/shield-policy-service/pull/1)
- [Fraud consumer contract link](https://github.com/amithp-ust/shield-fraud-scoring/pull/1)

These compatibility PRs are merged. Review future provider and consumer contract
changes together; the six-sibling fixture resolves contracts locally without
network access. Context CI validates metadata and context regression tests, not
the six-repository fixture. Each application has a minimal Python 3.11 unit-test
workflow; cross-repository fixture checks still run with all six sibling checkouts.
