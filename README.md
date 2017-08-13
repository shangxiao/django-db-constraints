# django-db-constraints

## What is this?

Add database table-level constraints to your Django model's Meta class and have `makemigrations` add the appropriate migration.

```python
class Foo(models.Model):
    bar = models.IntegerField()
    baz = models.IntegerField()

    class Meta:
        db_constraints = {
            'bar_equal_baz': 'check (bar = baz)',
        }
```

This should generate a migration like so:

```python
class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Foo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bar', models.IntegerField()),
                ('baz', models.IntegerField()),
            ],
        ),
        django_db_constraints.operations.AlterConstraints(
            name='Foo',
            db_constraints={'bar_equal_baz': 'check (bar = baz)'},
        ),
    ]
```

The resulting SQL applied:

```sql
CREATE TABLE "sample_foo" ("id" serial NOT NULL PRIMARY KEY, "bar" integer NOT NULL, "baz" integer NOT NULL)
ALTER TABLE "sample_foo" ADD CONSTRAINT "bar_equal_baz" check (bar = baz)
```

## Composite foreign keys

It's possible to support composite foreign keys if you have a unique key on your reference model:

([Why are composite foreign keys useful?](https://github.com/rapilabs/blog/blob/master/articles/same-parent-db-pattern.md))

```python
class Bar(models.Model):
    baz = models.IntegerField()

    class Meta:
        unique_together = ('id', 'baz')


class Foo(models.Model):
    bar = models.ForeignKey(Bar)
    baz = models.IntegerField()

    class Meta:
        db_constraints = {
            'composite_fk': 'foreign key (bar_id, baz) references sample_bar (id, baz)',
        }
```

Results in:

```sql
ALTER TABLE "sample_foo" ADD CONSTRAINT "composite_fk" foreign key (bar_id, baz) references sample_bar (id, baz)
```

## Migration operation ordering

Given that nothing will depend on a constraint operation, they're simply added to the end of the list of operations
for a migration.  This includes operations that drop fields used in a constraint as the database drop will any related
constraints as well (at least with PostgreSQL).

## Caveats

It's possible to end up in a situation where the constraints are declared on the Meta class but do not exist in the database
due to a database dropping a constraint implicitly when a field in the constraint is dropped.

## Installation

```
pip install django-db-constraints
```

in your settings.py:

```python
INSTALLED_APPS = [
    'django_db_constraints',
    …
]
```
