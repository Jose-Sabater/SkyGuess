from FlightRadar24 import FlightRadar24API
from config import Config

config = Config()


def init_fr_api():
    """Initializes the FlightRadar24 API"""
    fr_api = FlightRadar24API(user=config.fr24_uname, password=config.fr24_pwd)
    return fr_api
