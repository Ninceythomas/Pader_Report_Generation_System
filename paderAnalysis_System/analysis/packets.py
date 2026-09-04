"""
packets.py
----------
THE CORE DESIGN IDEA OF THIS PROJECT.

Each report section gets its OWN small evidence packet: a JSON object
containing only the pre-computed numbers that section needs, nothing else.

This is the opposite of "hand the model the CSV and ask it to write a
PADER." Every packet is:
  - Built entirely from analyses.py output (already-verified numbers)
  - Scoped: no field the section doesn't need is included
  - Declarative: section name + reporting period + a short "instructions"
    line reminding the model what NOT to do (invent, infer causality,
    add numbers not present)

WHY per-section packets instead of one giant context blob:
  1. Smaller prompt -> less chance the model "notices" an unrelated number
     and drags it into a sentence where it doesn't belong.
  2. Each section can be regenerated independently (re-run just the
     Reaction Analysis section without touching the others) -- this is
     also what makes Version 1 (config-driven report types) possible
     without a rewrite: a new report type just declares a different set
     of packets per section.
  3. Auditable: if a sentence in the final report is wrong, the packet
     that produced it is a small, readable JSON object you can check by
     eye in seconds.

Each build_*_packet() function below corresponds 1:1 to one report
section from PADER_Starter_Guide.md.
"""

REPORTING_PERIOD = {
    "product": "Bisoprolol",
    "application_number": "B-1",
    "report_type": "PADER (simplified, exercise version)",
    "period_start": "2024-12-27",
    "period_end": "2025-12-26",
}


def build_narrative_summary_packet(results, meta):
    """Section 2: Narrative Summary and Analysis (the main analytical section)."""
    return {
        "section": "Narrative Summary and Analysis",
        "reporting_period": REPORTING_PERIOD,
        "approved_analysis_results": {
            "total_cases": results["case_volume"]["total_cases"],
            "serious_cases": results["case_volume"]["serious_cases"],
            "serious_pct": results["case_volume"]["serious_pct"],
            "non_serious_cases": results["case_volume"]["non_serious_cases"],
            "non_serious_pct": results["case_volume"]["non_serious_pct"],
            "top_3_reactions_overall": results["reaction_analysis"]["top_reactions_overall"][:3],
            "top_3_reactions_serious": results["reaction_analysis"]["top_reactions_serious"][:3],
            "top_3_countries": dict(list(results["demographics"]["top_5_countries"].items())[:3]),
            "sex_breakdown": results["demographics"]["by_sex"],
            "alert_case_count": results["alert_15day"]["total_alert_cases"],
            "data_quality_note": (
                f"{meta['missing_age_count']} of {meta['unique_case_count']} cases have no "
                f"recorded age; {meta['missing_sex_count']} have no recorded sex."
            ),
        },
        "instructions": (
            "Summarize ONLY the figures above, in plain regulatory prose. "
            "Do not state or imply a safety conclusion (e.g. 'no concerns identified', "
            "'the product is safe') that is not explicitly present in the figures. "
            "Do not invent a causal relationship between the product and any reaction. "
            "Neutral, factual tone. 2-4 short paragraphs."
        ),
    }


def build_summary_analysis_of_cases_packet(results, meta):
    """Section 3: Summary Analysis of Cases (aggregate case-level breakdown)."""
    return {
        "section": "Summary Analysis of Cases",
        "reporting_period": REPORTING_PERIOD,
        "approved_analysis_results": {
            "case_volume": results["case_volume"],
            "by_age_group": results["demographics"]["by_age_group"],
            "by_sex": results["demographics"]["by_sex"],
            "by_country_top5": results["demographics"]["top_5_countries"],
            "outcome_counts": results["outcome_analysis"]["outcome_counts"],
        },
        "instructions": (
            "Present the case-volume and demographic breakdown as factual statements "
            "with exact figures. Do not average, estimate, or recompute any number -- "
            "use the values given exactly as provided. Note any data gaps "
            "(e.g. 'Unknown' age/sex counts) plainly rather than omitting them. "
            "Neutral tone, short paragraphs or a brief bulleted summary."
        ),
    }


