from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DashboardAdmin', '0010_add_is_pinned'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesetting',
            name='ad_left_link',
            field=models.URLField(blank=True, default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='ad_right_link',
            field=models.URLField(blank=True, default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='ad_top_link',
            field=models.URLField(blank=True, default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='sitesetting',
            name='ad_down_link',
            field=models.URLField(blank=True, default='', max_length=1000),
        ),
    ]
