import csv
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Upsert the version-controlled Nepal LPG company catalog and brand links."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            help="Optional path to a compatible company CSV catalog.",
        )

    def handle(self, *args, **options):
        company_model = apps.get_model("companies", "LPGCompany")
        link_model = apps.get_model("companies", "CompanyBrand")
        brand_model = apps.get_model("brands", "LPGBrand")
        catalog_path = options["file"] or (
            Path(apps.get_app_config("companies").path)
            / "data"
            / "nepal_lpg_companies.csv"
        )
        try:
            with catalog_path.open(newline="", encoding="utf-8") as catalog_file:
                rows = list(csv.DictReader(catalog_file))
        except OSError as exc:
            raise CommandError(f"Could not read company catalog {catalog_path}: {exc}") from exc

        required = {
            "company_id",
            "code",
            "brand_name",
            "brand_code",
            "company_name",
            "main_location",
            "contact_person",
            "phone",
            "email",
        }
        if not rows:
            raise CommandError("The company catalog must contain at least one row.")
        if not required.issubset(rows[0]):
            missing = ", ".join(sorted(required - set(rows[0])))
            raise CommandError(f"Company catalog is missing columns: {missing}")

        seen_ids = set()
        seen_codes = set()
        with transaction.atomic():
            for row in rows:
                try:
                    company_id = int(row["company_id"])
                except (TypeError, ValueError) as exc:
                    raise CommandError(f"Invalid company ID: {row}") from exc
                if company_id in seen_ids or row["code"] in seen_codes:
                    raise CommandError(f"Duplicate company ID or code: {row}")
                seen_ids.add(company_id)
                seen_codes.add(row["code"])
                try:
                    brand = brand_model.objects.get(code=row["brand_code"])
                except brand_model.DoesNotExist as exc:
                    raise CommandError(
                        f"Brand code {row['brand_code']!r} is not seeded before company import."
                    ) from exc
                company, _ = company_model.objects.update_or_create(
                    company_id=company_id,
                    defaults={
                        "code": row["code"],
                        "legal_name": row["company_name"],
                        "main_location": row["main_location"],
                        "contact_person": row["contact_person"],
                        "phone": row["phone"],
                        "email": row["email"],
                        "is_active": True,
                    },
                )
                link_model.objects.update_or_create(
                    company=company,
                    brand=brand,
                    defaults={"is_primary": True, "is_active": True},
                )

        self.stdout.write(
            self.style.SUCCESS(f"Upserted {len(rows)} LPG company rows and brand links.")
        )
