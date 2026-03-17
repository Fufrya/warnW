import requests
import json
from datetime import datetime
import os
import sys
def get_config_path():
    if sys.platform == "win32":
        base = os.getenv("APPDATA")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/library/Application Support")
    else:
        base = os.path.expanduser("~/.config")
    app_dir = os.path.join(base, "warnW")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "config.json")

def gather2():
    cfg = get_config_path()
    if os.path.exists(cfg):
        with open(cfg, "r") as f:
            cfg = json.load(f)
        rn = datetime.now()
        hour = int(rn.strftime("%H"))
        la = cfg.get("user_data1", None)
        lo = cfg.get("user_data2", None)
        if la is not None and lo is not None:
            link = f"https://api.open-meteo.com/v1/forecast?latitude={la}&longitude={lo}&hourly=surface_pressure&current=surface_pressure&forecast_days=1"
            HEADERS = {"User-Agent": "Mozilla/5.0"}
            fetch = requests.get(link, headers = HEADERS, timeout=10)
            fetch.raise_for_status()
            data = fetch.json()
            if not data:
                return None
            else:
                return{
                    "cr":data.get("current")["surface_pressure"],
                    "1h":data.get("hourly")["surface_pressure"][hour+1] if hour <= 22 else "-1",
                    "2h": data.get("hourly")["surface_pressure"][hour + 2] if hour <= 21 else "-1",
                    "3h": data.get("hourly")["surface_pressure"][hour + 3] if hour <= 20 else "-1",
                }
        else:
            return("You did not set your location")
gather2()
