from django.db import models


class LPGBrand(models.Model):
    """The stable brand catalog used by all LPG workflows."""

    brand_id = models.PositiveIntegerField(primary_key=True)
    code = models.SlugField(max_length=80, unique=True)
    name_en = models.CharField("English name", max_length=160)
    name_ne = models.CharField("Nepali name", max_length=160)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["brand_id"]
        verbose_name = "LPG brand"
        verbose_name_plural = "LPG brands"

    def __str__(self):
        return self.name_en
