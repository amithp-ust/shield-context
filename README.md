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
  Model IDs, exact client CLI version, and approval lists are deliberately
  unconfigured. Metadata validation passes; accelerator `doctor` must REFUSE
  model execution until client setup and approvals are complete. No mock judge
  or approved model is supplied. `version: service-managed` describes the backend,
  not the CLI. `allow_unpinned_model: true` records only the user-approved isolated
  Copilot design exception (model ID/CLI pinning without an immutable backend
  revision); it does not approve any client model. Tool IDs are inventory only:
  client tool terms and policies remain unconfirmed.
- `context/glossary.yaml`: shared domain identifiers and definitions.
  Accountable owners come from the component map; all terms remain drafts.
- `context/scope.yaml`: regions, data classes, and candidate regulations requiring
  compliance-owner review, not a legal determination.
  `REG-US-01` and `REG-US-02` retain prior IDs and candidate applicability in
  `regulation_provenance`; both remain `unverified`.
- `context/standards/`: API, data, security, and naming conventions.

## Publishing specifications

Application repositories start with empty `specs/` directories (tracked using
`.gitkeep`). Publish changes as pull requests rather than silently updating a
second repository.

For an intent such as "show why a claim was partly paid on the portal", the
primary package belongs in
`shield-claims-service/specs/001-claim-payment-reason/`:
`spec.md`, `interview.md`, `plan.md`, and `tasks.md`.
The portal package at
`shield-customer-portal/specs/001-claim-payment-reason/` contains only the
portal requirements in `spec.md`, with a link to the primary `spec.md` and the
source requirement IDs. Both packages retain the same intent ID. This is a
publishing example, not an already implemented or published feature.

## Validation

```sh
python -m pip install -r requirements-dev.txt
python scripts/validate.py
# Optional: with the six sibling checkouts present:
python scripts/validate.py --repos-root ..
python scripts/verify_fixture.py --repos-root ..
```

CI checks metadata, dependency references, glossary ownership, and profile
configuration. The optional sibling check also verifies component paths and
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
- Confirm tool terms/policies and enable the required Copilot CLI policy only
  after client review; do not treat this inventory as an approval.
- Bootstrap client workflows only with an explicitly reviewed accelerator
  `--accelerator-ref` set to a full 40-character commit SHA, not a branch or tag.
  Wait for the reviewed accelerator release commit; no client workflow is
  installed by these PRs.
- Before enabling client workflows, set repository variables
  `I2S_CONTEXT_REPOSITORY` and `I2S_CONTEXT_REF` (the approved context revision),
  and configure secrets `I2S_ACCELERATOR_TOKEN` and `I2S_CONTEXT_TOKEN` with
  least-privilege repository access. Never put token values in this profile,
  documentation, or specifications.
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

Review the provider and consumer contracts together before the context map change.
Canonical links on `main` become available only after the corresponding PRs merge;
the six-sibling fixture resolves the proposed contracts locally without network
access. Context CI validates metadata and context regression tests, not the
six-repository fixture; the application repositories currently have no CI checks.
