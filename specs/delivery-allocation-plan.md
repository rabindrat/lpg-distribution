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
- [x] Keep applicant/dealer address text optional and preserve raw values.
- [x] Add canonical location references and dealer tole/ward coverage records.
- [x] Apply exact/normalized/fuzzy tole-or-ward coverage matching to allocations.

## Next slices

- [ ] Add dealer sale/invoice recording.
- [ ] Add applicant receipt confirmation.
- [ ] Add notification attempts and SMS/email provider abstraction.
- [ ] Add Celery Beat reminders, expiry checks, and escalation cases.
- [ ] Add immutable workflow transitions and audit events.
- [ ] Add company/NOC exception queues and reports.

## Location decision

- Kathmandu Valley is the pilot scope: Kathmandu, Lalitpur, and Bhaktapur districts.
- Municipality/ward/tole reference fields are optional; the original text is retained for later enrichment.
- Dealer coverage may be declared at either tole or ward precision.
- Tole matching uses exact canonical references where available, normalized text, and a conservative fuzzy threshold; unresolved locations are not silently treated as matches.
- Use [LocalBoundaries](https://github.com/openknowledgenp/localboundaries) as the baseline source for province/district/local-level boundary data. It publishes those administrative levels, not a complete authoritative tole layer.
- Maintain the tole reference/alias layer through NOC and dealer data stewardship. The [nepal-geo-data package](https://github.com/bedbyaspokhrel/nepal-geo-data) may help bootstrap names and ward lists, but should not be treated as the regulatory source of truth.

## Operating rules

- PostgreSQL is the source of truth; Redis only transports tasks and stores task results.
- Allocation ranking is P1 first, then distance, then application creation time, then ID.
- Missing coordinates sort after applications with known distance.
- Allocation creation and application status changes occur in one transaction.
- Tasks must be safe to retry without creating duplicate allocations.
