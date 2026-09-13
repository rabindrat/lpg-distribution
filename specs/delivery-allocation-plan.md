# Delivery and allocation implementation plan

## Current slice

- [x] Add Celery application wiring and Redis broker/result configuration.
- [x] Add durable `AllocationRun` records.
- [x] Add ranked `Allocation` records with priority and distance snapshots.
- [x] Add an idempotent applicant-selection task entry point.
- [x] Add optional private household coordinates for distance ranking.
- [x] Add dealer UI to receive cylinders and create/monitor allocation runs.
- [x] Add reusable cylinder-unit and filled-cycle records.
- [x] Reserve available filled cylinders together with applicant allocations.

## Next slices

- [ ] Add dealer sale/invoice recording.
- [ ] Add applicant receipt confirmation.
- [ ] Add notification attempts and SMS/email provider abstraction.
- [ ] Add Celery Beat reminders, expiry checks, and escalation cases.
- [ ] Add immutable workflow transitions and audit events.
- [ ] Add company/NOC exception queues and reports.

## Operating rules

- PostgreSQL is the source of truth; Redis only transports tasks and stores task results.
- Allocation ranking is P1 first, then distance, then application creation time, then ID.
- Missing coordinates sort after applications with known distance.
- Allocation creation and application status changes occur in one transaction.
- Tasks must be safe to retry without creating duplicate allocations.
