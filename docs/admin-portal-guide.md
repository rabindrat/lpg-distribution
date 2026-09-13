# Admin portal quick guide

This guide explains the records shown in Django Admin at `/admin/`. It describes
what each model is for, what its fields mean, and which values are normally
maintained by the system or by a workflow.

## Before editing records

- Use existing catalog records where possible. `LPGBrand.brand_id`,
  `LPGCompany.company_id`, and seeded directory IDs are stable identifiers; do
  not renumber or reuse them.
- A field shown as a relationship points to another admin record. For example,
  `brand` means an `LPGBrand` record, while `dealer` means a `DealerProfile`.
- Dates and timestamps are stored by the application. The application uses UTC
  in the database and displays dates according to the configured admin locale.
- Keep mobile numbers, addresses, coordinates, uploaded documents, and
  complaint text private. Do not copy them into public notes or exports.
- Prefer changing a status or adding a correction record over deleting an
  operational record. Most relationships protect records from deletion.

## How the main records fit together

```text
User ── ApplicantProfile ── Household ── LPGApplication
                                         └── Allocation ── DealerProfile
                                                           ├── BrandAuthorization ── LPGBrand
                                                           ├── CoverageArea ── LocationUnit
                                                           └── CylinderFill ── CylinderUnit

User ── CompanyMembership ── LPGCompany ── CompanyBrand ── LPGBrand
                                      └── CompanySupplyReport
```

## Allocations

### Allocation runs

An allocation run is a request to select applicants for one dealer, one brand,
and a requested number of cylinders. It is the parent record for the ranked
allocations produced by the background worker.

| Field | Meaning | Admin guidance |
|---|---|---|
| `dealer` | Dealer receiving the allocation work | Select the intended dealer. |
| `brand` | LPG brand being supplied | Must match the dealer's active authorization and available stock. |
| `requested_quantity` | Number of applicants/cylinders requested | Required; must be at least 1. |
| `status` | Run lifecycle | `Queued`, `Running`, `Completed`, or `Failed`. Normally worker-managed. |
| `candidate_count` | Eligible applicants considered | System-calculated. Read-only in Admin. |
| `stock_count` | Filled cylinders available when ranking ran | System-calculated. Read-only. |
| `selected_count` | Applicants selected by the run | System-calculated. Read-only. |
| `created_by` | User who queued the run | Record the responsible operator. |
| `error_message` | Failure details, if any | Read-only; useful when investigating a failed run. |
| `created_at`, `started_at`, `completed_at`, `updated_at` | Run audit timestamps | System-managed; read-only. |

### Allocations

An allocation is one ranked reservation created by an allocation run. It links
one LPG application to the dealer, brand, and optional filled cylinder selected
for that application.

| Field | Meaning | Admin guidance |
|---|---|---|
| `run` | Parent allocation run | System-assigned and read-only. |
| `application` | Applicant application being served | One application can have at most one allocation; read-only. |
| `cylinder_fill` | Filled cylinder reserved for the allocation | Optional link to `CylinderFill`; use only the matching dealer and brand. |
| `dealer`, `brand` | Snapshot of who supplies what | System-assigned and read-only. |
| `rank` | Applicant's position in the run | Lower numbers are selected first; read-only. |
| `priority_snapshot` | Priority captured when ranked | `P1` or `P2`; read-only. |
| `location_match_level` | How the household/dealer location matched | May be blank; read-only. |
| `location_match_score` | Numeric match confidence | May be blank; read-only. |
| `distance_meters` | Calculated household-to-dealer distance | May be blank; read-only. |
| `status` | Allocation lifecycle | `Reserved`, `Sale recorded`, `Receipt confirmed`, `Cancelled`, or `Escalated`. |
| `created_at`, `updated_at` | Allocation timestamps | System-managed and read-only. |

## Applicants

### Applicant profiles

An applicant profile connects a login account to the applicant's verified
mobile number and, when known, a household.

| Field | Meaning | Admin guidance |
|---|---|---|
| `user` | Linked Django `User` account | One profile per user. |
| `mobile_number` | Applicant's mobile number | Unique contact value; keep private. |
| `mobile_verified` | Whether mobile verification is complete | Do not mark verified without the approved verification process. |
| `household` | Applicant's associated household | Optional; link only after confirming the household. |

### Complaints

A complaint is an applicant-submitted support or service issue. The current
model stores the report; it does not yet include separate assignment,
resolution, or closure fields.

