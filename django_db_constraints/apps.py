from django.apps import AppConfig
from django.db.migrations import operations, state
from django.db.migrations.operations.models import ModelOptionOperation
from django.db.models import options

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('db_constraints',)
state.DEFAULT_NAMES = options.DEFAULT_NAMES


class AlterConstraints(ModelOptionOperation):
    option_name = 'db_constraints'
    reduces_to_sql = True
    reversible = True

    def __init__(self, name, db_constraints):
        self.db_constraints = db_constraints
        super().__init__(name)

    def state_forwards(self, app_label, state):
        model_state = state.models[app_label, self.name_lower]
        model_state.options[self.option_name] = self.db_constraints
        state.reload_model(app_label, self.name_lower, delay=True)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        to_model = to_state.apps.get_model(app_label, self.name)

        if self.allow_migrate_model(schema_editor.connection.alias, to_model):
            from_model = from_state.apps.get_model(app_label, self.name)

            to_constraints = getattr(to_model._meta, self.option_name, {}).keys()
            from_constraints = getattr(from_model._meta, self.option_name, {}).keys()

            table_operations = tuple(
                'DROP CONSTRAINT IF EXISTS {name}'.format(
                    name=schema_editor.connection.ops.quote_name(constraint_name),
                )
                for constraint_name in from_constraints - to_constraints
            ) + tuple(
                'ADD CONSTRAINT {name} {constraint}'.format(
                    name=schema_editor.connection.ops.quote_name(constraint_name),
                    constraint=to_model._meta.db_constraints[constraint_name],
                )
                for constraint_name in to_constraints - from_constraints
            ) + tuple(
                'DROP CONSTRAINT IF EXISTS {name}, ADD CONSTRAINT {name} {constraint}'.format(
                    name=schema_editor.connection.ops.quote_name(constraint_name),
                    constraint=to_model._meta.db_constraints[constraint_name],
                )
                for constraint_name in to_constraints & from_constraints
                if to_model._meta.db_constraints[constraint_name] != from_model._meta.db_constraints[constraint_name]
            )

            if table_operations:
                schema_editor.execute('ALTER TABLE {table} {table_operations}'.format(
                    table=schema_editor.connection.ops.quote_name(to_model._meta.db_table),
                    table_operations=', '.join(table_operations),
                ))

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        return self.database_forwards(app_label, schema_editor, from_state, to_state)


class DjangoDbConstraintsConfig(AppConfig):
    name = 'django_db_constraints'

    def ready(self):
        from django.db.migrations.autodetector import MigrationAutodetector
        generate_created_models = MigrationAutodetector.generate_created_models

        def generate_created_models_patch(self, *args, **kwargs):
            rv = generate_created_models(self, *args, **kwargs)
            for (app_label, migration_operations) in self.generated_operations.items():
                for operation in migration_operations:
                    if isinstance(operation, operations.CreateModel) and 'db_constraints' in operation.options:
                        db_constraints = operation.options.pop('db_constraints')
                        self.add_operation(
                            app_label,
                            AlterConstraints(name=operation.name, db_constraints=db_constraints),
                            # dependencies=related_dependencies, ??
                        )
            return rv

        MigrationAutodetector.generate_created_models = generate_created_models_patch

        # use this rather than _detect_changes which has some wrapping code (we want to insert around the time of generate_altered_unique_together)
        generate_altered_unique_together = MigrationAutodetector.generate_altered_unique_together

        def generate_altered_unique_together_patch(self, *args, **kwargs):
            rv = generate_altered_unique_together(self, *args, **kwargs)

            for app_label, model_name in sorted(self.kept_model_keys):
                old_model_name = self.renamed_models.get((app_label, model_name), model_name)
                old_model_state = self.from_state.models[app_label, old_model_name]
                new_model_state = self.to_state.models[app_label, model_name]

                old_value = old_model_state.options.get('db_constraints', {})
                new_value = new_model_state.options.get('db_constraints', {})
                if old_value != new_value:
                    self.add_operation(
                        app_label,
                        AlterConstraints(
                            name=model_name,
                            db_constraints=new_value,
                        ),
                        # dependencies=dependencies, needed?
                    )

            return rv

        MigrationAutodetector.generate_altered_unique_together = generate_altered_unique_together_patch
