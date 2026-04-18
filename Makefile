# Modern Operating Systems — Build Targets
#
# Prerequisites:
#   cargo install mdbook
#   Chrome or Chromium on PATH (for PDF output via print.html)
#   cargo install mdbook-epub    (optional, for EPUB output)

MDBOOK   := mdbook
SRC_DIR  := src
OUT_DIR  := book
PDF_OUT  := book.pdf

# Locate a headless-capable Chrome/Chromium binary.
# Override by exporting CHROME=/path/to/chrome on the command line.
CHROME ?= $(shell \
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$$(command -v google-chrome 2>/dev/null)" \
    "$$(command -v chromium 2>/dev/null)" \
    "$$(command -v chromium-browser 2>/dev/null)"; \
  do \
    [ -x "$$c" ] && echo "$$c" && break; \
  done)

.PHONY: html pdf epub serve clean check

## html     : Build the book as a static HTML site
html:
	$(MDBOOK) build

## serve    : Serve locally with live reload (http://localhost:3000)
serve:
	$(MDBOOK) serve --open

## pdf      : Render the single-page print.html to a PDF via headless Chrome
pdf: html
	@if [ -z "$(CHROME)" ]; then \
	  echo "ERROR: no Chrome/Chromium found. Install Google Chrome or Chromium,"; \
	  echo "       or pass CHROME=/path/to/chrome."; \
	  exit 1; \
	fi
	"$(CHROME)" --headless --disable-gpu --no-pdf-header-footer \
	  --print-to-pdf="$(CURDIR)/$(PDF_OUT)" \
	  "file://$(CURDIR)/$(OUT_DIR)/print.html"
	@echo "PDF written to $(PDF_OUT) ($$(du -h $(PDF_OUT) | awk '{print $$1}'))"

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
	rm -rf $(OUT_DIR) $(PDF_OUT)

## help     : Show available targets
help:
	@grep '^## ' Makefile | sed 's/^## /  /'
