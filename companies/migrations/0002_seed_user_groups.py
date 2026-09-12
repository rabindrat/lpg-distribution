from django.db import migrations


GROUP_NAMES = ("NOC / GOV IT", "Companies", "Dealers", "Applicants")


def create_default_groups(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    for name in GROUP_NAMES:
        group_model.objects.get_or_create(name=name)


def remove_default_groups(apps, schema_editor):
    group_model = apps.get_model("auth", "Group")
    group_model.objects.filter(name__in=GROUP_NAMES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("companies", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_default_groups, remove_default_groups),
    ]
