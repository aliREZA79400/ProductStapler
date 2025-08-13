import logging


def setup_logger(logger_name, log_file_path):
    """
    Sets up a logger with console (DEBUG) and file (INFO) handlers.

    :param logger_name: str - Name of the logger (e.g., "Mobile_Extractor_IDs")
    :param log_file_path: str - Full path to the log file
    """
    # Get a logger instance
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Create a console handler for printing to the terminal
    console_handler = logging.StreamHandler()
    # Set the console handler's level to DEBUG to show everything
    console_handler.setLevel(logging.DEBUG)

    # Create a file handler for writing to a log file
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    # Set the file handler's level to INFO to save only INFO and higher
    file_handler.setLevel(logging.INFO)

    # Add both handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Create a formatter for the log messages
    formatter = logging.Formatter(
        "{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
    )

    # Apply the formatter to both handlers
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    return logger
