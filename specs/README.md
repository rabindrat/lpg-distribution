# Centralized LPG Distribution System — Specification Set

Status: **Draft / pre-development discovery**

Source: the linked ChatGPT conversation, “Make A Distribution App”, including the pre-development discovery questionnaire and the Django-first architecture recommendation.

These documents describe the smallest credible Kathmandu Valley pilot while preserving the controls needed for a government-operated LPG distribution workflow. Items marked **TBD** require written approval before production development.

## Documents

- [Functional specification](functional-spec.md) — actors, workflows, business rules, interfaces, and MVP acceptance criteria.
- [Technical architecture](technical-architecture.md) — modular Django monolith, deployment, integrations, and delivery phases.
- [Data model](data-model.md) — core entities, relationships, constraints, lifecycle states, and audit requirements.
- [Security and operations](security-operations.md) — access control, privacy, security, hosting, backup, DR, and support requirements.
- [Discovery decision register](discovery-decisions.md) — proposed defaults, unresolved decisions, owners, and sign-off gates.

## Baseline decisions captured from the conversation

- Build a **modular Django monolith first**.
- Use server-rendered Django templates with HTMX, Bootstrap, and minimal JavaScript; do not start with React.
- Use PostgreSQL + PostGIS as the production database.
- Use Django Admin for NOC and company back-office workflows, with strict organization-scoped permissions.
- Start with a responsive web application/PWA; defer a native Android client until the workflow stabilizes.
- Enforce one household entitlement per calendar month at the database layer, not only in Python code.
- LPG companies have exclusive final authority for dealer approval; NOC monitors and audits.
- Keep production data, backups, and object storage in Nepal unless a written exception is approved.

## Repository note

The current scaffold is generated with Django **6.1.1**, while the conversation recommends Django **5.2 LTS**. Before implementation, the project owner must choose one baseline and pin it in the dependency lockfile. The functional intent in these specs is version-independent.
