# Functional Specification

## 1. Product definition

The Centralized LPG Distribution System manages applicant eligibility, household-level monthly entitlement, dealer authorization, LPG-company supply, dealer stock, allocation, home delivery, invoicing, monitoring, and audit for Nepal. The initial rollout is a Kathmandu Valley pilot.

The system is a single platform with role-specific interfaces:

1. Applicant web/PWA.
2. Dealer portal.
3. LPG company verification and approval portal.
4. NOC / ministry / local-level monitoring portal.

## 2. Goals and non-goals

### Goals

- Prevent duplicate household applications and second-cylinder allocation within the same calendar month.
- Make dealer authorization traceable from self-registration through physical verification and company approval.
- Reconcile company supply, dealer stock, invoices, and verified deliveries.
- Give NOC and authorized government users timely operational visibility without exposing unnecessary citizen data.
- Launch quickly with a maintainable volunteer-friendly stack and a clear path to later mobile/API expansion.

### Non-goals for the first release

- Native Android application.
- Microservices, Kubernetes, event bus, or separate authentication service.
- Full commercial-customer workflow; commercial customers are currently excluded.
- Automated replacement of legal/government decisions that are still TBD.

## 3. Actors and responsibilities

| Actor | Primary responsibilities |
|---|---|
| Applicant / household member | Register, verify account, submit application, view status, present QR/token, acknowledge delivery, raise complaint. |
| Dealer | Maintain profile, receive/confirm stock, view assigned applications, issue invoice, record delivery, report exceptions. |
| LPG company verifier | Perform onsite dealer verification, capture fresh GPS/photo/evidence, recommend correction or verification. |
| LPG company approver | Approve or reject a physically verified dealer; activate, suspend, or inactivate company dealers. |
| LPG company supply user | Submit daily supply and dispatch data and correct it through adjustment records. |
| NOC operator | Monitor all approved operational data, manage exceptions, reporting, audit, and regulatory oversight. |
| Ministry / local-level user | View authorized dashboards and jurisdiction-scoped records. |
| Auditor | Read-only access to approved audit and reporting data. |
| System administrator | Manage accounts, roles, configuration, infrastructure integration, and support; cannot erase audit history. |

## 4. Functional requirements

### FR-1: Applicant accounts and household

- Registration uses a verified mobile number as the default username.
- The system supports password authentication and configurable OTP for registration, recovery, and sensitive actions.
- Multiple applicant accounts may link to one household, but all linked accounts share one household entitlement.
- Household records must support municipality, ward, tole/street, house number, flat/unit, family size, and members where required for verification.
- The system must represent multiple households in one building as separate household records.
- Household identity and duplicate resolution must be auditable and must not depend on mobile number alone.

### FR-2: Eligibility, entitlement, and application

- Initial eligible categories are Labourer, Student, and Individual/Family/Household.
- Commercial customers are out of scope until approved.
- Default policy: one household may receive at most one cylinder per calendar month, regardless of LPG brand.

### User groups and company operations

- The initial access hierarchy has four groups: `NOC / GOV IT`, `Companies`, `Dealers`, and `Applicants`.
- NOC/GOV IT users administer and oversee the system; company users are scoped to their LPG company; dealers are scoped to their own registration and authorizations; applicants are scoped to their own household and applications.
- A company may be linked to multiple LPG brands, and a dealer may hold multiple brand authorizations spanning multiple companies.
- Company users may submit branded daily supply reports containing cylinders received and cylinders delivered to dealers. Detailed dispatch, receipt, stock, invoice, reconciliation, and approval workflows require the later supply-chain modules.
- The monthly reset is proposed for 00:00 on the first day of the calendar month in the approved business timezone.
- The system must distinguish pending/allocated applications from consumed entitlement.
- Default recommendation: consume entitlement only after verified delivery; the final policy is TBD.
- A high-confidence duplicate may be blocked; an ambiguous match must be routed to manual review rather than silently rejected.
- Applicant receives an application ID, priority, due date, brand/preference, assigned dealer when known, current status, and secure QR/token.

### FR-3: Priority and due dates

- P1: Labourer and Student; proposed delivery target is within 2 days.
- P2: Individual/Family/Household; proposed delivery target is within 5 days.
- The priority calculation and deadline must be stored on the application so later rule changes do not rewrite history.
- Missed deadlines create an overdue state and an alert/exception for the appropriate dealer, LPG company, and NOC roles.
- Verification rules for Labourer and Student status are configurable and require approved evidence types.

### FR-4: QR/token control

- QR must contain only a random, non-guessable application token; never customer name, mobile, or address.
- Delivery validation is server-side and must check application status, dealer assignment, token validity, and single-use/replay protection.
- QR expiry policy is TBD; it must be invalidated after verified delivery, cancellation, rejection, or expiry.
- Lost QR reissue must not create a second valid token.

### FR-5: Dealer self-registration and approval

