import requests
import json

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

def fetch_trials(condition: str, max_results: int = 8):
    params = {
        "query.cond": condition,
        "filter.overallStatus": "RECRUITING",
        "pageSize": max_results,
        "format": "json",
        "countTotal": "true",
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
    data = fetch_trials("type 2 diabetes", max_results=8)
    print(f"Total matching trials in registry: {data.get('totalCount')}")
    print(f"Trials fetched this run: {len(data['studies'])}")

    with open("raw_trials.json", "w") as f:
        json.dump(data["studies"], f, indent=2)
    print("Saved full raw records to raw_trials.json")

    extracted = []
    for study in data["studies"]:
        try:
            extracted.append(extract_trial_fields(study))
        except KeyError as e:
            nct_id = study.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "UNKNOWN")
            print(f"Skipped {nct_id}: missing field {e}")

    with open("trials.json", "w") as f:
        json.dump(extracted, f, indent=2)
    print(f"Saved {len(extracted)} simplified trial records to trials.json")
