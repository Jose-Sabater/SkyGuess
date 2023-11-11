from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    def __init__(self):
        self.fr24_uname = os.getenv("fr_uname")
        self.fr24_pwd = os.getenv("fr_pwd")
