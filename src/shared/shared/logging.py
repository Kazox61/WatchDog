import logging

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def setup_logger(name, level=logging.DEBUG):
    stream_handler = logging.StreamHandler()

    # handlers = [stream_handler, file_handler]
    handlers = [stream_handler]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
