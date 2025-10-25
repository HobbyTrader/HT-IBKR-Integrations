import time
import logging

from ht_tools.utils import helpers

if __name__ == '__main__':
    config_json = helpers.load_config()
    print(config_json.get("loglevel"))
    
    