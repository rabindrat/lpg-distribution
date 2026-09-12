# Pending Work Checklist

Use this as the working checklist for the Kathmandu Valley pilot. A checked item means it is present in the current repository; an unchecked item is still pending. Items marked **Gate** should be resolved before production rollout.

## 1. Already completed in the repository

- [x] Applicant registration and login.
- [x] Applicant household/address form.
- [x] Applicant LPG application form and dashboard.
- [x] Initial monthly duplicate-application protection.
- [x] Dealer account registration.
- [x] Dealer business, address, GPS, license, shop-photo, and supporting-document fields.
- [x] Dealer status dashboard.
- [x] Django Admin actions for verification queue, physical verification, approval, and rejection.
- [x] Crispy Forms with Bootstrap 5 and HTMX-ready templates.
- [x] PostgreSQL/WhiteNoise/Gunicorn configuration.
- [x] Railway start, migration, build, health-check, and environment-variable guidance.
- [x] Basic applicant/dealer tests and Django system checks.

## 2. Production decision gates

### Ownership and governance

- [ ] **Gate:** Name the official system owner.
- [ ] **Gate:** Name the data controller/owner.
- [ ] **Gate:** Confirm day-to-day operator: NOC IT, IDMC, vendor, or joint team.
- [ ] **Gate:** Name the authority allowed to change entitlement, priority, dealer, reporting, and privacy rules.
- [ ] Confirm the organizations and jurisdictions represented in the system.
- [ ] Assign a named owner and decision date to every unresolved item in the discovery register.

### Household and eligibility rules

- [ ] **Gate:** Approve the legal/operational definition of a household.
- [ ] **Gate:** Approve mandatory household identity fields and evidence.
- [ ] Define how separate flats, rented rooms, and shared residences are proven.
- [ ] Approve Labourer and Student eligibility evidence.
- [ ] Assign the authority responsible for duplicate-household review.
- [ ] Define acceptable evidence and appeal handling for duplicate disputes.

### Entitlement and application rules

- [ ] **Gate:** Confirm one cylinder per household per calendar month.
- [ ] **Gate:** Confirm whether entitlement is consumed at approval, allocation, or verified delivery.
- [ ] Define cancellation and same-month reapplication behavior.
- [ ] Define failed-delivery attempts, rescheduling, and application expiry.
- [ ] Decide whether brand switching is allowed and under what conditions.
- [ ] Decide whether applicants choose dealers, choose from nearby dealers, or receive system assignment.
- [ ] Approve the P1/P2 categories, delivery targets, evidence, and escalation path.
- [ ] Approve QR expiry, lost-QR reissue, and replay/fraud policy.

### Dealer and company workflow

- [ ] **Gate:** Confirm the LPG company has exclusive final dealer-approval authority.
- [ ] Decide whether one employee may perform both verification and approval.
- [ ] Approve dealer GPS-distance tolerance.
- [ ] Define the physical verification checklist and correction/reinspection process.
- [ ] Confirm whether one dealer may represent multiple LPG brands.
- [ ] Define company, verifier, approver, and NOC organization scopes.
- [ ] Decide whether company verification/approval requires a dedicated portal or Django Admin is sufficient for the pilot.

### Supply, stock, delivery, and invoice rules

- [ ] Define the daily company-supply reporting deadline.
- [ ] Decide whether supply is entered manually, uploaded by Excel, or integrated by API.
- [ ] Define dealer receipt acknowledgement.
- [ ] Approve the stock ledger and negative-stock exception policy.
- [ ] Confirm whether delivery to the registered residence is mandatory.
- [ ] **Gate:** Approve the official proof-of-delivery combination.
- [ ] Define responsibility and investigation process for fraudulent delivery confirmation.
- [ ] Approve invoice fields, numbering scope, correction, cancellation, and receipt format.

### Privacy, GIS, and data sovereignty

- [ ] Approve the public-vs-restricted data matrix.
- [ ] Define who may view customer names, mobile numbers, and addresses.
- [ ] Confirm local-level municipality/ward visibility rules.
- [ ] **Gate:** Approve Google Maps or an alternative government GIS.
- [ ] **Gate:** Confirm database and backup residency requirements in Nepal.
- [ ] Define restrictions on foreign cloud processing.
- [ ] Select the approved NOC/IDMC/DoIT hosting and data-centre environment.

## 3. Engineering work still pending

### Domain model and data integrity

- [ ] Add organization, LPG company, municipality, ward, and tole reference models.
- [x] Add the initial LPG brand reference model and seed catalog.
- [x] Replace applicant/dealer free-text brand entry with approved active-brand relationships; retain legacy text values for compatibility during migration.
- [ ] Introduce a separate `Entitlement` model with one record per household/month.
- [ ] Implement explicit state-transition services for applications, dealers, verification, allocation, delivery, invoices, supply, and stock.
- [ ] Add immutable audit events and workflow-transition history.
- [ ] Add database transactions/row locking for entitlement, allocation, delivery, and stock operations.
- [ ] Add retention, archive, anonymization, deletion, and legal-hold fields/processes.

