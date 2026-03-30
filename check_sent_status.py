#!/usr/bin/env python3
"""Legacy wrapper for the shared send-status command."""
import subprocess
import sys


def main():
    args = ["python3", "devnavigator.py", "send-status", *sys.argv[1:]]
    raise SystemExit(subprocess.run(args, check=False).returncode)


if __name__ == "__main__":
    main()