| Field | Meaning | Admin guidance |
|---|---|---|
| `applicant` | User who submitted the complaint | Keep linked to the original reporter. |
| `confirmation_number` | Reference supplied to or received from the applicant | Optional; searchable. |
| `complaint` | Full complaint text | Treat as sensitive case information. |
| `created_at` | Submission time | System-managed and read-only. |

### Households

A household is the address and family record used to determine eligibility,
location matching, and the monthly LPG entitlement/application relationship.

| Field | Meaning | Admin guidance |
|---|---|---|
| `municipality` | Municipality/local-level name as entered | Preserve the submitted text unless correcting it. |
| `ward` | Ward number or label | Use the local convention consistently. |
| `tole` | Tole or street | Optional address detail. |
| `house_number` | House or plot number | Optional. |
| `flat_unit` | Flat or unit number | Optional. |
| `family_size` | Number of people in the household | Required; must be at least 1. |
| `latitude`, `longitude` | Private household coordinates | Optional; used for dealer-distance ranking. Keep private and verify before correction. |
| `location_unit` | Canonical municipality, ward, or tole reference | Optional; use the matching `LocationUnit` level. |
| `location_match_confidence` | Quality of the canonical location match | `Not resolved`, `User entered`, `Canonical reference`, or `Fuzzy match`. |
| `members` | Optional one-member-per-line verification notes | MVP free text; do not add unnecessary personal data. |
| `created_by` | User who created the household | Record originator. |
| `created_at`, `updated_at` | Record timestamps | System-managed. |

### LPG applications

An LPG application is the household's request for the current entitlement
month. The system prevents more than one application for the same household
and entitlement month.

| Field | Meaning | Admin guidance |
|---|---|---|
| `applicant` | User submitting the request | Keep linked to the submitting account. |
| `household` | Household requesting LPG | Required. |
| `reference` | Public application reference, such as `APP-...` | Generated once; read-only. Use it when communicating about an application. |
| `category` | Applicant category | `Labourer`, `Student`, or `Individual / Family / Household`. |
| `brand_preference` | Whether the applicant wants any brand or a specific brand | `Any available brand` or `Prefer a specific brand`. |
| `preferred_brand` | Requested brand, when applicable | Optional; normally set when the preference is specific. |
| `status` | Application lifecycle | `Submitted`, `Under review`, `Allocated`, `Delivered`, `Cancelled`, or `Rejected`. |
| `priority` | Calculated service priority | `P1` for labourer/student; `P2` for household. Read-only. |
| `due_date` | Calculated target date | Read-only; based on priority. |
| `entitlement_month` | Month to which the application belongs | System-managed and read-only. |
| `created_at`, `updated_at` | Application timestamps | System-managed and read-only. |

## Authentication and authorization

These are Django's built-in authentication records. They control who can log
into Admin and what that user can see or change. They are separate from the
business profiles such as `ApplicantProfile`, `DealerProfile`, and
`CompanyMembership`.

### Groups

A group is a reusable bundle of permissions. Assign users to groups when they
need the same access, rather than granting many individual permissions.

| Field | Meaning | Admin guidance |
|---|---|---|
| `name` | Group name | Use a clear role name, such as `Company users`. |
| `permissions` | Model-level permissions assigned to the group | Grant only the minimum required add/change/view/delete access. |

### Users

A user is a login identity. A user can also be linked to an applicant or dealer
profile, company membership, and Django groups.

| Field | Meaning | Admin guidance |
|---|---|---|
| `username` | Login identifier | Must be unique. |
| `password` | Password managed by Django | Set through the password-change control; never paste a plaintext password into notes. |
| `first_name`, `last_name` | User's name | Use for identification and audit attribution. |
| `email` | Email address | Optional in the current model. Keep private. |
| `is_active` | Whether login is allowed | Turn off for a disabled account; do not delete an account with audit history. |
| `is_staff` | Whether the user may enter Django Admin | Give only to users who need Admin access. |
| `is_superuser` | Full bypass of permission checks | Reserve for platform administrators; use groups for ordinary roles. |
| `groups` | Groups assigned to the user | Controls bundled permissions. |
| `user_permissions` | Direct permissions | Use sparingly and document exceptions. |
| `last_login` | Most recent login | System-managed audit information. |
| `date_joined` | Account creation time | System-managed. |
| `id` | Internal user ID | System identifier; do not use as a public reference. |

## Brands

