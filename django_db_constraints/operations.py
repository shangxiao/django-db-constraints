from django.db.migrations.operations.models import ModelOptionOperation


class AlterConstraints(ModelOptionOperation):
    option_name = 'db_constraints'
    reduces_to_sql = True
    reversible = True

    # xxx
    _auto_deps = []

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
