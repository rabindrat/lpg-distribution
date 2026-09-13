from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class LocationUnit(models.Model):
    """Canonical municipality, ward, or tole reference used for enrichment."""

    class Level(models.TextChoices):
        MUNICIPALITY = "municipality", "Municipality"
        WARD = "ward", "Ward"
        TOLE = "tole", "Tole"

    code = models.CharField(max_length=80, unique=True)
    level = models.CharField(max_length=20, choices=Level.choices)
    name_en = models.CharField(max_length=160)
    name_ne = models.CharField(max_length=160, blank=True)
    normalized_name = models.CharField(max_length=160, db_index=True)
    aliases = models.JSONField(
        default=list,
        blank=True,
        encoder=DjangoJSONEncoder,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
    )
    district_name = models.CharField(max_length=80, blank=True)
    is_kathmandu_valley = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level", "name_en", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "normalized_name", "level"],
                name="one_location_name_per_parent_level",
            )
        ]

    def __str__(self):
        return self.name_en
