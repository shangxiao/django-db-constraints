.PHONY: dist deploy clean

dist:
	python setup.py sdist
	python setup.py bdist_wheel

deploy: dist
	twine upload dist/*

clean:
	rm -rf dist/ build/ django_db_constraints.egg-info/
