#!/usr/bin/env python3
"""Entry point for the modular Flask backend."""

from __future__ import annotations

import argparse
import os
import sys


if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app
from backend import webapp as legacy


app = create_app()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the modular CYBERGHOST Flask backend")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8011")))
    args = parser.parse_args(argv)

    legacy.validate_email_runtime_config()
    legacy.run_local_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

