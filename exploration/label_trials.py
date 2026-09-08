import csv
import json
from patients import PATIENTS

with open("trials.json") as f:
    TRIALS = json.load(f)

OUTPUT_FILE = "labels.csv"

def already_labeled():
    try:
        with open(OUTPUT_FILE) as f:
            reader = csv.DictReader(f)
            return {(row["patient_id"], row["nct_id"]) for row in reader}
    except FileNotFoundError:
        return set()

def main():
    done = already_labeled()
    file_exists = len(done) > 0

    with open(OUTPUT_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["patient_id", "nct_id", "label", "notes"])

        for trial in TRIALS:
            print("\n" + "#" * 70)
            print(f"TRIAL {trial['nct_id']}: {trial['title']}")
            print(f"Age range: {trial['minimum_age']} - {trial['maximum_age']}")
            print(f"\n{trial['eligibility_criteria']}")
            print("#" * 70)

            for patient in PATIENTS:
                if (patient.patient_id, trial["nct_id"]) in done:
                    continue

                print("\n" + "-" * 70)
                print(f"PATIENT {patient.patient_id}")
                print(f"  Age: {patient.age}, Sex: {patient.sex}")
                print(f"  Condition: {patient.condition} ({patient.diabetes_type})")
                print(f"  Prior therapy failed: {patient.prior_therapy_failed}")
                print(f"  Pregnant/lactating: {patient.pregnant_or_lactating}")
                print(f"  Substance abuse history: {patient.substance_abuse_history}")
                print(f"  Trial in last 12mo: {patient.trial_participation_last_12mo}")
                print(f"  Notes: {patient.notes}")
                print("(scroll up to re-read this trial's criteria if needed)")

                label = input("\nMatch? (y/n/skip to quit): ").strip().lower()
                if label == "skip":
                    print(f"Stopping. Progress saved to {OUTPUT_FILE}.")
                    return
                notes = input("Why (short note): ").strip()
                writer.writerow([patient.patient_id, trial["nct_id"], label, notes])
                f.flush()

    print("\nAll pairs labeled.")

if __name__ == "__main__":
    main()
