import json
import os
from datetime import datetime

DATA_FILE = "data/applied_candidates.json"

def store_candidate_json(candidate_data: dict):
    # Ensure data folder exists
    os.makedirs("data", exist_ok=True)

    # Load existing data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    # Add timestamp
    candidate_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append new candidate
    data.append(candidate_data)

    # Save back to file
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print("📁 Candidate stored in JSON database")
