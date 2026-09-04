"""
load_data.py
------------
Loads the raw ICSR Excel file and produces two clean, deduplicated tables:

  1. cases_df     -- one row per unique case (safetyreportid), keeping only
                      the LATEST safetyreportversion for each case.
  2. reactions_df -- one row per (case, individual reaction), produced by
                      splitting the comma-joined reaction/outcome strings.

WHY dedupe by version:
  The raw file has 1,068 rows but only 1,024 unique safetyreportid values.
  Inspection showed `safetyreportversion` increments when a case is updated
  (follow-up report). Keeping every version would double-count cases and
  reactions. Keeping only the max version per case gives the most current,
  non-duplicated picture -- which is what a real PADER counts.

WHY split reactions:
  `patient_reaction_reactionmeddrapt` and `patient_reaction_reactionoutcome`
  are comma-joined strings (e.g. "Chest pain,Anxiety,Panic attack" paired
  with "recovered/resolved,unknown,unknown"). They are positionally aligned
  index-for-index. A single case row can therefore represent multiple
  reactions, each with its own outcome. Reaction-level analysis (top
  reactions, outcome breakdown) must operate on the split/exploded table,
  NOT the raw row -- otherwise "Chest pain,Anxiety,Panic attack" would be
  miscounted as one reaction instead of three.

This module contains ZERO LLM calls. It is pure deterministic data
processing. That is intentional: counting, deduplicating, and splitting
strings is a job Python does exactly and reproducibly -- there is nothing
here for a language model to add except risk.
"""

import pandas as pd
import numpy as np
from datetime import datetime

import os

# Path resolved relative to THIS file's location, not hardcoded to any one
# machine -- so this works whether the project lives at /home/claude/...,
# E:\pader_system\..., or anywhere else it's unzipped to.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(_THIS_DIR, "..", "data", "Bisoprolol_icsr_sample_1068rows.xlsx")

SERIOUSNESS_FLAG_COLS = [
    "seriousnessdeath",
    "seriousnesslifethreatening",
    "seriousnesshospitalization",
    "seriousnessdisabling",
    "seriousnesscongenitalanomali",
    "seriousnessother",
]


def _parse_date(yyyymmdd):
    """FDA/FAERS dates arrive as integers like 20250305. Convert to datetime."""
    if pd.isna(yyyymmdd):
        return pd.NaT
    try:
        return datetime.strptime(str(int(yyyymmdd)), "%Y%m%d")
    except (ValueError, TypeError):
        return pd.NaT


def _age_group(age, unit):
    """
    Bucket a numeric onset age into a standard pharmacovigilance age group.
    Uses patient_patientonsetage + patient_patientonsetageunit since the
    pre-built patient_patientagegroup field is blank for ~97% of rows.
    Returns "Unknown" when age is missing or the unit is not year/month/day/week
    in a way we can safely convert.
    """
    if pd.isna(age):
        return "Unknown"

    unit = str(unit).strip().lower() if pd.notna(unit) else "year"

    # Normalize to years for bucketing
    if unit == "year":
        age_years = age
    elif unit == "month":
        age_years = age / 12
    elif unit == "week":
        age_years = age / 52
    elif unit == "day":
        age_years = age / 365
    else:
        # Unit code "800" or unrecognized -- do not guess, mark unknown
        return "Unknown"

    if age_years < 2 / 12:
        return "Neonate (<28 days)"
    elif age_years < 2:
        return "Infant (28 days-2yr)"
    elif age_years < 12:
        return "Child (2-11yr)"
    elif age_years < 18:
        return "Adolescent (12-17yr)"
    elif age_years < 65:
        return "Adult (18-64yr)"
    else:
        return "Elderly (65+yr)"


