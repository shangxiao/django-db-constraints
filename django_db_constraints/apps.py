from django.apps import AppConfig
from django.db.migrations import state
from django.db.models import options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('db_constraints',)
state.DEFAULT_NAMES = options.DEFAULT_NAMES


class DjangoDbConstraintsConfig(AppConfig):
    name = 'django_db_constraints'

    def ready(self):
        from django.core.management.commands import makemigrations, migrate  # noqa
        from .autodetector import MigrationAutodetectorWithDbConstraints  # noqa

        makemigrations.MigrationAutodetector = MigrationAutodetectorWithDbConstraints
        migrate.MigrationAutodetector = MigrationAutodetectorWithDbConstraints
