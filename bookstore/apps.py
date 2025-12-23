from django.apps import AppConfig


class BookstoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookstore"
    
    def ready(self):
        # Ensure signal handlers are connected when app is ready
        try:
            import bookstore.signals  # noqa: F401
        except Exception:
            # Avoid breaking app import if signals fail; log if needed
            import logging
            logging.exception("Failed to import bookstore.signals in ready()")