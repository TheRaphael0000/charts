import json
import requests
from datetime import datetime, timedelta
import dotenv
import os

dotenv.load_dotenv()

# --- CONFIGURATION ---
BESZEL_URL = "http://192.168.0.3:8090"  # Replace with your Hub URL & port
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
SYSTEM_NAME = "gold"            # The name of the server in your dashboard
OUTPUT_FILE = "temperatures_cpu.json"


def get_monthly_temperatures():
    session = requests.Session()

    print("Authenticating with Beszel Hub...")
    auth_url = f"{BESZEL_URL}/api/collections/users/auth-with-password"
    try:
        auth_response = session.post(
            auth_url, json={"identity": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        auth_response.raise_for_status()
        token = auth_response.json().get("token")
        session.headers.update({"Authorization": f"Bearer {token}"})
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    systems_url = f"{BESZEL_URL}/api/collections/systems/records"
    try:
        sys_response = session.get(
            systems_url, params={"filter": f"name='{SYSTEM_NAME}'"})
        sys_response.raise_for_status()
        records = sys_response.json().get("items", [])
        if not records:
            return
        system_id = records[0].get("id")
    except Exception as e:
        print(e)
        return

    stats_url = f"{BESZEL_URL}/api/collections/system_stats/records"

    params = {
        "filter": f"system='{system_id}' && type='480m'",
        "sort": "created",
        "perPage": 5000
    }

    try:
        stats_response = session.get(stats_url, params=params)
        stats_response.raise_for_status()
        stats_records = stats_response.json().get("items", [])

        historical_records = []
        for record in stats_records:
            stats_data = record.get("stats", record.get("info", {}))
            temperatures = stats_data.get("t", {})

            if temperatures:  # Skip entries if temperature tracking was offline/null
                historical_records.append({
                    "timestamp": record.get("created"),
                    "sensors": temperatures.get("cpu_thermal")
                })

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(historical_records, f, indent=4)

    except Exception as e:
        print(e)


if __name__ == "__main__":
    get_monthly_temperatures()
