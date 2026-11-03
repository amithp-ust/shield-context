# Data standards

The owning component is authoritative for each glossary term. Identify reads,
writes, derived data, and replicated records when tracing a requirement.
Specify freshness and reconciliation for any copy of another component's data.
Propose cross-component database contracts explicitly rather than assuming
internal tables are stable interfaces.

Use parameterized SQL, explicit migrations, foreign keys where applicable, and
synthetic fixtures only. Store money as integer USD cents, not floating point.
Never silently substitute a zero amount for missing policy or payment data.
Document retention and deletion before production use.
