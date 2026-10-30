.PHONY: check check-python check-package check-site

# The whole gate: Python tests, the installable package and the documentation site.
check: check-python check-package check-site

# Tests cover the validator rules, the examples, their fixtures, conformance and the size budget.
check-python:
	uv lock --check
	uv sync --locked
	uv run --locked pytest -q

# The wheel must carry the schemas and conformance cases it reads at run time.
check-package:
	rm -rf .runtime/dist
	uv build --wheel --out-dir .runtime/dist
	uv run --locked python -c "import sys, zipfile, glob; names = zipfile.ZipFile(glob.glob('.runtime/dist/*.whl')[0]).namelist(); missing = [n for n in ('agentcourses/schemas/course.schema.json', 'agentcourses/conformance_cases/01-minimal-course/expected.json') if n not in names]; sys.exit(f'wheel is missing {missing}' if missing else 0)"

check-site:
	pnpm --dir site install --frozen-lockfile --config.confirmModulesPurge=false
	pnpm --dir site run check
	pnpm --dir site run build
