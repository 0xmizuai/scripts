from mongoengine import *

import os
from dotenv import load_dotenv

load_dotenv()
MONGO_DB_URL = os.getenv('MONGO_DB_URL')

connect(MONGO_DB_URL)

