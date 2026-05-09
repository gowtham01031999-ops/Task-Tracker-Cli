#!/usr/bin/env python3
"""Thin executable entrypoint for the Task Tracker CLI."""

import sys

from task_tracker.cli import run_cli


if __name__ == "__main__":
    sys.exit(run_cli())
