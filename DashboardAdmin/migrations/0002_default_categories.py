from django.db import migrations

def create_categories(apps, schema_editor):
    Category = apps.get_model("DashboardAdmin", "Category")
    for name in ["anime", "event", "gaming", "geek"]:
        Category.objects.get_or_create(name=name)

def delete_categories(apps, schema_editor):
    Category = apps.get_model("DashboardAdmin", "Category")
    Category.objects.filter(name__in=["anime", "event", "gaming", "geek"]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ("DashboardAdmin", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_categories, delete_categories),
    ]
