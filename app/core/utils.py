import logging

def configure_logging(level=logging.INFO):
    """Configures the logging system."""
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_error(message, error=None):
    """Handles errors gracefully."""
    logging.error(message)
    if error:
        logging.error(f"Error details: {error}")
    # Consider raising an exception or exiting gracefully
