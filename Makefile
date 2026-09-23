PY := python3

.PHONY: all build matchups clean site

all: build matchups

build:
	$(PY) src/run_01_build.py

matchups:
	$(PY) src/run_02_matchups.py

# Regenerate the GitHub Pages page from README.md. Needs `pip install markdown`.
site:
	$(PY) tools/site.py

clean:
	rm -f figures/*.png output/*.csv data/processed/*
