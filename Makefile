i:
	python scripts/install-skills.py

install: i

i-dry:
	python scripts/install-skills.py --dry-run

install-dry: i-dry

test:
	uvx --python 3.14 pytest==9.2.0 tests
