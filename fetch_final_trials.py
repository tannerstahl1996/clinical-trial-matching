import requests
import json

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

FINAL_TRIAL_IDS = [
    "NCT05028140",
    "NCT07465224",
    "NCT06863532",
    "NCT06428968",
    "NCT06256419",
    "NCT05427084",
    "NCT07272343",
]

def fetch_by_ids(nct_ids: list):
    params = {
        "filter.ids": ",".join(nct_ids),
        "pageSize": len(nct_ids),
        "format": "json",
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def extract_trial_fields(study: dict) -> dict:
    protocol = study["protocolSection"]
    identification = protocol["identificationModule"]
    eligibility = protocol["eligibilityModule"]

    return {
        "nct_id": identification["nctId"],
        "title": identification["briefTitle"],
        "sex": eligibility.get("sex"),
        "minimum_age": eligibility.get("minimumAge"),
        "maximum_age": eligibility.get("maximumAge"),
        "healthy_volunteers": eligibility.get("healthyVolunteers"),
        "eligibility_criteria": eligibility.get("eligibilityCriteria"),
    }

if __name__ == "__main__":
    data = fetch_by_ids(FINAL_TRIAL_IDS)
    fetched_ids = {s["protocolSection"]["identificationModule"]["nctId"] for s in data["studies"]}
    missing = set(FINAL_TRIAL_IDS) - fetched_ids
    if missing:
        print(f"WARNING: did not get back {missing} — check these IDs")

    with open("raw_trials.json", "w") as f:
        json.dump(data["studies"], f, indent=2)

    extracted = [extract_trial_fields(s) for s in data["studies"]]
    with open("trials.json", "w") as f:
        json.dump(extracted, f, indent=2)

    print(f"Saved {len(extracted)} trials to trials.json")
