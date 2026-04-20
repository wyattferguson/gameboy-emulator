"""

This module provides a unified logger with loguru fallback to standard logging.

Step-by-step:
1. Attempt to import and bind loguru logger.
2. If unavailable, configure Python logging defaults.
3. Expose a module-level logger object.
4. Keep logging API consistent across runtime modules.
5. Support diagnostics without introducing hard dependency failures.
"""

import logging

try:
    from loguru import logger as logger
except ModuleNotFoundError:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger("gbemu")
