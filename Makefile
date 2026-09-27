PY ?= .venv/bin/python

.PHONY: all rules font googlefonts test fontbakery clean
all: rules font test

rules:
	$(PY) build/compile_rules.py

font: rules
	$(PY) build/build_font.py --woff2

googlefonts: rules
	$(PY) build/build_font.py --google-fonts

test:
	$(PY) -m pytest -q tests

fontbakery: googlefonts
	.venv/bin/fontbakery check-googlefonts --configuration fontbakery.yml -l WARN -n --skip-network --json build/out/fontbakery.json --ghmarkdown build/out/fontbakery.md fonts/googlefonts/ttf/TaiwanPinyinKai-Regular.ttf

clean:
	rm -rf build/out fonts/googlefonts
