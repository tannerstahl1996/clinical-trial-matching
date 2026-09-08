import requests
import json

BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

def fetch_candidates(condition: str, max_results: int = 30):
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

def summarize(study: dict) -> dict:
    protocol = study["protocolSection"]
    identification = protocol["identificationModule"]
    design = protocol.get("designModule", {})
    interventions = protocol.get("armsInterventionsModule", {}).get("interventions", [])

    return {
        "nct_id": identification["nctId"],
        "title": identification["briefTitle"],
        "study_type": design.get("studyType"),
        "phase": design.get("phases"),
        "intervention_types": [i.get("type") for i in interventions],
        "intervention_names": [i.get("name") for i in interventions],
    }

if __name__ == "__main__":
    data = fetch_candidates("type 2 diabetes", max_results=30)
    print(f"Total in registry: {data.get('totalCount')}")
    print(f"Fetched: {len(data['studies'])}\n")

    with open("candidate_trials_raw.json", "w") as f:
        json.dump(data["studies"], f, indent=2)

    for study in data["studies"]:
        s = summarize(study)
        print(f"{s['nct_id']} | {s['study_type']} | {s['phase']} | {s['intervention_types']}")
        print(f"  {s['title']}")
        print(f"  Drugs: {s['intervention_names']}\n")
