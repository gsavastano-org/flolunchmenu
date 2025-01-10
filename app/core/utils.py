import logging
import imghdr
from pathlib import Path

def configure_logging(level=logging.INFO, log_file=None):
    """Configures the logging system."""
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

def handle_error(message, error=None):
    """Handles errors gracefully."""
    logging.error(message)
    if error:
        logging.error(f"Error details: {error}")

def is_valid_jpeg(file_path):
    """Checks if a file is a valid JPEG image using pathlib."""
    return imghdr.what(Path(file_path)) == 'jpeg'
