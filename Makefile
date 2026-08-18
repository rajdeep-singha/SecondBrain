# Prefer the project virtualenv if it exists, else fall back to python3.
PY ?= $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

.PHONY: help install catalog embed index search distill

help:
	@echo "SecondBrain — make targets"
	@echo "  make install        Install python deps (fastembed, sqlite-vec)"
	@echo "  make catalog        Build INDEX.md + .brain/manifest.json (stdlib only)"
	@echo "  make embed          (Re)build the semantic vector DB (.brain/index.db)"
	@echo "  make index          catalog + embed (the usual after adding notes)"
	@echo "  make search q=\"...\"  Semantic search  (optional: d=<domain> k=<n>)"
	@echo "  make distill        Show how to distill inbox items into notes"

install:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

catalog:
	$(PY) scripts/build_index.py

embed:
	$(PY) scripts/embed.py

index: catalog embed

# usage: make search q="aptos coin transfer" d=aptos k=5
search:
	@$(PY) scripts/search.py "$(q)" $(if $(d),--domain $(d),) $(if $(k),-k $(k),)

distill:
	@echo "Drop raw exports into sessions/inbox/ or tweets/inbox/,"
	@echo "then in Claude Code run the 'distill-session' skill to file them as notes."
	@echo "After distilling, run: make index"
