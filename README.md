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

- `i2s.profile.yaml`: illustrative intent-to-spec configuration, judge, model
  approvals, and tool register. No external profile schema is implied. Model IDs
  are deliberately unconfigured; do not run a model judge until approved.
- `context/glossary.yaml`: shared domain identifiers and definitions.
- `context/scope.yaml`: regions, data classes, and candidate regulations requiring
  compliance-owner review, not a legal determination.
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
