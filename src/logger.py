import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import settings

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def _add_file_handler(logger: logging.Logger, path: str, level: int) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding='utf-8',
    )
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(handler)


def setup_logging() -> logging.Logger:
    root_logger = logging.getLogger('energymonitor')
    root_logger.setLevel(logging.INFO)

    if root_logger.handlers:
        return root_logger

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root_logger.addHandler(console_handler)

    _add_file_handler(root_logger, settings.log_file_path, logging.INFO)
    _add_file_handler(root_logger, settings.error_log_file_path, logging.ERROR)

    return root_logger


logger = setup_logging()
