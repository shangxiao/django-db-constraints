from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='django-db-constraints',
    version='0.3.0',
    author='shangxiao',
    description='Add database table-level constraints to your Django model\'s Meta',
    long_description=readme(),
    url='https://github.com/rapilabs/django-db-constraints',
    license='MIT',
    packages=find_packages(),
    install_requires=('django',),
)
