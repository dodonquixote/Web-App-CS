from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('DashboardAdmin', '0011_add_ad_links'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lang', models.CharField(choices=[('id', 'Indonesian'), ('en', 'English'), ('ja', 'Japanese')], max_length=5)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('desc', models.TextField(blank=True, default='')),
                ('source_hash', models.CharField(blank=True, default='', max_length=64)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='DashboardAdmin.article')),
            ],
        ),
        migrations.AddConstraint(
            model_name='articletranslation',
            constraint=models.UniqueConstraint(fields=('article', 'lang'), name='unique_article_lang'),
        ),
    ]
