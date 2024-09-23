import json
import os
import requests
import sys

from funda_scraper import FundaScraper

# Use absolute paths so it works in CRONs
base = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(base, 'settings.json')
DATA_FILE = os.path.join(base, 'data.json')

def setup():
    if not os.path.exists(SETTINGS_FILE):
        sys.exit("No settings file")

    if not os.path.exists(DATA_FILE):
        json.dump({
            "last_id": 0
        }, open(DATA_FILE, 'w'))

def get_id(u):
    parts = u.split("/")
    return int(parts[-2].split("-")[1])

if __name__ == "__main__":
    setup()

    config = json.load(open(SETTINGS_FILE))
    data = json.load(open(DATA_FILE))

    area = config['funda']['area']
    if type(area) is list:
        area = '%22%2C%22'.join(area)

    scraper = FundaScraper(
        area=area,
        want_to=config['funda']['type'],
        find_past=False,
        n_pages=1,
        max_price=config['funda']['max_price'],
        sort="date_down",
        property_type=config['funda']['property_type'],
    )

    # df = scraper.run(raw_data=False, save=True, filepath="test.csv")
    # The Funda Scraper is currently failing to parse the data from Funda, but it can find the URLS
    # Workaround to extract IDs from the URLs, and just use these to find if there are any new listings
    # IDs are NOT chronological, so we cant just sort by that, we have to find the row of the previous ID
    df = scraper.run(raw_data=True)
    df['id'] = df.apply(lambda x: get_id(x["url"]), axis=1)
    new = []
    for index, row in df.iterrows():
        if row["id"] == data["last_id"]:
            break
        new.append((row["id"], row["url"]))

    if len(new) > 0:
        msg = ""
        if len(new) == 1:
            msg = f"Nieuw huis op Funda: {new[0][1]}"
        else:
            msg = f"{len(new)} nieuwe huizen op Funda, nieuwste: {new[0][1]}"

        # Send notification
        url = f"https://api.telegram.org/bot{config['telegram']['api_token']}/sendMessage"
        params = {"chat_id": config["telegram"]["chat_id"], "text": msg}
        r = requests.get(url, params=params)

        # Update state
        data["last_id"] = new[0][0]
        json.dump(data, open(DATA_FILE, 'w'))
