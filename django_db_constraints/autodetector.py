from django.db.migrations import operations
from django.db.migrations.autodetector import MigrationAutodetector

from .operations import AlterConstraints


class MigrationAutodetectorWithDbConstraints(MigrationAutodetector):
    db_constraints_operations = []

    def generate_created_models(self, *args, **kwargs):
        rv = super().generate_created_models(*args, **kwargs)
        for (app_label, migration_operations) in self.generated_operations.items():
            for operation in migration_operations:
                if isinstance(operation, operations.CreateModel) and 'db_constraints' in operation.options:
                    db_constraints = operation.options.pop('db_constraints')
                    self.db_constraints_operations.append((
                        app_label,
                        AlterConstraints(name=operation.name, db_constraints=db_constraints),
                    ))
        return rv

    def generate_altered_unique_together(self, *args, **kwargs):
        rv = super().generate_altered_unique_together(*args, **kwargs)

        for app_label, model_name in sorted(self.kept_model_keys):
            old_model_name = self.renamed_models.get((app_label, model_name), model_name)
            old_model_state = self.from_state.models[app_label, old_model_name]
            new_model_state = self.to_state.models[app_label, model_name]

            old_value = old_model_state.options.get('db_constraints', {})
            new_value = new_model_state.options.get('db_constraints', {})
            if old_value != new_value:
                self.db_constraints_operations.append((
                    app_label,
                    AlterConstraints(
                        name=model_name,
                        db_constraints=new_value,
                    ),
                ))

        return rv

    def _sort_migrations(self, *args, **kwargs):
        rv = super()._sort_migrations()
        for app_label, operation in self.db_constraints_operations:
            self.generated_operations.setdefault(app_label, []).append(operation)
        return rv
