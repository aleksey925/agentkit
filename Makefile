i:
	python scripts/install-skills.py

install: i

i-dry:
	python scripts/install-skills.py --dry-run

install-dry: i-dry
