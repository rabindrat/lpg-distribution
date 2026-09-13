import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from locations.models import LocationAlias, LocationUnit
from locations.services import normalize_location_text


class Command(BaseCommand):
    help = "Upsert canonical municipality, ward, and tole records from a JSON catalog."

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path)
        parser.add_argument(
            "--source",
            default="location-catalog",
            help="Source label stored on imported aliases.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the catalog without writing records.",
        )

    def handle(self, *args, **options):
        path = options["path"]
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise CommandError(f"Catalog file not found: {path}") from error
        except json.JSONDecodeError as error:
            raise CommandError(f"Catalog is not valid JSON: {error}") from error

        rows = payload.get("locations", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise CommandError("Catalog must be a list or an object with a 'locations' list.")
        rows = [self._feature_to_row(row) for row in rows]
        self._validate_rows(rows)

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"Validated {len(rows)} location rows."))
            return

        with transaction.atomic():
            units = {}
            for row in rows:
                unit, _ = LocationUnit.objects.update_or_create(
                    code=row["code"],
                    defaults={
                        "level": row["level"],
                        "name_en": row["name_en"],
                        "name_ne": row.get("name_ne", ""),
                        "normalized_name": normalize_location_text(row["name_en"]),
                        "aliases": row.get("aliases", []),
                        "district_name": row.get("district_name", ""),
                        "is_kathmandu_valley": row.get("is_kathmandu_valley", False),
                        "is_active": row.get("is_active", True),
                    },
                )
                units[row["code"]] = unit

            for row in rows:
                parent_code = row.get("parent_code")
                parent = units.get(parent_code) if parent_code else None
                if parent_code and parent is None:
                    raise CommandError(
                        f"Parent code {parent_code!r} is not present in the catalog."
                    )
                unit = units[row["code"]]
                if unit.parent_id != (parent.pk if parent else None):
                    unit.parent = parent
                    unit.save(update_fields=["parent", "updated_at"])
                for alias in row.get("aliases", []):
                    LocationAlias.objects.update_or_create(
                        location=unit,
                        normalized_alias=normalize_location_text(alias),
                        defaults={"alias": alias, "source": options["source"], "is_active": True},
                    )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(rows)} location rows."))

    @staticmethod
    def _feature_to_row(row):
        if "properties" not in row:
            return row
        properties = row["properties"]
        return {
            **properties,
            "code": properties.get("code") or properties.get("locallevel_fullcode"),
            "name_en": properties.get("name_en") or properties.get("gapa_napa"),
            "name_ne": properties.get("name_ne") or properties.get("gapa_napa_np", ""),
        }

    @staticmethod
    def _validate_rows(rows):
        levels = {choice for choice, _ in LocationUnit.Level.choices}
        codes = {row.get("code") for row in rows}
        if None in codes or "" in codes:
            raise CommandError("Every location row requires a code.")
        for row in rows:
            if row.get("level") not in levels:
                raise CommandError(
                    f"Invalid location level for {row.get('code')!r}: {row.get('level')!r}"
                )
            if not row.get("name_en"):
                raise CommandError(f"Location {row.get('code')!r} requires name_en.")
            if row.get("parent_code") and row["parent_code"] not in codes:
                raise CommandError(
                    f"Parent code {row['parent_code']!r} is not present in the catalog."
                )
