# Single source of truth for which trials are in scope for this project.
# Every script that touches trials should filter against this list,
# rather than trusting that trials.json only contains the right ones.

KEPT_TRIAL_IDS = [
    "NCT05028140",
    "NCT07465224",
    "NCT06863532",
    "NCT06428968",
    "NCT06256419",
]
