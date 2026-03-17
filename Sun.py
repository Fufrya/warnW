import requests
url = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-latest.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def gather():
    ciferki = requests.get(url, headers = HEADERS, timeout=10)
    ciferki.raise_for_status()
    data = ciferki.json()
    if not data:
        return None
    current = data[-1]

    return{
        "time":current.get("time_tag"),
        "seichas":current.get("current_class"),
        "bilo":current.get("max_class"),
        "v":current.get("max_time"),
    }
if __name__ == "__main__":
    vivod = gather()
    if vivod:
        print("Current X-ray data:")
        print("Activity level ", vivod["seichas"])
        print("Last updated ", vivod["time"])
        if vivod['bilo'] and vivod["bilo"][0] == "M":
            print("The recent maximum was ", vivod["bilo"], "happened at ", vivod["v"],", it may affect you")
        if vivod['bilo'] and vivod["bilo"][0] == "X":
            print("Major flare! ", vivod["bilo"], "happened at ", vivod["v"], ", consider taking medicine if needed")
    else:
        print("No data found.")