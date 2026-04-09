import logging, os 
from datetime import datetime, timezone

file_path= os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.log'))

def get_logger(name="debug"):
    global file_path
    logger= logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        handler= logging.FileHandler(filename= file_path, encoding="utf-8")
        formatter= logging.Formatter(fmt= "%(asctime)s %(message)s", datefmt= "%d/%m/%Y - %H:%M:%S")

        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate= False

    return logger


#log= get_logger()
#log.info('TEST')