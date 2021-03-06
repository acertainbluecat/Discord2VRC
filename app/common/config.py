import configparser

from os import path
from typing import List
from urllib.parse import quote_plus


CONFIG_DIR = "../config.ini"


def parse_owners(owners: str) -> List[int]:
    """Parse owner list from config file"""
    return [int(owner) for owner in owners.split("\n")]


def to_dict(cfg: configparser.ConfigParser) -> dict:
    """Converts ConfigParser object into dictionary"""
    return {s.lower(): dict(cfg[s]) for s in cfg.sections()}


def setup_config() -> dict:
    """Reads config file, and returns dictionary with
    parsed configuration
    """
    cfg = configparser.ConfigParser()
    cfg.read(CONFIG_DIR)
    config = to_dict(cfg)
    config["discord"]["owners"] = parse_owners(config["discord"]["owners"])
    config["database"]["password"] = quote_plus(config["database"]["password"])
    config["directories"]["uploadsdir"] = path.join(
        config["directories"]["staticdir"],
        config["directories"]["uploadsfolder"],
    )
    return config


config = setup_config()