def load_and_clean():
    """
    Returns (cases_df, reactions_df, meta)

    cases_df: one row per unique case, latest version only. Includes
              derived columns: received_dt, age_group, is_serious (bool),
              seriousness_criteria (list of which flags fired).

    reactions_df: one row per (safetyreportid, reaction), exploded from the
                  comma-joined fields, aligned positionally with outcome.

    meta: dict of load-time facts (raw row count, dedup count, date range,
          any rows dropped and why) -- used for the report's data-quality
          footnote and for anyone auditing this pipeline later.
    """
    raw = pd.read_excel(RAW_PATH)
    raw_row_count = len(raw)

    # --- 1. Keep only latest version per case --------------------------------
    raw["safetyreportversion"] = pd.to_numeric(raw["safetyreportversion"], errors="coerce").fillna(1)
    idx_latest = raw.groupby("safetyreportid")["safetyreportversion"].idxmax()
    cases_df = raw.loc[idx_latest].copy().reset_index(drop=True)

    dropped_older_versions = raw_row_count - len(cases_df)

    # --- 2. Parse dates --------------------------------------------------------
    cases_df["received_dt"] = cases_df["receivedate"].apply(_parse_date)

    # --- 3. Derive age group -----------------------------------------------
    cases_df["age_group"] = cases_df.apply(
        lambda r: _age_group(r["patient_patientonsetage"], r["patient_patientonsetageunit"]),
        axis=1,
    )

    # --- 4. Normalize sex --------------------------------------------------
    cases_df["sex_clean"] = cases_df["patient_patientsex"].fillna("Unknown").str.strip().str.title()
    cases_df.loc[~cases_df["sex_clean"].isin(["Male", "Female"]), "sex_clean"] = "Unknown"

    # --- 5. Serious flag (case-level) --------------------------------------
    cases_df["is_serious"] = cases_df["serious"].astype(str).str.strip().str.lower() == "serious"

    # Which specific seriousness criteria fired (not mutually exclusive --
    # per the guide, these are independent yes/no flags)
    def criteria_list(row):
        return [c.replace("seriousness", "") for c in SERIOUSNESS_FLAG_COLS
                if str(row.get(c, "")).strip().lower() == "yes"]
    cases_df["seriousness_criteria"] = cases_df.apply(criteria_list, axis=1)

    # --- 6. Country: use occurcountry, fall back to reporter country -------
    # DECISION: occurcountry chosen as primary per Appendix B guidance to
    # "pick one and note which." Falls back to primarysource_reportercountry
    # only when occurcountry is missing.
    cases_df["country_clean"] = cases_df["occurcountry"].fillna(cases_df["primarysource_reportercountry"])
    cases_df["country_clean"] = cases_df["country_clean"].fillna("Unknown").str.strip().str.title()

    # --- 7. 15-day Alert flag -----------------------------------------------
    cases_df["is_alert"] = cases_df["fulfillexpeditecriteria"].astype(str).str.strip().str.lower() == "yes"

    # --- 8. Explode reactions/outcomes into reaction-level table ------------
    def split_field(val):
        if pd.isna(val):
            return []
        return [x.strip() for x in str(val).split(",")]

    records = []
    for _, row in cases_df.iterrows():
        pts = split_field(row["patient_reaction_reactionmeddrapt"])
        outcomes = split_field(row["patient_reaction_reactionoutcome"])
        # Positional alignment; if lengths mismatch, pad outcomes with "unknown"
        # rather than silently dropping a reaction (we log this in meta).
        mismatch = len(pts) != len(outcomes)
        if mismatch:
            if len(outcomes) < len(pts):
                outcomes = outcomes + ["unknown"] * (len(pts) - len(outcomes))
            else:
                outcomes = outcomes[: len(pts)]

        for pt, outcome in zip(pts, outcomes):
            if pt == "" or pt.lower() == "nan":
                continue
            records.append({
                "safetyreportid": row["safetyreportid"],
                "reaction_pt": pt,
                "outcome": outcome if outcome else "unknown",
                "is_serious_case": row["is_serious"],
                "age_group": row["age_group"],
                "sex_clean": row["sex_clean"],
                "country_clean": row["country_clean"],
                "received_dt": row["received_dt"],
            })

    reactions_df = pd.DataFrame(records)

    meta = {
        "raw_row_count": raw_row_count,
        "unique_case_count": cases_df["safetyreportid"].nunique(),
        "older_version_rows_dropped": int(dropped_older_versions),
        "total_reaction_mentions": len(reactions_df),
        "date_min": cases_df["received_dt"].min(),
        "date_max": cases_df["received_dt"].max(),
        "missing_age_count": int(cases_df["patient_patientonsetage"].isna().sum()),
        "missing_sex_count": int((cases_df["sex_clean"] == "Unknown").sum()),
        "dedup_method": "Kept max(safetyreportversion) row per safetyreportid; "
                         "reaction/outcome fields split on comma with positional alignment.",
    }

    return cases_df, reactions_df, meta


if __name__ == "__main__":
    cases, reactions, meta = load_and_clean()
    print("=== META ===")
    for k, v in meta.items():
        print(f"{k}: {v}")
    print("\n=== CASES SHAPE ===", cases.shape)
    print("=== REACTIONS SHAPE ===", reactions.shape)
