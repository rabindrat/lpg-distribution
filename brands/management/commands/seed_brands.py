import json
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Upsert the version-controlled Nepal LPG brand catalog into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=Path,
            help="Optional path to a compatible brand JSON catalog.",
        )

    def handle(self, *args, **options):
        brand_model = apps.get_model("brands", "LPGBrand")
        catalog_path = options["file"] or (
            Path(apps.get_app_config("brands").path) / "data" / "nepal_lpg_brands.json"
        )
        try:
            entries = json.loads(catalog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Could not read brand catalog {catalog_path}: {exc}") from exc

        if not isinstance(entries, list) or not entries:
            raise CommandError("The brand catalog must be a non-empty JSON array.")

        seen_ids = set()
        seen_codes = set()
        with transaction.atomic():
            for entry in entries:
                required = {"id", "code", "name_en", "name_ne", "is_active"}
                if not required.issubset(entry):
                    missing = ", ".join(sorted(required - set(entry)))
                    raise CommandError(f"Brand entry is missing: {missing}")
                if entry["id"] in seen_ids or entry["code"] in seen_codes:
                    raise CommandError(f"Duplicate brand ID or code: {entry}")
                seen_ids.add(entry["id"])
                seen_codes.add(entry["code"])
                brand_model.objects.update_or_create(
                    brand_id=entry["id"],
                    defaults={
                        "code": entry["code"],
                        "name_en": entry["name_en"],
                        "name_ne": entry["name_ne"],
                        "is_active": entry["is_active"],
                    },
                )

        self.stdout.write(self.style.SUCCESS(f"Upserted {len(entries)} LPG brands."))