def build_reaction_analysis_packet(results):
    """Section 4: Reaction / Adverse Event Analysis."""
    return {
        "section": "Reaction / Adverse Event Analysis",
        "reporting_period": REPORTING_PERIOD,
        "approved_analysis_results": {
            "top_reactions_overall": results["reaction_analysis"]["top_reactions_overall"],
            "top_reactions_serious": results["reaction_analysis"]["top_reactions_serious"],
            "unique_reaction_terms": results["reaction_analysis"]["unique_reaction_terms"],
            "total_reaction_mentions": results["reaction_analysis"]["total_reaction_mentions"],
            "top_reactions_by_sex": results["reaction_analysis"]["top_reactions_by_sex"],
            "top_reactions_by_age_group": results["reaction_analysis"]["top_reactions_by_age_group"],
            "soc_availability_note": results["reaction_analysis"]["note_no_soc"],
        },
        "instructions": (
            "Summarize the reaction frequency data given. Explicitly state that System "
            "Organ Class grouping is not available in the source data (do not invent SOC "
            "categories). Report reaction counts as observed frequencies only -- do not "
            "characterize any reaction as expected, unexpected, or drug-related, since "
            "expectedness/causality data was not supplied for this exercise. "
            "Neutral tone, 2-3 short paragraphs."
        ),
    }


def build_serious_cases_alert_packet(results):
    """Section 5: Serious Cases / 15-Day Alerts."""
    return {
        "section": "Serious Cases / 15-Day Alerts",
        "reporting_period": REPORTING_PERIOD,
        "approved_analysis_results": {
            "total_alert_cases": results["alert_15day"]["total_alert_cases"],
            "alert_pct_of_total": results["alert_15day"]["alert_pct_of_total"],
            "fatal_alert_cases": results["alert_15day"]["fatal_alert_cases"],
            "top_reactions_in_alert_cases": results["alert_15day"]["top_reactions_in_alert_cases"],
            "seriousness_criteria_breakdown": results["seriousness_criteria"],
            "sample_case_ids": results["alert_15day"]["sample_alert_case_ids"],
        },
        "instructions": (
            "Summarize the 15-day Alert case figures given. Note that seriousness "
            "criteria are independent (yes/no) flags and are not mutually exclusive -- "
            "a single case may meet more than one criterion, so the criteria counts "
            "will not sum to the total case count. Do not invent case narratives; "
            "only reference the case IDs and counts provided. Neutral, factual tone."
        ),
    }


def build_trends_packet(results):
    """Section 6: Trends and Important Observations."""
    return {
        "section": "Trends and Important Observations",
        "reporting_period": REPORTING_PERIOD,
        "approved_analysis_results": {
            "monthly_case_counts": results["monthly_trend"]["monthly_case_counts"],
            "monthly_serious_counts": results["monthly_trend"]["monthly_serious_counts"],
            "min_month_count": results["monthly_trend"]["min_month_count"],
            "max_month_count": results["monthly_trend"]["max_month_count"],
            "top_reaction_movers_first_vs_second_half": results["reaction_trend_movers"]["movers"],
            "split_date": results["reaction_trend_movers"].get("split_date"),
        },
        "instructions": (
            "Describe observable numerical patterns only (e.g. 'cases rose from X in "
            "month A to Y in month B'). Do NOT characterize any pattern as a confirmed "
            "safety signal, a trend requiring action, or a cause-effect relationship. "
            "End by noting these observations are provided for qualified human reviewer "
            "assessment, not as concluded findings. Neutral tone, short paragraphs."
        ),
    }


def build_history_of_actions_packet():
    """
    Section 7: History of Actions.
    No action data was supplied with this dataset (confirmed in
    PADER_Starter_Guide.md Appendix B). Per that guide: do not invent
    actions -- state plainly that none were provided. This packet is
    intentionally empty of any 'action' data; the instruction alone
    produces the correct, honest sentence.
    """
    return {
        "section": "History of Actions",
        "reporting_period": REPORTING_PERIOD,
        "approved_analysis_results": {
            "actions_data_supplied": False,
        },
        "instructions": (
            "State plainly and only that no history-of-actions data (e.g. labeling "
            "changes, regulatory communications, safety studies) was supplied for this "
            "reporting period. Do not invent, assume, or imply any specific action took "
            "place. One or two sentences."
        ),
    }


ALL_PACKET_BUILDERS = {
    "narrative_summary": build_narrative_summary_packet,
    "summary_analysis_of_cases": build_summary_analysis_of_cases_packet,
    "reaction_analysis": build_reaction_analysis_packet,
    "serious_cases_alert": build_serious_cases_alert_packet,
    "trends": build_trends_packet,
    "history_of_actions": build_history_of_actions_packet,
}
