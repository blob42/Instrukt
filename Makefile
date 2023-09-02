.PHONY: all build docs clean clean_docs test

BUILD := poetry build --no-cache

# ensure poetry plugin blixbuild is installed


# version extratected from pyproject.toml
package := $(shell grep "^name" pyproject.toml | head -n1 | cut -d "=" -f 2 | sed 's/ //g' | sed 's/"//g')
docs_dst := $(package)/docs
docs_src := docs/build/markdown
docs := $(shell find $(docs_src) -type f -name "*.md")
version := $(shell grep "^version" pyproject.toml | cut -d "=" -f 2 | sed 's/ //g' | sed 's/"//g')

all: build

docs-%:
	cd docs && poetry run make $*

docs: docs-html docs-markdown sync_docs

build: sync_docs
	$(BUILD)

sync_docs: $(patsubst $(docs_src)/%.md, $(docs_dst)/%.md, $(docs))


$(docs_dst):
	@echo "creating $(docs_dst)"
	mkdir -p $(docs_dst)

$(docs_dst)/%.md:  $(docs_src)/%.md | $(docs_dst)
	@mkdir -p $(dir $@)
	cp $< $@

clean: clean_docs

clean_docs:
	rm -rf $(docs_dst)
