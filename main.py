#!/usr/bin/env python3

'''Main entry point for the M811 Configurator application.'''

import logging

from ui.main_window import start_app
from ui.dump_analyzer import start_app

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    raise SystemExit(start_app())
