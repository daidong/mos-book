# Modern Operating Systems — Build Targets
#
# Prerequisites:
#   cargo install mdbook
#   cargo install mdbook-pdf        (for PDF output)
#   cargo install mdbook-epub       (for EPUB output)

MDBOOK  := mdbook
SRC_DIR := src
OUT_DIR := book

.PHONY: html pdf epub serve clean check

## html     : Build the book as a static HTML site
html:
	$(MDBOOK) build

## serve    : Serve locally with live reload (http://localhost:3000)
serve:
	$(MDBOOK) serve --open

## pdf      : Build PDF (requires mdbook-pdf backend)
pdf:
	MDBOOK_OUTPUT='{"pdf":{}}' $(MDBOOK) build

## epub     : Build EPUB (requires mdbook-epub backend)
epub:
	MDBOOK_OUTPUT='{"epub":{}}' $(MDBOOK) build

## check    : Validate all internal links
check:
	$(MDBOOK) test
	@echo "Checking for broken links..."
	@find $(SRC_DIR) -name '*.md' -exec grep -l '\[.*\](.*\.md)' {} \; | \
		while read f; do \
			perl -nle 'while (/\]\(([^)]+\.md)\)/g) { print $$1 }' "$$f" | while read link; do \
				dir=$$(dirname "$$f"); \
				target="$$dir/$$link"; \
				if [ ! -f "$$target" ]; then \
					echo "BROKEN: $$f -> $$link"; \
				fi; \
			done; \
		done

## clean    : Remove build artifacts
clean:
	rm -rf $(OUT_DIR)

## help     : Show available targets
help:
	@grep '^## ' Makefile | sed 's/^## /  /'
