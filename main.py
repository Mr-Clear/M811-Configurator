#!/usr/bin/env python3

'''Main entry point for the M811 Configurator application.'''

import logging
import sys

MIN_PYTHON = (3, 10)

if sys.version_info < MIN_PYTHON:
    min_version = ".".join(str(part) for part in MIN_PYTHON)
    current_version = ".".join(str(part) for part in sys.version_info[:3])
    raise SystemExit(
        f"Python {min_version}+ is required (current: {current_version})."
    )

from ui.main_window import start_app
from ui.dump_analyzer.dump_analyzer import start_app

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    raise SystemExit(start_app())
