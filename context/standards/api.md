# API standards

Use OpenAPI 3.1 contracts in `contracts/`. Stubs are callable Python functions;
paths describe the intended service boundary, not a running HTTP deployment.
Use stable opaque string IDs and JSON objects with snake_case properties.
Represent money as nonnegative integer USD cents and timestamps as UTC ISO 8601.

Document success and error responses. Missing resources map to 404, malformed
inputs to 400, and business-rule conflicts to 409 when an HTTP adapter is added.
Do not turn dependency errors into successful responses. Payout creation must
be idempotent by claim ID. Version breaking contract changes explicitly.

Events require a JSON Schema, event ID, event type, timestamp, and resource ID.
Do not include unnecessary customer data in events.
