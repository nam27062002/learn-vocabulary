from django.apps import AppConfig


class VocabularyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vocabulary'
    
    def ready(self):
        """Import signals when the app is ready."""
        import vocabulary.signals
