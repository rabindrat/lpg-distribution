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
```

Set the build command to:

```bash
python manage.py collectstatic --noinput
```

Configure the health check path as `/health`, then generate a Railway public domain. Dealer photos/documents use the local `media/` path by default; for production, mount a Railway volume and set `MEDIA_ROOT=/data/media`, or configure an approved object-storage backend before relying on uploads.
