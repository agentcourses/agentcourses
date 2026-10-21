.PHONY: check check-docs check-receipts check-contracts

CHECK_ROOT ?= $(CURDIR)
DOCS_BASE_REF ?= HEAD
export UV_PYTHON := 3.12.11
export PLAYWRIGHT_BROWSERS_PATH := $(CURDIR)/site/.browsers

check-docs:
	uv run --locked python tools/check_docs.py --root "$(CHECK_ROOT)" --scope present --baseline-ref "$(DOCS_BASE_REF)"

# Sequential recipes stop before tests or builds when source inspection fails.
check: check-docs check-contracts
	uv lock --check
	uv sync --locked --python 3.12.11
	uv run --locked pytest -q
	AC_SITE_MODE=production pnpm --dir site run check
	AC_SITE_MODE=production pnpm --dir site run build
	AC_SITE_MODE=production pnpm --dir site exec playwright test
	@if test -d site/tests/design/fixtures; then \
		AC_SITE_MODE=design pnpm --dir site run build && \
		AC_SITE_MODE=design pnpm --dir site exec playwright test && \
		AC_SITE_MODE=production pnpm --dir site run build; \
	else \
		echo "Foundation production proof complete; the design collection has no fixtures yet."; \
	fi
	$(MAKE) check-receipts CHECK_ROOT="$(CHECK_ROOT)"

# The pending owner choice remains a visible failure after independent checks run.
check-receipts:
	uv run --locked python experiments/call-receipts/probe.py --cases "$(CHECK_ROOT)/experiments/call-receipts/cases"
	uv run --locked python experiments/call-receipts/probe.py --audit-report "$(CHECK_ROOT)/docs/delivery/call-receipts.md"
	uv run --locked python experiments/call-receipts/probe.py --require-decision "$(CHECK_ROOT)/docs/delivery/call-receipts.md"

# The proof harness inspects author data without executing course commands.
check-contracts:
	uv run --locked python tools/check_contracts.py --root "$(CHECK_ROOT)"
