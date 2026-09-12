# Technical Architecture Specification

## 1. Architecture decision

Build a **modular Django monolith first**. One deployment contains the applicant, dealer, company, and NOC interfaces. Django Groups and object/queryset-level authorization determine what each role can see and do.

This is the selected first implementation because it minimizes moving parts while retaining clean module boundaries and a later API/mobile path. Do not introduce microservices, Kubernetes, multiple frontend applications, a separate auth service, or an event bus for the MVP.

## 2. Target stack

| Layer | Target |
|---|---|
| Runtime | Python 3.13 (proposed) |
| Backend | Django 5.2 LTS (conversation recommendation; version must be resolved against current scaffold) |
| Database | PostgreSQL + PostGIS |
| Web UI | Django Templates + HTMX + Bootstrap 5 + minimal Alpine.js |
| API | Django REST Framework when mobile/external clients need it |
| Web serving | Nginx + Gunicorn |
| Packaging | Docker / Docker Compose for the pilot |
| Cache/tasks | No Redis/Celery dependency on day one; add Redis/Celery when async workload justifies it |
| Object storage | Local filesystem in development; MinIO/S3-compatible, Nepal-hosted or approved equivalent in production |
| Maps | PostGIS internally; Google Maps only as a presentation/integration layer |

## 3. Django module boundaries

```text
lpg/
├── accounts/
├── households/
├── applicants/
├── brands/
├── companies/
├── dealers/
├── verification/
├── applications/
├── allocations/
├── deliveries/
├── invoices/
├── inventory/
├── supply/
├── gis/
├── complaints/
├── reporting/
├── audit/
└── api/
```

Each module owns its models, state transitions, forms/serializers, services, admin configuration, and tests. Cross-module workflows use explicit service functions or commands rather than hidden signal chains.

## 4. Interface design

### Applicant web/PWA

Representative routes:

```text
/                  home
/login/
/register/
/apply/
/application/<application-id>/
/dealers/
/dealers/map/
/household/
/complaints/
```

The UI is responsive for Android phones, tablets, and desktop browsers. HTMX handles dependent and partial updates such as municipality → ward, brand → dealer, household → duplicate check, and dealer → current application count.

### Staff portals

Use a separate, branded staff entry point backed by Django authentication and permissions. Use Django Admin heavily for NOC, LPG company, verifier, approver, supply, inventory, audit, and reporting operations. Do not expose Django Admin to applicants.

### API surface

The API is not required for the first web release, but the domain must be API-ready. Candidate versioned endpoints:

```text
/api/v1/login
/api/v1/applications
/api/v1/dealers
/api/v1/household
/api/v1/delivery
/api/v1/invoices
```

The API must call the same domain services as the web UI. It must not duplicate entitlement, allocation, stock, or delivery rules.

## 5. Deployment topology

### Pilot topology

```text
Internet
   │
WAF / firewall / TLS termination / reverse proxy
   │
Nginx
   │
Gunicorn → Django application
   ├── PostgreSQL + PostGIS
   ├── local or approved object storage
   └── optional Redis
```

One Ubuntu VM running Docker Compose is sufficient for the pilot. Initial services are Nginx, Django, PostgreSQL/PostGIS, and optionally MinIO. Add Redis/Celery only for SMS/OTP, email, large reports, scheduled reconciliation, duplicate scans, alerts, and overdue calculations that cannot be handled synchronously.

The production database, backups, object storage, and secrets should be hosted in Nepal or an explicitly approved environment. A separate Nepal failure domain is required for disaster recovery.

### Scaling path

```text
1 Django server → 2 Django servers → load balancer
```

Scale only when measured workload, availability, or recovery requirements justify it. The design must avoid assumptions that force premature Kubernetes adoption.

## 6. Core technical rules

- Use PostgreSQL constraints and transactions for critical entitlement and inventory invariants.
- Add a uniqueness constraint on `(household_id, entitlement_month)`.
- Use row locking or an equivalent transaction strategy when allocating entitlement or stock.
- Use PostGIS geometry/point fields for dealer and verification locations with a documented SRID.
- Store photos/documents by object key and metadata, not as large binary fields in PostgreSQL.
- Use immutable event/audit records for corrections rather than overwriting submissions.
- Keep secrets, encryption keys, SSL certificates, DNS, and production credentials under government/NOC-controlled accounts.
- Provide management commands for monthly entitlement preparation, overdue calculation, reconciliation, and data-quality reports before introducing Celery.

## 7. Development sequence

1. Accounts, organizations, brands, dealers, households, and applications.
2. Dealer physical verification and company approval.
3. Entitlement, duplicate detection, priority, and due dates.
4. Allocation, invoice, and delivery.
5. Company supply, dealer stock, reconciliation, and exceptions.
6. NOC dashboard, maps, reports, and complaints.
7. SMS/OTP, asynchronous tasks, versioned API, and native mobile client.

## 8. Environments and quality gates

- Local development uses Docker Compose or the project virtual environment with SQLite only for early UI work; behavior depending on PostgreSQL/PostGIS must be tested against the target database.
- Staging mirrors production authentication, storage, TLS, background jobs, and database extensions as far as practical.
- CI must run migrations, unit tests, workflow/state-transition tests, permission tests, API tests when present, and basic security checks.
- Production release requires database backup verification, migration review, rollback plan, VAPT/penetration testing, and pilot owner sign-off.
