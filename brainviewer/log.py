import logging


class BrainviewerStreamHandler(logging.StreamHandler):
    """ Custom stream handler used by brainviewer loggers """
    _FORMAT = '[%(levelname)1.1s %(asctime)s %(filename)s:%(lineno)d] %(message)s'

    def __init__(self, *args, **kwargs):
        logging.StreamHandler.__init__(self, *args, **kwargs)

        formatter = logging.Formatter(fmt=self._FORMAT)
        self.setFormatter(formatter)


def get_logger(name='cml'):
    """ Returns a configured logger to be used throughout the brainviewer package

    Parameters
    ----------
    name: str
        Name of the logger, default "cml"

    """
    logger = logging.getLogger(name)

    for handler in logger.handlers:
        if isinstance(handler, BrainviewerStreamHandler):
            # Logging has already been configured
            return logger

    stream_handler = BrainviewerStreamHandler()
    logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    return logger