### LPG brands

An LPG brand is the shared brand catalog used by applications, companies,
dealers, inventory, and allocations.

| Field | Meaning | Admin guidance |
|---|---|---|
| `brand_id` | Stable catalog ID | Generated/seeded identifier; read-only in Admin. Never renumber or reuse. |
| `code` | Stable URL-safe/internal code | Must be unique; avoid changing after records reference it. |
| `name_en` | English brand name | Official display name. |
| `name_ne` | Nepali brand name | Official localized display name. |
| `is_active` | Whether the brand can be used in current workflows | Retire with `false`; do not delete a referenced brand. |
| `created_at`, `updated_at` | Catalog timestamps | System-managed and read-only. |

## Companies

### LPG companies

An LPG company is a bottling or industry company participating in LPG
distribution.

| Field | Meaning | Admin guidance |
|---|---|---|
| `company_id` | Stable company catalog ID | Seeded/stable; read-only in Admin. |
| `code` | Unique internal company code | Keep stable once used in integrations or reports. |
| `legal_name` | Registered company name | Use the official legal name. |
| `main_location` | Main operating location | Keep concise and current. |
| `contact_person` | Primary company contact | Keep current; private business information. |
| `phone` | Company phone contact | Private business information. |
| `email` | Company email contact | Private business information. |
| `is_active` | Whether the company participates in current workflows | Deactivate instead of deleting historical companies. |
| `created_at`, `updated_at` | Company timestamps | System-managed and read-only. |

### Company brands

This is the link between an LPG company and a brand. It exists separately so a
company can support multiple brands.

| Field | Meaning | Admin guidance |
|---|---|---|
| `company` | LPG company | Required. |
| `brand` | LPG brand | Required; the company/brand pair must be unique. |
| `is_primary` | Whether this is the company's primary brand | Use only one primary brand per company unless policy says otherwise. |
| `is_active` | Whether the relationship is currently valid | Deactivate the link when the company stops handling the brand. |
| `created_at`, `updated_at` | Link timestamps | System-managed. |

### Company memberships

A company membership scopes a user to an LPG company and gives that user a
company role. Assigning a membership also adds the broad company-user group;
the membership is the record that identifies which company the user belongs to.

| Field | Meaning | Admin guidance |
|---|---|---|
| `user` | Django user account | Required. |
| `company` | Company the user may work for | Required; a user/company pair may occur only once. |
| `role` | Company responsibility | `Company administrator`, `Supply operator`, or `Company reviewer`. |
| `is_active` | Whether the membership is currently valid | Deactivate to remove company access without deleting the user. |
| `created_at`, `updated_at` | Membership timestamps | System-managed. |

### Company supply reports

A supply report is a company's daily branded-cylinder summary. It records
quantities received and delivered to dealers; it is not a replacement for a
future append-only stock ledger.

| Field | Meaning | Admin guidance |
|---|---|---|
| `company` | Reporting company | Required. |
| `brand` | Brand covered by the report | Required. |
| `report_date` | Business date of the report | One report per company/brand/date. |
| `cylinders_received` | Cylinders received by the company | Required; cannot be negative. |
| `cylinders_delivered_to_dealers` | Cylinders dispatched to dealers | Required; cannot be negative. |
| `notes` | Context or reconciliation notes | Keep factual and concise. |
| `submitted_by` | User who submitted the report | Required; identifies the reporting operator. |
| `created_at`, `updated_at` | Report timestamps | System-managed and read-only. |

## Dealers

### Dealer profiles

A dealer profile is the business, contact, location, evidence, and approval
record for a dealer that may receive allocations.

