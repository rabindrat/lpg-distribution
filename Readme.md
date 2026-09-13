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

For a field-by-field explanation of the Django Admin records and common
workflows, see [docs/admin-portal-guide.md](docs/admin-portal-guide.md).

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

## Background allocation worker

Applicant selection is queued through Celery and Redis. PostgreSQL remains the durable source of truth for allocation runs, ranked allocations, application status, and audit records.

Run the worker processes locally with Redis available at `redis://localhost:6379/0`:

```bash
celery -A lpg_app worker --loglevel=INFO
celery -A lpg_app beat --loglevel=INFO
```

The first allocation slice is represented by the `allocations` app and the cylinder inventory slice by `inventory`. Dealers can record received filled cylinders, then queue a run from the dashboard. The worker ranks P1 before P2, then known household-to-dealer distance, application creation time, and application ID; it reserves no more applicants than the available filled cylinders. See [specs/delivery-allocation-plan.md](specs/delivery-allocation-plan.md) for the delivery milestones.

## Location matching

Household and dealer address components are optional. The original text is retained, while `locations.LocationUnit` can be used later to attach canonical municipality, ward, and tole references. Active dealers declare either tole or ward coverage at `/dealer/coverage/`. Allocation uses exact canonical references, normalized address context, or a conservative fuzzy tole match; unresolved locations remain outside automatic selection for review.

The Kathmandu Valley pilot uses Kathmandu, Lalitpur, and Bhaktapur as its geographic scope. [LocalBoundaries](https://github.com/openknowledgenp/localboundaries) is the selected baseline for municipality/district boundary imports. A maintained NOC/dealer reference layer is still required for tole names and aliases because toles are not supplied as a complete administrative boundary level by that dataset.

## Dealer directory seed

The collected dealer directory is stored in `dealers/data/kathmandu_valley_dealers.csv` and can be loaded with:

```bash
python manage.py seed_dealers
```

The seed creates 189 unclaimed directory entries. Each entry stores normalized landline/mobile values in a `phones` array. Registration can select a directory entry to prefill the form; a unique phone match also reconciles automatically. Existing authenticated dealer accounts are never overwritten by a phone collision—OTP verification and account recovery must govern that case.

## Dealer workflow

The first dealer slice is available at:

```text
/dealer/register/   Submit dealer account, business, location, and evidence
/dealer/dashboard/  View registration and review status
/admin/             Queue verification and approve/reject dealers
```

Dealer registrations begin as `Submitted`. Admin users can move them to `Pending Company Verification`, mark them physically verified, approve them as active, or reject them. Company-scoped permissions and a dedicated verifier/approver UI are follow-up work.

## Production Deployment

Set the Railway pre-deploy command to:

```bash
./pre-run.sh
```

This runs migrations, seeds brands/companies/dealers in dependency order, and collects static assets. The script can also seed staging demo data when `SEED_DEMO_DATA=true`; demo records are idempotent and are never enabled by default. Set `DEMO_DATA_PASSWORD` to the password for newly created demo accounts.

Equivalent commands are:

```bash
python manage.py migrate --noinput
python manage.py seed_brands
python manage.py seed_companies
python manage.py seed_dealers
# Optional staging-only data:
SEED_DEMO_DATA=true DEMO_DATA_PASSWORD='change-this-staging-password' python manage.py seed_demo_data
```

Set the build command to:

```bash
python manage.py collectstatic --noinput
```

Configure the health check path as `/health`, then generate a Railway public domain. Dealer photos/documents use the local `media/` path by default; for production, mount a Railway volume and set `MEDIA_ROOT=/data/media`, or configure an approved object-storage backend before relying on uploads.
