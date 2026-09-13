# Location catalog import format

`import_location_catalog` accepts a JSON list or an object containing a `locations` list. It is upsert-only: existing rows and user-entered address text are not deleted.

Example:

```json
{
  "locations": [
    {
      "code": "NP-KTM-KMC",
      "level": "municipality",
      "name_en": "Kathmandu Metropolitan City",
      "name_ne": "काठमाडौँ महानगरपालिका",
      "district_name": "Kathmandu",
      "is_kathmandu_valley": true
    },
    {
      "code": "NP-KTM-KMC-W10",
      "level": "ward",
      "name_en": "Ward 10",
      "parent_code": "NP-KTM-KMC",
      "district_name": "Kathmandu",
      "is_kathmandu_valley": true
    },
    {
      "code": "NP-KTM-KMC-W10-BANESHWOR",
      "level": "tole",
      "name_en": "Baneshwor",
      "aliases": ["New Baneshwor", "New-Baneshwar"],
      "parent_code": "NP-KTM-KMC-W10",
      "district_name": "Kathmandu",
      "is_kathmandu_valley": true
    }
  ]
}
```

Run validation first:

```bash
python manage.py import_location_catalog locations/data/kathmandu_valley_locations.json --dry-run
```

The pilot should load an approved catalog for Kathmandu, Lalitpur, and Bhaktapur. Boundary geometry can be added when the approved GIS/PostGIS import format is finalized.
