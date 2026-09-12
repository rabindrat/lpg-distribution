# Security and Operations Specification

## 1. Security objectives

- Protect citizen identity, household, address, application, and delivery data.
- Prevent duplicate entitlement, token replay, unauthorized dealer approval, stock manipulation, and audit tampering.
- Keep government-controlled ownership of source code, repositories, domains, certificates, cloud/API accounts, encryption keys, and production credentials.
- Make every material business decision explainable after the fact.

## 2. Authentication and authorization

- Applicant identity defaults to verified mobile number plus password.
- OTP is required for registration/recovery and may be required for sensitive actions after the policy is approved.
- MFA is required at minimum for NOC users, LPG company approvers, system administrators, and privileged company representatives.
- Enforce a documented password length/complexity policy, failed-login lockout, password history, and session expiry.
- Use Django Groups plus organization/jurisdiction-scoped querysets and object permissions.
- Deny by default; permissions must be tested at both UI and service/API layers.

## 3. Minimum permission matrix

| Capability | Applicant | Dealer | Company verifier | Company approver | NOC | Local-level | Auditor |
|---|---:|---:|---:|---:|---:|---:|---:|
| Manage own account/household | Own | No | No | No | Support-only | No | No |
| Submit application | Yes | On behalf only if approved | No | No | Support-only | No | No |
| View customer PII | Own | Assigned delivery only | Verification need-to-know | Company scope | Authorized oversight | Jurisdiction scope | Approved read-only |
| Register dealer | No | Own draft | No | No | Monitor | No | No |
| Physical verification | No | No | Assigned company dealers | View | Audit/override only if approved | No | Read-only |
| Final dealer approval | No | No | No | Own company | Monitor/audit | No | Read-only |
| Submit company supply | No | No | No | Company scope | View/audit | No | Read-only |
| Record stock/invoice/delivery | No | Assigned dealer | No | Company view | Oversight | No | Read-only |
| View cross-company dashboard | No | No | No | No | Yes | Approved aggregate | Approved reports |
| Change business rules | No | No | No | No | Authorized owner only | No | No |
| View audit records | No | Own actions where allowed | Own actions | Company scope | Yes | Scope-limited | Yes |

The final field-level privacy matrix is TBD and must be approved by the data owner/legal authority.

## 4. Application and infrastructure controls

- TLS for all network communication; secure cookies, CSRF protection, HSTS, and restrictive security headers in production.
- WAF/firewall, reverse proxy, rate limiting, login throttling, and monitored administrative endpoints.
- Secrets managed outside source control; separate credentials per environment and service.
- Database, object storage, and backup encryption with government-controlled key custody.
- Malware/type/size validation for photographs and documents; checksum and access audit for stored files.
- Dependency pinning, patching, code review, migration review, and vulnerability scanning.
- Independent VAPT/penetration testing before production; repeat annually and after major security-impacting releases at the frequency approved by governance.

## 5. Audit and logging

Permanent audit records are required for at least:

- Dealer registration, verification, company approval, rejection, suspension, and reactivation.
- Applicant/household creation, duplicate review, entitlement override, application, allocation, cancellation, and status changes.
- Supply submission/correction, stock receipt/correction, invoice creation/correction, delivery confirmation, and complaint resolution.
- Account, role, organization, configuration, business-rule, and permission changes.

Audit records must be append-only from the application perspective, protected from ordinary admin deletion, queryable by authorized roles, timestamped in UTC with the approved business timezone shown in reports, and retained for the legally approved period.

## 6. Privacy and data sovereignty

- Production database and backups should physically remain in Nepal unless NOC/DoIT/IDMC/legal authority approves an exception.
- Foreign cloud processing of personal/transaction data requires written approval and a documented data-transfer assessment.
- Public views expose aggregates and approved dealer information only.
- Customer PII is restricted by role, organization, and jurisdiction; exports inherit the same scope.
- Retention rules must define account, application/delivery/invoice, audit, photo/document, and complaint periods, including archive/anonymize/delete/legal-hold behavior.

## 7. Backup and disaster recovery

- Target RPO: **15 minutes or better** (proposed; approve formally).
- Target RTO: **1 hour or better** (proposed; approve formally).
- Maintain encrypted backups in a separate Nepal location/failure domain.
- Test restoration at least twice yearly or at the approved quarterly cadence.
- A restore test is not complete until application login, entitlement uniqueness, stock reconciliation, object retrieval, audit integrity, and reports are verified.

## 8. Monitoring and support

Monitor availability, error rate, latency, authentication failures, queue/task failures, database capacity, backup success, storage capacity, stock anomalies, overdue applications, duplicate-review backlog, and integration failures.

Define L1 applicant support, dealer support, L2 application operations, L3 engineering, security-incident escalation, named owners, contact windows, and whether 24×7 support is required. Do not rely on vendor-only accounts for production recovery.

## 9. Pilot controls

Pilot launch requires:

- Representative municipalities/wards, 2–3 LPG companies, and a manageable dealer set.
- Trained users and a support runbook.
- Duplicate detection, delivery timeliness, reconciliation, availability, user acceptance, and complaint-rate success thresholds.
- Named sign-off authority for pilot acceptance and full rollout.
