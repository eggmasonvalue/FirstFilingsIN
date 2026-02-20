#!/bin/bash
set -e

echo "Running Ruff..."
uv run ruff check .

echo "Running Tests..."
uv run env PYTHONPATH=src pytest tests/

echo "All checks passed!"