- Dealer registration captures legal/contact details, municipality/ward/tole, complete address, plot/house number, LPG brand authorization, license details, GPS, shop photo, and supporting documents.
- The system may preload dealer directory entries. An applicant can select a matching entry to prefill registration; all listed contact numbers are retained, and a unique phone match can reconcile the directory entry automatically.
- Seeded directory records remain unclaimed until a phone-verified onboarding flow claims them. A collision with an existing authenticated dealer account must not overwrite that account.
- Dealer GPS and at least one fresh shop-front photo are proposed as mandatory.
- A dealer may be authorized for multiple brands only if the company/brand relationship is explicitly represented.
- Physical inspection by an LPG company representative is mandatory under the current proposal.
- Verification captures fresh GPS, fresh photo, checklist results, evidence, verifier identity, timestamp, and location tolerance result.
- Final dealer approval belongs exclusively to the LPG company. NOC monitors, audits, and provides regulatory oversight.
- Suggested dealer states: Draft, Submitted, Pending Company Verification, Verification Correction Required, Physically Verified, Pending Company Approval, Company Approved/Active, Rejected, Suspended, Inactive.
- Verification and final approval should be separate roles where feasible.

### FR-6: Supply, stock, allocation, and reconciliation

- Each LPG company submits daily opening supply, new supply/production, dealer-wise dispatch, total dispatched, remaining balance, date/time, and submitting user.
- Daily reporting deadline is TBD.
- Corrections create adjustment records; original submissions remain immutable.
- Dealer stock is calculated as opening + received − delivered ± approved adjustments = closing.
- Dealer receipt of company dispatch must have an explicit acknowledgement workflow or an approved alternative.
- Negative stock is blocked or escalated and never silently accepted.
- Allocation must consider approved dealer status, brand authorization, availability, priority, geographic rules, and current application state.

### FR-7: Delivery and invoice

- Delivery to the registered residence is the proposed default; final policy is TBD.
- The system supports an official offline workflow: dealer prints/downloads an authorized delivery list, staff delivers and obtains acknowledgement, and dealer records delivery after return.
- Proof-of-delivery method is TBD but must be explicit (for example, QR + customer acknowledgement + dealer confirmation).
- Every delivery requires an invoice/receipt number.
- Invoice number is proposed to be unique per dealer.
- Cancellation/correction creates a new transaction while retaining the original invoice in audit history.
- Fraudulent or incorrect delivery confirmation must identify accountable users and preserve evidence.

### FR-8: Maps and public/restricted information

- PostGIS is the authoritative source for dealer coordinates and geographic queries.
- Google Maps is a visualization/navigation layer only; the application must remain usable if its JavaScript fails.
- Applicant-facing dealer map may show approved dealer name, brand, contact, address, location, and approved aggregate availability/application summary.
- NOC/ministry dashboards may additionally show stock, supply, pending/overdue applications, delivery performance, and geographic shortages according to role.
- Public unauthenticated data is limited to approved aggregates, dealer location/contact, supply statistics, delivery statistics, and geographic availability.
- Customer names, mobile numbers, and residential addresses are restricted by field-level permission.
- Local-level users are restricted to their municipality/ward unless explicitly authorized.

### FR-9: Reporting and complaints

- NOC dashboard KPIs include applications, eligible applications, P1/P2, allocated, delivered, verified delivery, pending, overdue, brand supply, dealer stock, and geographic shortages.
- LPG companies receive company-scoped supply, stock, application, allocation, delivery, and exception reports.
- Municipal/local-level users receive jurisdiction-scoped reporting.
- Excel/PDF export is proposed; confirm whether both are required.
- Complaints must capture category, application/dealer reference, description, status, assignment, timestamps, and resolution/audit history.

## 5. Status and transition principles

- Business entities use explicit state machines; invalid transitions are rejected.
- A transition records actor, organization, timestamp, reason, and supporting evidence where applicable.
- Deletes are not used for operational records. Records are cancelled, rejected, suspended, archived, or anonymized according to retention policy.
- All entitlement overrides, allocation changes, stock corrections, supply corrections, invoice changes, role changes, and approval decisions are permanently auditable.

## 6. MVP acceptance criteria

The pilot is ready for formal acceptance only when it can demonstrate:

- A household can register and submit one eligible application.
- A second account linked to the same household cannot obtain a second monthly entitlement.
- P1/P2 due dates and overdue exceptions are calculated and visible.
- A dealer can register, submit evidence, pass physical verification, and be approved by a company approver.
- A company can submit daily supply and a dealer can reconcile receipt, stock, invoice, and delivery.
- Delivery token replay, invalid dealer use, and invalid application states are rejected.
- NOC can view cross-company dashboards while company and local-level users remain scoped.
- Audit history can explain every approval, correction, override, allocation, invoice, and delivery.
- Backup restoration, security testing, and pilot sign-off are complete.