| Field | Meaning | Admin guidance |
|---|---|---|
| `user` | Dealer's login account | One profile per user; read-only in Admin. |
| `dealer_name` | Trading/business name | Official directory name. |
| `proprietor_name` | Owner/proprietor name | Private identity information. |
| `mobile_number` | Primary dealer mobile number | Unique; keep private. |
| `email` | Dealer email | Keep current and private. |
| `municipality`, `ward`, `tole`, `address`, `house_plot_number` | Dealer location details | Preserve submitted address while canonicalizing through coverage/location records where possible. |
| `phones` | Additional phone numbers | JSON list; keep normalized and private. |
| `brands` | Brands authorized for the dealer | Managed through the `DealerBrandAuthorization` inline; do not treat it as a simple free-form list. |
| `authorization_license` | Main authorization/license reference | Keep aligned with supporting evidence. |
| `gps_latitude`, `gps_longitude` | Dealer coordinates | Required; verify values are within valid latitude/longitude ranges. |
| `shop_photo` | Shop photo upload | Store only approved evidence; access is restricted. |
| `supporting_document` | Optional supporting document | Restricted business/legal evidence. |
| `status` | Dealer onboarding and approval state | `Draft`, `Submitted`, `Pending Company Verification`, `Verification Correction Required`, `Physically Verified`, `Pending Company Approval`, `Company Approved / Active`, `Rejected`, `Suspended`, or `Inactive`. |
| `verification_notes` | Physical verification notes | Record evidence and findings, not unsupported conclusions. |
| `rejection_reason` | Reason for rejection | Required in practice when rejecting; keep clear and actionable. |
| `verified_by`, `verified_at` | Physical verification actor and time | System/workflow-managed and read-only. |
| `approved_by`, `approved_at` | Approval actor and time | System/workflow-managed and read-only. |
| `created_at`, `updated_at` | Profile timestamps | System-managed and read-only. |

Useful Admin actions on dealer profiles are moving submitted dealers to
verification, marking them physically verified, approving verified dealers,
and rejecting non-active dealers. Approval changes the dealer to `Active`.

### Dealer brand authorizations

An authorization says that a dealer may handle a particular LPG brand. A dealer
can have multiple brand authorizations.

| Field | Meaning | Admin guidance |
|---|---|---|
| `dealer` | Authorized dealer | Required. |
| `brand` | Authorized LPG brand | Required; one authorization per dealer/brand pair. |
| `authorization_license` | Brand-specific license/reference | Optional in the current model; add when available. |
| `status` | Authorization lifecycle | `Pending`, `Active`, `Suspended`, or `Expired`. |
| `is_primary` | Whether this is the dealer's primary brand | Use consistently for directory/display purposes. |
| `created_at`, `updated_at` | Authorization timestamps | System-managed. |

Only an active authorization should be used for brand-specific allocation and
stock operations.

### Dealer coverage areas

A coverage area records where a dealer declares it can serve. Coverage is
recorded at either tole or ward precision.

| Field | Meaning | Admin guidance |
|---|---|---|
| `dealer` | Dealer declaring the area | Required. |
| `coverage_level` | Precision of the area | `Tole` or `Ward`. |
| `municipality` | Municipality/local-level name | Keep aligned with the selected location. |
| `ward` | Ward number | Required for ward coverage. |
| `tole` | Tole name | Required for tole coverage; must be blank for ward-only coverage. |
| `location_unit` | Optional canonical location reference | Its level must match `coverage_level`. |
| `created_by` | User who added the coverage | Required. |
| `is_active` | Whether the area is currently served | Deactivate when the dealer stops covering it. |
| `created_at`, `updated_at` | Coverage timestamps | System-managed. |

### Dealer directory entries

A directory entry is a seeded dealer/depot record from the reference directory.
It may be unclaimed, claimed, onboarded, or merged into a verified dealer
profile. It is not the same thing as an approved `DealerProfile`.

| Field | Meaning | Admin guidance |
|---|---|---|
| `registry_id` | Stable source-directory ID | Read-only; do not renumber. |
| `brand` | Brand listed by the source directory | Required. |
| `dealer_name` | Directory business name | Source value; correct only through the approved stewardship process. |
| `contact_person` | Directory contact | Source value; private. |
| `phones` | Directory phone numbers | JSON list; private. |
| `address` | Directory address | Source value; private. |
| `district`, `local_level`, `ward` | Directory geography | Source values used for search/prefill. |
| `status` | Directory/onboarding state | `Unclaimed`, `Claimed`, `Onboarded`, or `Merged`. |
| `onboarded_dealer` | Linked verified dealer profile | Optional one-to-one link. |
| `source` | Origin of the directory data | Keep the source identifier when importing or reconciling. |
| `created_at`, `updated_at` | Directory timestamps | System-managed and read-only. |

## Inventory

### Cylinder units

A cylinder unit is the reusable physical cylinder asset. The same unit can have
multiple fill cycles over time.

