import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CleanSoundStudio.settings')
django.setup()

from DashboardAdmin.models import Category, Article

cats = Category.objects.all()
print('Categories:', [c.name for c in cats])
print('---')
for c in cats:
    qs = Article.objects.filter(category=c, status='published')
    print(f"{c.name}: {qs.count()}")
    for a in qs:
        print('  -', a.title, a.slug)
