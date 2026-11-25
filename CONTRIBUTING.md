# Contributing to `fragmetrics`

Contributions, bug reports, and metric implementations are welcome!

## Development setup

This project uses [`uv`](https://docs.astral.sh/uv/) for dependency and
environment management (standard `pip` also works via `pyproject.toml`).

```bash
git clone https://github.com/Emanuel-Agu/fragmetrics.git
cd fragmetrics

# Create virtual environment and install dev dependencies
uv sync --dev

# Run the test suite
uv run pytest

# Run the linter
uv run ruff check .
```

To also run the tutorial notebooks:

```bash
uv sync --dev --extra notebooks
uv run jupyter lab
```

## Guidelines

- Keep all functions operating on projected CRS geometries in metres, with
  outputs following the IndiFrag unit conventions (areas in km², perimeters in
  km).
- Add unit tests (synthetic geometries) for every new metric or bug fix, and
  validation tests against `reference/expected_results/` where reference values
  exist.
- Run `uv run ruff check .` and `uv run pytest` before opening a pull request.
- Please open an issue first for major API changes or new metric groups so we
  can align on function signatures and column names.
