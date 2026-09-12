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

The forms use `django-crispy-forms` with `crispy-bootstrap5`. OTP verification, production brand reference data, and final household-policy decisions remain follow-up work.

## Dealer workflow

The first dealer slice is available at:

```text
/dealer/register/   Submit dealer account, business, location, and evidence
/dealer/dashboard/  View registration and review status
/admin/             Queue verification and approve/reject dealers
```

Dealer registrations begin as `Submitted`. Admin users can move them to `Pending Company Verification`, mark them physically verified, approve them as active, or reject them. Company-scoped permissions and a dedicated verifier/approver UI are follow-up work.