| Field | Meaning | Admin guidance |
|---|---|---|
| `dealer` | Dealer currently responsible for the cylinder | Required. |
| `brand` | Cylinder brand | Required; keep aligned with fills and authorizations. |
| `asset_code` | Internal asset identifier, such as `CYL-...` | Generated and read-only. |
| `manufacturer_serial_number` | Manufacturer's serial number | Optional but unique when supplied. |
| `capacity_kg` | Cylinder capacity in kilograms | Optional; cannot be negative. |
| `status` | Physical asset state | `Active`, `Damaged`, or `Retired`. |
| `created_at`, `updated_at` | Asset timestamps | System-managed and read-only. |

### Cylinder fills

A cylinder fill is one filled-inventory cycle for a reusable cylinder. It tracks
the filled item as it moves through dealer stock and the allocation/receipt
workflow.

| Field | Meaning | Admin guidance |
|---|---|---|
| `cylinder_unit` | Reusable cylinder asset that was filled | Required. |
| `dealer` | Dealer holding the filled cylinder | Required. |
| `brand` | Brand of the fill | Required; should match the cylinder and supply context. |
| `fill_reference` | Generated fill event reference, such as `FILL-...` | Read-only; use for reconciliation. |
| `source_reference` | Company/dispatch/source document reference | Optional; useful for matching supply reports. |
| `received_by` | User who recorded receipt | Required. |
| `filled_at` | Time the fill was produced/received | Required operational timestamp. |
| `status` | Fill lifecycle | `In dealer stock`, `Reserved`, `Sold, receipt pending`, `Receipt confirmed`, `Returned empty`, `Damaged`, or `Cancelled`. |
| `created_at`, `updated_at` | Fill timestamps | System-managed and read-only. |

## Locations

### Location units

A location unit is the canonical reference for a municipality, ward, or tole.
It supports consistent matching of household and dealer addresses.

| Field | Meaning | Admin guidance |
|---|---|---|
| `code` | Unique canonical location code | Keep stable once used by matching or imports. |
| `level` | Administrative precision | `Municipality`, `Ward`, or `Tole`. |
| `name_en` | English name | Official display name. |
| `name_ne` | Nepali name | Optional localized name. |
| `normalized_name` | Search/matching form of the name | System/import-managed; used for matching. |
| `aliases` | JSON list of alternate names/spellings | Use stewarded aliases; do not put unrelated locations here. |
| `parent` | Parent location in the hierarchy | A ward/tole should point to its parent where known. |
| `district_name` | District label | Optional reference data. |
| `is_kathmandu_valley` | Whether the location is in the pilot valley scope | Use the approved geographic scope. |
| `is_active` | Whether the location is available for matching | Deactivate obsolete records instead of deleting referenced locations. |
| `created_at`, `updated_at` | Reference-data timestamps | System-managed and read-only. |

Location units include an inline list of `LocationAlias` records in Admin.

### Location aliases

A location alias is a stewarded alternate spelling or local name that maps to a
canonical `LocationUnit`.

| Field | Meaning | Admin guidance |
|---|---|---|
| `location` | Canonical location receiving the alias | Required. |
| `alias` | Alternate spelling/local name | Enter the actual source spelling. |
| `normalized_alias` | Normalized value used for search | Generated on save; read-only. |
| `source` | Where the alias came from | Defaults to `NOC / dealer stewardship`; keep provenance. |
| `is_active` | Whether the alias participates in matching | Deactivate bad or obsolete aliases. |
| `created_at`, `updated_at` | Alias timestamps | System-managed and read-only. |

## Recommended admin order for common tasks

1. Maintain active `LPGBrand`, `LPGCompany`, and `LocationUnit` reference data.
2. Create or activate the `User`, then assign `Groups` or direct permissions.
3. Add `CompanyMembership` for company users and `CompanyBrand` for supported
   company/brand pairs.
4. Review `DealerProfile`, then add active `DealerBrandAuthorization` and
   `DealerCoverageArea` records.
5. Maintain `CylinderUnit` and `CylinderFill` records before queuing an
   `AllocationRun`.
6. Review `ApplicantProfile`, `Household`, and `LPGApplication` records; use
   the application reference when investigating a case.
7. Use `Complaints` for applicant issues and keep any follow-up evidence in
   approved private channels until a dedicated case workflow is available.

## Fields that should normally not be hand-edited

The application intentionally generates or records these values: public
references (`APP-...`, `FILL-...`, and cylinder asset codes), allocation ranking
and matching results, application priority/due date/entitlement month, location
normalizations, approval/verification actors and timestamps, and created or
updated timestamps. If one is wrong, correct the source record or use the
approved workflow rather than forcing a downstream value.
