import csv
import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Upsert the preloaded Kathmandu Valley dealer/depot directory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            help="Optional path to a normalized dealer CSV catalog.",
        )

    def handle(self, *args, **options):
        dealer_model = apps.get_model("dealers", "DealerRegistry")
        brand_model = apps.get_model("brands", "LPGBrand")
        catalog_path = options["file"] or (
            Path(apps.get_app_config("dealers").path)
            / "data"
            / "kathmandu_valley_dealers.csv"
        )
        try:
            with catalog_path.open(newline="", encoding="utf-8") as catalog_file:
                rows = list(csv.DictReader(catalog_file))
        except OSError as exc:
            raise CommandError(f"Could not read dealer catalog {catalog_path}: {exc}") from exc

        required = {
            "registry_id",
            "brand_code",
            "dealer_name",
            "contact_person",
            "phones",
            "address",
            "district",
            "local_level",
            "ward",
        }
        if not rows:
            raise CommandError("The dealer catalog must contain at least one row.")
        if not required.issubset(rows[0]):
            missing = ", ".join(sorted(required - set(rows[0])))
            raise CommandError(f"Dealer catalog is missing columns: {missing}")

        seen_ids = set()
        with transaction.atomic():
            for row in rows:
                try:
                    registry_id = int(row["registry_id"])
                    phones = json.loads(row["phones"])
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise CommandError(f"Invalid dealer directory row: {row}") from exc
                if registry_id in seen_ids:
                    raise CommandError(f"Duplicate dealer registry ID: {registry_id}")
                if not isinstance(phones, list) or not all(
                    isinstance(phone, str) and phone.isdigit() for phone in phones
                ):
                    raise CommandError(f"Phones must be a JSON array of digit strings: {row}")
                seen_ids.add(registry_id)
                try:
                    brand = brand_model.objects.get(code=row["brand_code"])
                except brand_model.DoesNotExist as exc:
                    raise CommandError(
                        f"Brand code {row['brand_code']!r} is not seeded before dealer import."
                    ) from exc
                dealer_model.objects.update_or_create(
                    registry_id=registry_id,
                    defaults={
                        "brand": brand,
                        "dealer_name": row["dealer_name"],
                        "contact_person": row["contact_person"],
                        "phones": phones,
                        "address": row["address"],
                        "district": row["district"],
                        "local_level": row["local_level"],
                        "ward": row["ward"],
                        "source": "kathmandu-valley-dealer-directory",
                    },
                )

        self.stdout.write(self.style.SUCCESS(f"Upserted {len(rows)} dealer directory entries."))
