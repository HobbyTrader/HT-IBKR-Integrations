import os
import time
import json
import logging
from importlib.resources import files

def load_config() -> json:
    _config_path = files('ht_tools').joinpath('config.json')
    if not _config_path.is_file():
        # Non blocking warning since logging is not setup yet
        print(f"> WARNING - Config File not found: {_config_path}")    
    
    with open(_config_path) as file:
        return json.load(file)


def SetupLogger(log_level):
    if not os.path.exists("log"):
        os.makedirs("log")

    time.strftime("pyibapi.%Y%m%d_%H%M%S.log")

    recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'

    timefmt = '%y%m%d_%H:%M:%S'

    # logging.basicConfig( level=logging.DEBUG,
    #                    format=recfmt, datefmt=timefmt)
    logging.basicConfig(filename=time.strftime("log/IBKRIntegration.%y%m%d_%H%M%S.log"),
                        filemode="w",
                        level=logging.INFO,
                        format=recfmt, datefmt=timefmt)
    logger = logging.getLogger()
    console = logging.StreamHandler()
    # console.setLevel(logging.ERROR)
    console.setLevel(getattr(logging, log_level, logging.ERROR))
    logger.addHandler(console)