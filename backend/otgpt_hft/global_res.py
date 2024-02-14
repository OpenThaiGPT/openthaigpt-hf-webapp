from pathlib import Path
from otgpt_hft.api.data_bridge import DataBridge
from otgpt_hft.database import Database

DATA_STORE_PATH = Path("data/store")

g_data_bridge = DataBridge()
g_database = Database()
