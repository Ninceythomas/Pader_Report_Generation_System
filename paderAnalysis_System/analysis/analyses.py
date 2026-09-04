"""
analyses.py
-----------
The deterministic "accountant." Every function here computes an exact
number from the cleaned data using pandas -- no LLM calls anywhere in
this file.

DESIGN PRINCIPLE (see README for full reasoning):
  If a question has one correct numeric answer given the data, Python
  answers it. The LLM's job starts only after these numbers exist, and
  is limited to phrasing/summarizing them -- never recomputing them.

Each function returns a plain dict/list of JSON-safe values so it can be
dropped straight into an evidence packet and also straight into a
Jinja/markdown template for the Case Index without ever touching an LLM.
"""

import pandas as pd


def case_volume(cases_df):
    total = len(cases_df)
    serious = int(cases_df["is_serious"].sum())
    non_serious = total - serious
    return {
        "total_cases": total,
        "serious_cases": serious,
        "serious_pct": round(100 * serious / total, 1) if total else 0,
        "non_serious_cases": non_serious,
        "non_serious_pct": round(100 * non_serious / total, 1) if total else 0,
    }


def demographics(cases_df):
    age = cases_df["age_group"].value_counts().to_dict()
    sex = cases_df["sex_clean"].value_counts().to_dict()
    country = cases_df["country_clean"].value_counts().to_dict()
    return {
        "by_age_group": age,
        "by_sex": sex,
        "by_country": country,
        "top_5_countries": {k: int(v) for k, v in cases_df["country_clean"].value_counts().head(5).items()},
    }


def reaction_analysis(reactions_df, top_n=10):
    top_all = reactions_df["reaction_pt"].value_counts().head(top_n)
    serious_reactions = reactions_df[reactions_df["is_serious_case"]]
    top_serious = serious_reactions["reaction_pt"].value_counts().head(top_n)

    # reactions by sex / age group -- top 5 only, to keep packets small
    by_sex = (
        reactions_df.groupby(["sex_clean", "reaction_pt"]).size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .groupby("sex_clean").head(3)
    )
    by_age = (
        reactions_df.groupby(["age_group", "reaction_pt"]).size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .groupby("age_group").head(3)
    )

    return {
        "top_reactions_overall": [{"reaction": k, "count": int(v)} for k, v in top_all.items()],
        "top_reactions_serious": [{"reaction": k, "count": int(v)} for k, v in top_serious.items()],
        "unique_reaction_terms": int(reactions_df["reaction_pt"].nunique()),
        "total_reaction_mentions": len(reactions_df),
        "top_reactions_by_sex": by_sex.to_dict(orient="records"),
        "top_reactions_by_age_group": by_age.to_dict(orient="records"),
        "note_no_soc": "No System Organ Class field exists in the source data. "
                        "Analysis is reported at the MedDRA Preferred Term level only.",
    }


def outcome_analysis(reactions_df):
    counts = reactions_df["outcome"].value_counts().to_dict()
    total = len(reactions_df)
    pct = {k: round(100 * v / total, 1) for k, v in counts.items()} if total else {}
    return {
        "outcome_counts": counts,
        "outcome_pct": pct,
        "total_reaction_records": total,
    }


def seriousness_criteria_breakdown(cases_df):
    """
    Independent yes/no flags -- NOT mutually exclusive (a case can meet
    several). Counts each criterion separately across serious cases.
    """
    serious = cases_df[cases_df["is_serious"]]
    flags = {
        "Death": "seriousnessdeath",
        "Life-threatening": "seriousnesslifethreatening",
        "Hospitalization": "seriousnesshospitalization",
        "Disabling": "seriousnessdisabling",
        "Congenital anomaly": "seriousnesscongenitalanomali",
        "Other medically important": "seriousnessother",
    }
    out = {}
    for label, col in flags.items():
        out[label] = int((serious[col].astype(str).str.strip().str.lower() == "yes").sum())
    return out


def alert_15day_analysis(cases_df, reactions_df):
    """
    15-day Alert = fulfillexpeditecriteria == yes (per Appendix B: for this
    dataset, "serious" and "expedited/alert" are nearly the same population --
    we report both numbers rather than assuming they're identical).
    """
    alert_cases = cases_df[cases_df["is_alert"]]
    non_alert = cases_df[~cases_df["is_alert"]]

    alert_reactions = reactions_df[reactions_df["safetyreportid"].isin(alert_cases["safetyreportid"])]
    top_alert_reactions = alert_reactions["reaction_pt"].value_counts().head(5)

    death_in_alert = int(
        (alert_cases["seriousnessdeath"].astype(str).str.strip().str.lower() == "yes").sum()
    )

    return {
        "total_alert_cases": len(alert_cases),
        "total_non_alert_cases": len(non_alert),
        "alert_pct_of_total": round(100 * len(alert_cases) / len(cases_df), 1) if len(cases_df) else 0,
        "top_reactions_in_alert_cases": [{"reaction": k, "count": int(v)} for k, v in top_alert_reactions.items()],
        "fatal_alert_cases": death_in_alert,
        "sample_alert_case_ids": alert_cases["safetyreportid"].head(10).tolist(),
    }


