import json
from typing import List
from .models import Zone
from .config import ZONES_CONFIG_PATH

def load_zones() -> List[Zone]:
    with open(ZONES_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    zones = [Zone(**z) for z in data["zones"]]
    return zones