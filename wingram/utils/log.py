# ===============================================================
# logger
# ===============================================================
import logging

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    fmt = logging.Formatter(
        "> %(levelname)s|%(asctime)s|%(funcName)s| %(message)s", "%H:%M:%S")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)
