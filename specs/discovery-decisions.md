# Pre-Development Discovery Decision Register

This register turns the conversation’s questionnaire into implementation gates. “Proposed” is a design recommendation, not an approved government policy. Every TBD needs an answer, responsible authority, supporting document, and decision date before the affected production behavior is finalized.

## 1. Proposed defaults to validate

| Area | Proposed default | Approval needed from |
|---|---|---|
| Entitlement | One cylinder per household per calendar month, irrespective of brand | Business-rule owner |
| Monthly reset | 00:00 on the first day of the calendar month | Business-rule owner |
| Entitlement consumption | Consume after verified delivery; track pending/allocated separately | Business-rule owner / legal |
| Duplicate handling | Block high-confidence duplicates; manually review ambiguous matches | NOC / local verification authority |
| Priority | P1 Labourer/Student within 2 days; P2 household within 5 days | Business-rule owner |
| Applicant login | Verified registered mobile number plus password | Security/data owner |
| Family accounts | Multiple accounts may link to one household; one shared entitlement | Business-rule owner / privacy |
| QR payload | Random secure token only; no citizen PII | Security/data owner |
| Dealer evidence | Fresh shop photo and GPS during registration/verification | LPG companies / NOC |
| Dealer approval | LPG company has exclusive final approval; NOC monitors and audits | NOC / LPG companies |
| Correction policy | Append adjustment/correction records; never overwrite original submission | Audit/legal owner |
| Stock | Negative stock blocked or escalated | Supply-chain owner |
| Public data | Aggregates, approved dealer contact/location, supply/delivery statistics, geographic availability | Data/privacy owner |
| Local access | Municipality/ward scope by default | NOC / local government |
| Hosting | Nepal-hosted approved data centre/cloud; separate Nepal DR site | NOC/DoIT/IDMC |
| MFA | NOC, approvers, administrators, privileged company users | Security owner |
| VAPT | Independent pre-production test and recurring testing | Security owner |
| DR | RPO ≤15 minutes, RTO ≤1 hour, periodic restore tests | Infrastructure owner |
| Ownership | Government/NOC controls source code, repository, domains, certificates, API accounts, keys, and credentials | Project owner/legal/procurement |
| Pilot | Pilot before full Kathmandu Valley rollout | Project owner |

## 2. Unresolved business decisions

### Ownership and governance

- Official system owner, data controller, day-to-day operator, and authority for changing business rules.
- Official organization/user classes and final authority for reports, dealer requirements, entitlement, and priority rules.

### Eligibility and household identity

- Legal definition of household: residence, family relationship, cooking unit, household head, government record, or another rule.
- Required evidence for Labourer and Student status.
- Required proof for separate households at one address, rented rooms, and shared residences.
- Authority and evidence standard for duplicate-household disputes.

### Entitlement and application lifecycle

- Whether cancellation before delivery restores eligibility in the same month.
- Failed-delivery attempts, rescheduling period, and expiry behavior.
- Whether brand switching is allowed before allocation, only on stock shortage, or never.
- Whether applicant selects a dealer, selects from nearby approved dealers, or receives system assignment.
- QR expiry and lost-QR reissue rules.

### Dealer and supply-chain operations

- Dealer GPS-distance tolerance between declared and verified locations.
- Whether one employee may both verify and approve a dealer.
- Daily company-supply reporting deadline and whether entry, Excel upload, or API is used.
- Whether dealers must acknowledge company receipt and what constitutes acknowledgement.
- Whether home delivery must be to the registered residence.
- Official proof-of-delivery combination and accountability for fraudulent confirmation.
- Invoice numbering scope, correction/cancellation behavior, and required invoice fields.

### GIS, privacy, and sovereignty

- Google Maps approval or alternative government GIS.
- Field-level visibility for names, mobiles, addresses, stock, and transaction details.
- Legal database owner, Nepal data-residency requirement, backup residency, and foreign-cloud restrictions.
- Approved NOC/IDMC/DoIT hosting and data-centre environments.

### Infrastructure and security

- Approved operating systems, PostgreSQL/PostGIS, containers, Redis, and object storage.
- Public API/DMZ/VPN topology and available peak bandwidth.
- Password policy, MFA scope, VAPT cadence, audit retention, and audit-reader roles.

### Retention, reporting, integrations, and operations

- Retention periods and post-retention action for accounts, applications, deliveries, invoices, photos, documents, complaints, and audit records.
- NOC, LPG-company, and municipality report catalog; Excel/PDF export requirement.
- Existing NOC integrations, LPG ERP integrations, SMS/OTP provider, and government SSO.
- L1/L2/L3 support ownership, major-incident escalation, support hours, and 24×7 requirement.

### Pilot and rollout

- Pilot municipalities/wards, participating companies/dealers, success thresholds, and formal acceptance authority.

## 3. Required sign-off package

Before production development begins, collect approved versions of:

- Business rules and household definition.
- Entitlement, priority, allocation, delivery, invoice, and dealer approval workflows.
- Data dictionary and privacy/field-visibility matrix.
- Hosting, sovereignty, infrastructure, security, audit, retention, backup, and DR requirements.
- Integration specifications and operational/support model.
- Pilot plan, success criteria, rollout authority, and procurement/vendor ownership terms.

Required signatories:

```text
NOC: ______________________________
LPG Companies: ____________________
NOC IT / Engineering: ______________
IDMC / Infrastructure Authority: _____
DoIT / Relevant Government IT Authority: __________
Legal / Privacy: ____________________
Procurement: ________________________
Project Owner: ______________________
Decision date: _______________________
```
