Install requirements

```bash
poetry install
```

Run Django app:

`python manage.py runserver`

Migrate:

```bash
python manage.py makemigrations
python manage.py migrate app_name
python manage.py migrate
```

Admin:
```bash
python manage.py createsuperuser
```

## Applicant flow

The first front-end slice is available at:

```text
/register/       Create an applicant account
/login/          Log in with the registered mobile number
/household/      Enter household and address details
/apply/          Submit an LPG application
/dashboard/      View household and application status
```

The forms use `django-crispy-forms` with `crispy-bootstrap5`. OTP verification and final household-policy decisions remain follow-up work.

## LPG brand catalog

The approved brand catalog is stored in two coordinated layers:

- `brands/data/nepal_lpg_brands.json` is the reviewed, version-controlled seed catalog.
- The `brands.LPGBrand` table is the runtime source of truth used by applicant and dealer forms.

Brand IDs `1` through `55` are explicit and stable. Run the idempotent seed command after migrations (including on Railway):

```bash
python manage.py seed_brands
```

Do not renumber or reuse an existing ID. Retire a brand with `is_active: false`; add new brands with a new ID and then rerun the command.

## Company workflow

The initial company portal is available at `/company/dashboard/`. A company user must be assigned a `CompanyMembership` in Django Admin. The portal is scoped to that membership and currently supports daily branded-cylinder reports for quantities received and delivered to dealers.

Seed the supplied company catalog after seeding brands:

```bash
python manage.py seed_companies
```

The company catalog is stored in `companies/data/nepal_lpg_companies.csv`. Its company IDs are explicit and stable. The company-to-brand relationship is deliberately modeled separately, so additional brands can be linked later without changing the company record.

The initial CSV links each row to the closest existing brand code (for example, Sugam/STC, Himal/Gauri Shankar, Shriram/Shreeram, and Ugrachandi/Lokpriya aliases). These mappings should be confirmed against the final regulatory/company master before production use.

## Dealer workflow

The first dealer slice is available at:

```text
/dealer/register/   Submit dealer account, business, location, and evidence
/dealer/dashboard/  View registration and review status
/admin/             Queue verification and approve/reject dealers
```

Dealer registrations begin as `Submitted`. Admin users can move them to `Pending Company Verification`, mark them physically verified, approve them as active, or reject them. Company-scoped permissions and a dedicated verifier/approver UI are follow-up work.

## Production Deployment

```bash
python manage.py migrate --noinput
python manage.py seed_brands
python manage.py seed_companies
```

Set the build command to:

```bash
python manage.py collectstatic --noinput
```

Configure the health check path as `/health`, then generate a Railway public domain. Dealer photos/documents use the local `media/` path by default; for production, mount a Railway volume and set `MEDIA_ROOT=/data/media`, or configure an approved object-storage backend before relying on uploads.