### Applicant workflow

- [ ] Add mobile OTP registration, recovery, and sensitive-action verification.
- [ ] Add household-member linking for multiple family accounts.
- [ ] Add duplicate-candidate detection and manual review queue.
- [ ] Add application status timeline, QR generation, QR invalidation, and secure token validation.
- [ ] Add dealer selection/assignment and allocation visibility once the policy is approved.
- [ ] Add complaint submission and applicant notifications.

### Dealer/company workflow

- [ ] Add company-scoped roles and permissions.
- [ ] Add verifier queue and onsite checklist.
- [ ] Add fresh verification GPS/photo capture and evidence history.
- [ ] Add approver queue with separation-of-duties enforcement.
- [ ] Add correction requests, resubmission, rejection reason, and reinspection.
- [ ] Add dealer assigned applications, invoice entry, delivery recording, and delivery exceptions.
- [ ] Add dealer stock receipt, daily stock ledger, and reconciliation screens.

### Supply chain and reporting

- [ ] Add company daily supply submission and adjustment workflow.
- [ ] Add dealer dispatch/receipt reconciliation.
- [ ] Add stock balance and negative-stock alerts.
- [ ] Add NOC dashboard KPIs and overdue/shortage exception queues.
- [ ] Add company-scoped and municipality-scoped reports.
- [ ] Add approved Excel/PDF exports with export auditing.
- [ ] Add PostGIS dealer queries and a graceful map fallback when Google Maps is unavailable.
- [ ] Add SMS/OTP provider integration and delivery notification templates.
- [ ] Add versioned DRF API only when mobile or external integrations require it.

## 4. Production and Railway tasks

- [ ] **Gate:** Decide whether to remain on Django 6.1.1 or align with the earlier Django 5.2 LTS recommendation.
- [ ] Commit and review the dependency lockfile after the Django-version decision.
- [ ] Create the Railway application service and PostgreSQL service.
- [ ] Set a long random `SECRET_KEY`; never reuse the local value.
- [ ] Set `DEBUG=false`.
- [ ] Set the Railway public hostname in `ALLOWED_HOSTS`.
- [ ] Set the HTTPS public origin in `CSRF_TRUSTED_ORIGINS`.
- [ ] Set the Railway pre-deploy migration command.
- [ ] Set the static collection build command.
- [ ] Configure `/health` as the Railway health check.
- [ ] Decide whether to keep Django HTTPS redirect disabled behind Railway’s TLS edge or enable it after verifying forwarded-proto health checks.
- [ ] Enable HSTS only after the final domain/subdomain policy is confirmed.
- [ ] Configure persistent media storage: Railway volume at `/data/media` or approved S3-compatible object storage.
- [ ] Configure file type, size, malware, and access controls for uploaded dealer documents/photos.
- [ ] Configure production SMTP or approved notification provider when email is enabled.
- [ ] Add error monitoring, log retention, database metrics, backup alerts, and uptime monitoring.
- [ ] Create and test PostgreSQL backups and restoration.
- [ ] Decide RPO/RTO and document the disaster-recovery procedure.
- [ ] Perform an independent VAPT/security review before public launch.

## 5. Pilot readiness gate

- [ ] Select pilot municipalities and wards.
- [ ] Select 2–3 LPG companies and representative dealers.
- [ ] Create and train applicant, dealer, verifier, approver, NOC, and support users.
- [ ] Load approved municipality, ward, tole, company, brand, and dealer reference data.
- [ ] Run end-to-end tests: registration → household → application → allocation → invoice → delivery.
- [ ] Test duplicate household detection and manual dispute resolution.
- [ ] Test dealer correction, verification, approval, suspension, and rejection paths.
- [ ] Test supply, stock, invoice, and delivery reconciliation.
- [ ] Test role isolation with applicant, dealer, company, local-level, NOC, auditor, and admin accounts.
- [ ] Test backup restore and uploaded-document recovery.
- [ ] Measure application completion, delivery timeliness, reconciliation accuracy, availability, complaints, and user acceptance.
- [ ] Document pilot success thresholds.
- [ ] Obtain formal pilot sign-off and rollout authorization.

## 6. Post-pilot enhancements

- [ ] Native Android client or PWA enhancements based on observed usage.
- [ ] Redis/Celery for SMS, OTP, scheduled alerts, reconciliation, and large reports.
- [ ] ERP/API integrations with LPG companies and NOC systems.
- [ ] Government SSO integration if approved.
- [ ] Horizontal application scaling based on measured demand.
- [ ] Advanced GIS shortage and route-planning features.