def monthly_trend(cases_df):
    """
    Case volume by calendar month across the reporting period -- the exact,
    countable trend the guide asks for ("does volume increase/decrease").
    No interpretation of *why* -- that's for the human reviewer / LLM's
    bounded summarization, never a claim of causality from this function.
    """
    df = cases_df.dropna(subset=["received_dt"]).copy()
    df["month"] = df["received_dt"].dt.to_period("M").astype(str)
    monthly_counts = df.groupby("month").size().to_dict()
    monthly_serious = df[df["is_serious"]].groupby("month").size().to_dict()

    months_sorted = sorted(monthly_counts.keys())
    return {
        "monthly_case_counts": {m: monthly_counts[m] for m in months_sorted},
        "monthly_serious_counts": {m: monthly_serious.get(m, 0) for m in months_sorted},
        "first_month": months_sorted[0] if months_sorted else None,
        "last_month": months_sorted[-1] if months_sorted else None,
        "min_month_count": min(monthly_counts.values()) if monthly_counts else None,
        "max_month_count": max(monthly_counts.values()) if monthly_counts else None,
    }


def reaction_trend_top_movers(cases_df, reactions_df, n=3):
    """
    For the top overall reactions, count occurrences in the first half vs
    second half of the reporting period -- a concrete, checkable "did this
    go up or down" figure rather than an LLM-guessed trend.
    """
    df = reactions_df.dropna(subset=["received_dt"]).copy()
    if df.empty:
        return {"movers": []}

    mid = df["received_dt"].min() + (df["received_dt"].max() - df["received_dt"].min()) / 2
    df["half"] = df["received_dt"].apply(lambda d: "first_half" if d <= mid else "second_half")

    top_reactions = df["reaction_pt"].value_counts().head(n).index.tolist()
    movers = []
    for r in top_reactions:
        sub = df[df["reaction_pt"] == r]
        first = int((sub["half"] == "first_half").sum())
        second = int((sub["half"] == "second_half").sum())
        movers.append({"reaction": r, "first_half_count": first, "second_half_count": second})

    return {"movers": movers, "split_date": str(mid.date())}


def case_index(cases_df, reactions_df, limit=None):
    """
    Full traceable case listing -- the raw evidence any aggregate figure
    must be traceable back to (per PADER_Starter_Guide.md section 8).
    Returns list of dicts; not sent to the LLM (too large / not needed
    for prose) -- rendered directly into the report as a table/CSV.
    """
    react_by_case = (
        reactions_df.groupby("safetyreportid")["reaction_pt"]
        .apply(lambda s: "; ".join(s))
        .to_dict()
    )
    rows = []
    for _, r in cases_df.iterrows():
        rid = r["safetyreportid"]
        rows.append({
            "case_id": rid,
            "reactions": react_by_case.get(rid, ""),
            "serious": "Yes" if r["is_serious"] else "No",
            "received_date": r["received_dt"].strftime("%Y-%m-%d") if pd.notna(r["received_dt"]) else "Unknown",
            "country": r["country_clean"],
            "sex": r["sex_clean"],
            "age_group": r["age_group"],
        })
    if limit:
        rows = rows[:limit]
    return rows


def run_all(cases_df, reactions_df):
    """Convenience: run every deterministic analysis and return one dict."""
    return {
        "case_volume": case_volume(cases_df),
        "demographics": demographics(cases_df),
        "reaction_analysis": reaction_analysis(reactions_df),
        "outcome_analysis": outcome_analysis(reactions_df),
        "seriousness_criteria": seriousness_criteria_breakdown(cases_df),
        "alert_15day": alert_15day_analysis(cases_df, reactions_df),
        "monthly_trend": monthly_trend(cases_df),
        "reaction_trend_movers": reaction_trend_top_movers(cases_df, reactions_df),
    }


if __name__ == "__main__":
    from load_data import load_and_clean
    import json

    cases, reactions, meta = load_and_clean()
    results = run_all(cases, reactions)
    print(json.dumps(results, indent=2, default=str))
