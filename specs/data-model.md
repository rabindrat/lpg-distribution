# Data Model Specification

## 1. Modeling principles

- Use explicit organization ownership and geographic scope on records that staff users can access.
- Prefer stable internal IDs plus human-readable public references such as `APP-12345`.
- Store lifecycle status and immutable transition history separately.
- Preserve original submissions and corrections; do not overwrite operational evidence.
- Keep personal data and large files out of public URLs and logs.

## 2. Core entities

### Identity and organization

- `User`: authentication identity, verified mobile/email, status, last-login metadata.
- `Role`: applicant, dealer, company verifier, company approver, company supply user, NOC operator, ministry, local-level, auditor, administrator.
- `Organization`: NOC, LPG company, municipality, ward, ministry, service provider, or approved authority.
- `UserOrganizationMembership`: role, organization, jurisdiction, start/end dates, active flag.

### Geography and household

- `Municipality`, `Ward`, and optional `Tole` reference data.
- `Household`: canonical household identity, address, location where appropriate, family size, status, verification state, and ownership metadata.
- `HouseholdMember`: name/relationship/status only where required by approved policy.
- `HouseholdAccountLink`: links one or more users to a household with evidence and audit history.
- `DuplicateReview`: candidate household matches, confidence, reviewer, evidence, decision, and reason.

### LPG supply chain

- `LPGCompany` / organization subtype.
- `LPGBrand`: company, name, active state, regulatory metadata.
- `Dealer`: legal/contact profile, address, GPS, ownership, status, and organization scope.
- `DealerBrandAuthorization`: dealer-brand relationship, license/reference, validity, approval state.
- `DealerRegistration`: submitted registration snapshot and current workflow state.
- `DealerVerification`: onsite checklist, verifier, GPS, distance result, photos/documents, decision, and timestamp.
- `SupplySubmission`: company daily supply/production/dispatch snapshot.
- `SupplyAdjustment`: approved correction linked to an original submission.
- `DealerStockLedger`: append-only receipts, deliveries, adjustments, and calculated balance.
- `Allocation`: application-to-dealer/brand assignment, priority, timestamps, and reason.

### Customer transaction

- `Entitlement`: one household and one calendar month, with state and consumption metadata.
- `Application`: applicant/household, priority category, brand preference, dealer, due date, status, and public reference.
- `ApplicationToken`: hashed random token, issue/expiry/invalidated timestamps, and use metadata; never store a reusable plaintext token.
- `Delivery`: application, dealer, delivery staff/actor, location/evidence, acknowledgement, status, and verified timestamp.
- `Invoice`: dealer, delivery, invoice number, amount/quantity fields as approved, status, and correction links.
- `Complaint`: reporter, reference entity, category, assignment, status, resolution, and audit history.

### Governance and audit

- `AuditEvent`: actor, organization, action, entity type/ID, before/after summary or diff, reason, IP/device metadata if approved, timestamp, and correlation ID.
- `WorkflowTransition`: explicit state transition record for approvals, verification, applications, allocation, delivery, stock, and invoices.
- `Document`: object-storage key, media type, checksum, owner entity, classification, retention, and access policy.
- `ReportExport`: requester, filters, scope, generated file key, expiry, and access audit.

## 3. Relationships

```text
User ──< HouseholdAccountLink >── Household
Household ──< Entitlement (one per calendar month)
Household ──< Application ──< Allocation >── Dealer ──< DealerBrandAuthorization >── LPGBrand
Application ──< ApplicationToken
Application ──0..1 Delivery ──1 Invoice
LPGCompany ──< SupplySubmission ──< SupplyAdjustment
Dealer ──< DealerStockLedger
Dealer ──< DealerVerification
User ──< AuditEvent
```

## 4. Required constraints and invariants

### Entitlement

- Unique `(household_id, entitlement_month)`.
- Only one active/consumed entitlement can exist for a household/month.
- Verified delivery consumes the entitlement under the final approved policy.
- Cancellation/rejection must not silently create a second entitlement record.

### Application and delivery

- A delivered application cannot be delivered again.
- A token is single-use and invalid after delivery, cancellation, rejection, or expiry.
- Delivery requires an eligible application, approved/active dealer, valid allocation where allocation is mandatory, and invoice number.
- An invoice number is unique within the approved scope, proposed as per dealer.

### Stock and supply

- Ledger entries are append-only; corrections are adjustments.
- A transaction that would make stock negative is rejected or escalated.
- Company dispatch and dealer receipt must be linkable for reconciliation.
- Closing stock must be reproducible from opening balance and ledger entries.

### Dealer approval

- Only the owning LPG company can perform final approval.
- A dealer cannot receive allocations for a brand without an active authorization.
- Verification and approval actors must be recorded separately when the separation policy is enabled.

### Access scope

- Company users see only their company and authorized dealer/application/supply records.
- Local-level users see only their assigned municipality/ward unless elevated.
- Auditors have read-only access and cannot mutate operational records or delete audit data.

## 5. Audit fields on operational records

At minimum, operational records include `created_at`, `updated_at`, `created_by`, `updated_by`, organization owner, current status, and status-change reason. Approval, correction, override, allocation, invoice, and delivery records additionally include an immutable audit/event reference.

## 6. Sensitive data handling

- Encrypt database storage and backups in production.
- Avoid putting names, mobile numbers, addresses, or tokens in QR payloads, URLs, analytics events, or application logs.
- Use field-level redaction in admin lists, exports, and support views.
- Apply retention, archive, anonymization, deletion, and legal-hold rules only after the data-governance decision register is approved.
