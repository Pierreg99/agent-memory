"""Shared test fixtures."""
import os
import sys

# Ensure the package is importable when tests are run from /workspace
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
