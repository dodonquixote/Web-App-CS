from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DashboardAdmin', '0009_sitesetting_ad_top'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='is_pinned',
            field=models.BooleanField(default=False),
        ),
    ]
