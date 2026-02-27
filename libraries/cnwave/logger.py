import logging
import os


def setup_logger(name="cnwave", level=logging.INFO, log_to_file=False):

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional file handler
        if log_to_file:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(
                os.path.join(log_dir, "cnwave.log")
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

