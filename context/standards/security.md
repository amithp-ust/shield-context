# Security standards

These are local demonstration stubs, not production-ready services. Production
adapters must authenticate callers, authorize access per customer and operation,
encrypt transport and regulated data, and use least-privilege service identities.
Never deploy these callable stubs directly as public endpoints.

Use synthetic identifiers and amounts. Do not commit credentials, production
records, or payment instrument data. Do not log full policy or claim payloads.
Validate inputs at trust boundaries and propagate errors explicitly. Restrict
database access to documented contracts and assess any cross-service data reads.
Have Compliance review regulatory applicability and retention before deployment.
