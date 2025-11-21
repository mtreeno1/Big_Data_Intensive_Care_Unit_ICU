import os
import json
import requests
import pandas as pd
from tqdm import tqdm
from io import StringIO  # dùng StringIO chuẩn

BASE_URL = "https://api.vitaldb.net"

os.makedirs("data/raw/cases", exist_ok=True)
os.makedirs("data/raw/tracks", exist_ok=True)
os.makedirs("data/raw/labs", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

def download_text(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

# ==========================
# 1. Crawl cases (bỏ vì API rỗng)
# ==========================
def crawl_cases():
    print("\n--- Crawling: cases ---")
    url = f"{BASE_URL}/cases"
    text = download_text(url)
    if not text or text.strip() == "":
        print(f"Warning: {url} returned empty response. Skipping cases.")
        return None
    try:
        text = text.lstrip('\ufeff')  # nếu có BOM
        data = json.loads(text)
        out_json = "data/raw/cases/cases.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved: {out_json}")

        df = pd.DataFrame(data)
        df.to_csv("data/processed/cases.csv", index=False)
        print("Processed: data/processed/cases.csv")
        return data
    except Exception as e:
        print(f"Error parsing /cases JSON: {e}")
        return None

# ==========================
# 2. Crawl track list (CSV)
# ==========================
def crawl_track_list():
    print("\n--- Crawling: track list ---")
    url = f"{BASE_URL}/trks"
    text = download_text(url)
    if text:
        out_csv = "data/raw/tracks/track_list.csv"
        with open(out_csv, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {out_csv}")

        df = pd.read_csv(StringIO(text))
        df.to_csv("data/processed/track_list.csv", index=False)
        print("Processed: data/processed/track_list.csv")

        return df.to_dict(orient="records")
    return None

# ==========================
# 3. Crawl labs (CSV)
# ==========================
def crawl_labs():
    print("\n--- Crawling: labs ---")
    url = f"{BASE_URL}/labs"
    text = download_text(url)
    if text:
        out_csv = "data/raw/labs/labs.csv"
        with open(out_csv, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved: {out_csv}")

        df = pd.read_csv(StringIO(text))
        df.to_csv("data/processed/labs.csv", index=False)
        print("Processed: data/processed/labs.csv")

        return df.to_dict(orient="records")
    return None

# ==========================
# MAIN
# ==========================
if __name__ == "__main__":
    print("=== VITALDB DATA CRAWLER ===")

    cases = crawl_cases()  # sẽ skip nếu API rỗng
    trks = crawl_track_list()
    crawl_labs()

    print("\nDONE: Data saved in data/raw/ and data/processed/")
