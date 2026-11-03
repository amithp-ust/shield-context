# Naming standards

Repositories use `shield-<component>`. Component IDs use `CM-`, glossary terms
use `GL-` followed by four digits, and regulation entries use `REG-`.
Application IDs are `policy-admin`, `claims`, and `billing-customer`.

Python modules and JSON fields use snake_case. Monetary fields end in `_cents`.
Specifications live in `specs/<three-digit-sequence>-<intent-slug>/`.
Use stable requirement IDs in primary and component-specific specs so links
remain traceable across repositories.
