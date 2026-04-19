import logging

try:
    from loguru import logger as logger
except ModuleNotFoundError:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger("gbemu")
