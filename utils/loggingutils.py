import logging


def init_logging(logfile='main.log', mode='a', to_stdout=False):
    handlers = list()
    if logfile is not None:
        handlers.append(logging.FileHandler(logfile, mode=mode))
    if to_stdout:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(format='%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s',
                        datefmt='%y-%m-%d %H:%M:%S', handlers=handlers, level=logging.INFO)


def get_logger(name='main', logfile='main.log', mode='a', to_stdout=False):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler(logfile, mode=mode, encoding='utf-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    if to_stdout:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger
