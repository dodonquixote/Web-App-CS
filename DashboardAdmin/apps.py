from django.apps import AppConfig


class DashboardadminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DashboardAdmin'

    def ready(self):
        try:
            import DashboardAdmin.signals  # noqa: F401
        except Exception:
            pass
