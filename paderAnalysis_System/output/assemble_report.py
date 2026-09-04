"""
assemble_report.py
-------------------
Final assembly step. Pure Python string templating -- NO LLM call here.

Takes:
  - the approved review queue (only sections marked "approved" are
    included; anything flagged/pending is called out explicitly rather
    than silently dropped)
  - the deterministic case_index() table (analyses.py) for the traceable
    listing section

...and writes one Markdown report.

WHY this step has no LLM involvement: by this point every sentence has
already been through generation + grounding check + human review. The
only job left is arranging already-approved text and already-computed
tables into a document -- string concatenation, not reasoning. Giving
this step to an LLM would add a step where a hallucination could sneak
back in for no benefit.
"""

import sys
import os
import json
from datetime import datetime

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_THIS_DIR)
sys.path.insert(0, os.path.join(_ROOT_DIR, "analysis"))
from load_data import load_and_clean
from analyses import run_all, case_index

REVIEW_STATE_FILE = os.path.join(_ROOT_DIR, "review", "review_state.json")
FINAL_REPORT_DIR = os.path.join(_THIS_DIR, "final_report")
os.makedirs(FINAL_REPORT_DIR, exist_ok=True)


def load_approved_sections():
    with open(REVIEW_STATE_FILE) as f:
        queue = json.load(f)
    approved = {item["section_key"]: item for item in queue if item["review_status"] == "approved"}
    not_approved = [item for item in queue if item["review_status"] != "approved"]
    return approved, not_approved


def render_case_index_table(cases_rows, max_rows=50):
    """
    Renders the case index as a Markdown table. Full listing is also
    written to a companion CSV (case_index_full.csv) since embedding all
    1,024 rows in the Markdown body would dwarf the report itself --
    the table below shows the first `max_rows` for readability, with a
    clear pointer to the full file for complete traceability.
    """
    lines = [
        "| Case ID | Reactions | Serious | Received Date | Country | Sex | Age Group |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in cases_rows[:max_rows]:
        reactions = row["reactions"]
        if len(reactions) > 60:
            reactions = reactions[:57] + "..."
        lines.append(
            f"| {row['case_id']} | {reactions} | {row['serious']} | "
            f"{row['received_date']} | {row['country']} | {row['sex']} | {row['age_group']} |"
        )
    return "\n".join(lines)


def build_report():
    cases, reactions, meta = load_and_clean()
    results = run_all(cases, reactions)
    full_index = case_index(cases, reactions)

    approved, not_approved = load_approved_sections()

    generated_on = datetime.now().strftime("%Y-%m-%d")

    section_order = [
        ("narrative_summary", "3. Narrative Summary and Analysis"),
        ("summary_analysis_of_cases", "4. Summary Analysis of Cases"),
        ("reaction_analysis", "5. Reaction / Adverse Event Analysis"),
        ("serious_cases_alert", "6. Serious Cases / 15-Day Alerts"),
        ("trends", "7. Trends and Important Observations"),
        ("history_of_actions", "8. History of Actions"),
    ]

    parts = []
    parts.append(f"""# Periodic Adverse Drug Experience Report (PADER)
## Bisoprolol (Application Number: B-1)

**Report Type:** PADER (simplified exercise version)
**Reporting Period:** 2024-12-27 to 2025-12-26
**Date of This Report:** {generated_on}
**Data Source:** Bisoprolol_icsr_sample_1068rows.xlsx (1,068 rows / 1,024 unique cases after deduplication)

---

## 1. Reporting Period

| Field | Value |
|---|---|
| Product | Bisoprolol |
| Application Number | B-1 |
| Report Type | PADER (simplified, exercise version) |
| Reporting Period | 2024-12-27 to 2025-12-26 |
| Data Cut-off | 2025-12-26 (latest `receivedate` in source data) |
| Report Generated | {generated_on} |

## 2. Data Processing Notes

- Source file contained {meta['raw_row_count']} rows representing {meta['unique_case_count']} unique cases (`safetyreportid`). {meta['older_version_rows_dropped']} rows were superseded follow-up versions of the same case and were excluded, keeping only the latest version per case.
- {meta['dedup_method']}
- {meta['missing_age_count']} cases have no recorded patient age; {meta['missing_sex_count']} cases have no recorded sex.
- No System Organ Class (SOC) field is present in the source data; reaction analysis is reported at the MedDRA Preferred Term level only.
- No product label/CCDS reference was supplied for this exercise; expectedness (labeled vs. unlabeled) is out of scope.
- No history-of-actions data was supplied for this exercise (see Section 8).

""")

    for key, heading in section_order:
        parts.append(f"## {heading}\n\n")
        if key in approved:
            parts.append(approved[key]["generated_text"] + "\n\n")
        else:
            parts.append("*[Section pending human review -- not included in this version of the report.]*\n\n")

    parts.append("## 9. Case Index / Listing\n\n")
    parts.append(
        f"The table below lists the first 50 of {len(full_index)} total cases for illustration. "
        f"The complete case-level listing, to which every aggregate figure above is traceable, "
        f"is provided in the companion file `case_index_full.csv`.\n\n"
    )
    parts.append(render_case_index_table(full_index, max_rows=50))
    parts.append("\n\n")

    if not_approved:
        parts.append("## Review Status Notice\n\n")
        parts.append(
            "The following sections did not pass automated grounding review and required "
            "human attention before inclusion:\n\n"
        )
        for item in not_approved:
            parts.append(f"- **{item['section_name']}**: {item['reviewer_note']}\n")
        parts.append("\n")

    parts.append("---\n\n*This report was generated by an AI-assisted pipeline for a technical "
                  "exercise. All figures are derived deterministically from the source dataset via "
                  "Python analysis; narrative text was generated per-section from scoped, "
                  "pre-computed evidence packets, subject to automated grounding checks and human "
                  "review before inclusion. See README.md for full methodology.*\n")

    report_text = "".join(parts)

    report_path = os.path.join(FINAL_REPORT_DIR, "PADER_Bisoprolol_Report.md")
    with open(report_path, "w") as f:
        f.write(report_text)

    # Full case index as CSV for complete traceability
    import csv
    csv_path = os.path.join(FINAL_REPORT_DIR, "case_index_full.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=full_index[0].keys())
        writer.writeheader()
        writer.writerows(full_index)

    print(f"Report written: {len(report_text)} characters -> {report_path}")
    print(f"Case index: {len(full_index)} rows -> {csv_path}")
    return report_text


if __name__ == "__main__":
    build_report()
