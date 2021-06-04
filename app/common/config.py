import configparser

from os import path
from typing import List
from urllib.parse import quote_plus


CONFIG_DIR = "../config.ini"


def parse_owners(owners: str) -> List[int]:
    return [int(owner) for owner in owners.split("\n")]


def to_dict(cfg: configparser.ConfigParser) -> dict:
    return {k.lower(): dict(cfg[k]) for k in cfg.sections()}


def setup_config() -> dict:
    config = configparser.ConfigParser()
    config.read(CONFIG_DIR)
    config = to_dict(config)
    config["discord"]["owners"] = parse_owners(config["discord"]["owners"])
    config["database"]["password"] = quote_plus(config["database"]["password"])
    config["directories"]["uploadsdir"] = path.join(config["directories"]["staticdir"],
                                                    config["directories"]["uploadsfolder"])
    return config


config = setup_config()
