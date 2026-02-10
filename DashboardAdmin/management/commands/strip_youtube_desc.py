from django.core.management.base import BaseCommand
from DashboardAdmin.models import SiteSetting
from django.utils.html import strip_tags

class Command(BaseCommand):
    help = 'Strip HTML tags from SiteSetting.youtube_desc and save plain text'

    def handle(self, *args, **options):
        try:
            setting = SiteSetting.get_solo()
        except Exception as e:
            self.stderr.write(f'Failed to load SiteSetting: {e}')
            return

        old = setting.youtube_desc or ''
        new = strip_tags(old).strip()

        if old == new:
            self.stdout.write('No change needed: youtube_desc already plain text.')
            return

        # show a short preview
        self.stdout.write('Old (preview):')
        self.stdout.write(old[:500] + ("..." if len(old) > 500 else ""))
        self.stdout.write('\nNew (preview):')
        self.stdout.write(new[:500] + ("..." if len(new) > 500 else ""))

        setting.youtube_desc = new
        setting.save()
        self.stdout.write('\nUpdated SiteSetting.youtube_desc (saved).')
