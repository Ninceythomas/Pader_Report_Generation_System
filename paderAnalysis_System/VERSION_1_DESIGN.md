# Version 1 Design Doc — Generalizing Beyond PADER

Given the time available, this is a design doc rather than an implementation.
The question it answers: *"How much of Version 0 would survive a request to
support PSUR, PBRER, DSUR, CSR unmodified, if the differences were expressed
as configuration and data rather than new code paths?"*

## Short answer

Most of it. The layers that would survive completely unmodified:
`load_data.py`'s cleaning logic (any ICSR-shaped dataset needs the same
dedup/explode treatment), the underlying `analyses.py` functions (case
counts, reaction frequency, and demographic breakdowns are report-type-
agnostic — a PSUR needs the same "top reactions" number a PADER does), the
system prompt (the hard rules about grounding don't change based on report
type), `generate.py`'s call+grounding-check loop, and the human review
mechanism.

What would need to change is exactly the two things Version 0 was already
designed to keep separate and swappable: **which packets get built** (i.e.
which analyses feed which sections) and **the per-section instructions**
inside those packets. That separation is the reason this survives.

## What's already report-type-agnostic in Version 0

| Component | Why it generalizes |
|---|---|
| `load_data.py` | Any E2B/FAERS-style ICSR dataset has the same case/version/reaction shape |
| `analyses.py` functions | "Count serious cases," "top reactions," "monthly trend" are defined the same way regardless of which report consumes them |
| `system_prompt.py` | The grounding rules ("don't invent numbers," "don't assert causation") apply to every report type equally |
| `generate.py` | The call+check loop takes a packet and produces checked text — it doesn't know or care what report type the packet came from |
| `review.py` | Approve/flag is a generic gate |

## What needs to become configuration

**1. A report-type registry**, replacing the current hardcoded
`section_order` list in `assemble_report.py`:

```python
REPORT_TYPES = {
    "PADER": {
        "sections": [
            {"key": "narrative_summary", "packet_builder": "build_narrative_summary_packet"},
            {"key": "summary_analysis_of_cases", "packet_builder": "build_summary_analysis_of_cases_packet"},
            {"key": "reaction_analysis", "packet_builder": "build_reaction_analysis_packet"},
            {"key": "serious_cases_alert", "packet_builder": "build_serious_cases_alert_packet"},
            {"key": "trends", "packet_builder": "build_trends_packet"},
            {"key": "history_of_actions", "packet_builder": "build_history_of_actions_packet"},
        ],
        "reporting_basis": "21 CFR 314.80",
    },
    "PSUR": {
        "sections": [
            {"key": "worldwide_market_status", "packet_builder": "build_market_status_packet"},
            {"key": "summary_analysis_of_cases", "packet_builder": "build_summary_analysis_of_cases_packet"},  # REUSED
            {"key": "reaction_analysis", "packet_builder": "build_reaction_analysis_packet"},                  # REUSED
            {"key": "signal_evaluation", "packet_builder": "build_signal_evaluation_packet"},                  # NEW
            {"key": "benefit_risk", "packet_builder": "build_benefit_risk_packet"},                            # NEW
        ],
        "reporting_basis": "ICH E2C(R2) / EU GVP Module VII",
    },
    # DSUR, CSR, PBRER follow the same shape
}
```

A new report type is a new dict entry: which sections, in what order,
built from which packet functions. `assemble_report.py` loops over
`REPORT_TYPES[report_type]["sections"]` instead of a hardcoded list —
zero code changes to add PSUR once its packet builders exist.

**2. Packet builders are the real reusable unit, not sections.**
Version 0 already separates "packet builder function" from "section" —
`build_summary_analysis_of_cases_packet` and `build_reaction_analysis_packet`
are pure functions of `(results, meta)` with no PADER-specific logic in
them. A PSUR's case-summary section can call the exact same function a
PADER's does. Only genuinely new analytical needs (signal evaluation,
benefit-risk framing) require new packet builders — and those are still
just functions that assemble a JSON dict from already-computed `analyses.py`
outputs plus, where a report type needs an analysis Version 0 doesn't have
yet (e.g. cumulative-vs-interval signal detection for PSUR), one new
function in `analyses.py`. The deterministic/LLM split doesn't change.

**3. Per-section instructions become data, not code.**
Right now each packet builder hardcodes its `instructions` string. Moving
this to a small YAML/JSON config keyed by `(report_type, section_key)`
means editing report behavior doesn't require touching Python:

```yaml
PADER.serious_cases_alert.instructions: >
  Summarize the 15-day Alert case figures given. Note that seriousness
  criteria are independent (yes/no) flags...
PSUR.signal_evaluation.instructions: >
  Present the signal evaluation criteria and outcome given. Do not
  characterize a numerical pattern as a confirmed signal unless the
  packet's own evaluation field states that conclusion...
```

**4. System prompt stays a single constant** across all report types,
because the hard rules it encodes (grounding, no fabricated causation, no
invented narratives) are not report-type-specific — they're properties of
"honest regulatory writing," full stop. This is deliberate: report-type
differences belong in packets/config, not in the model's operating rules.

## What Version 0 would NOT survive unmodified

- `assemble_report.py`'s hardcoded section list and Markdown header
  template — becomes a small Jinja-style template keyed by report type.
- The `REPORTING_PERIOD` constant in `packets.py` is currently
  hand-set for one product/period — needs to become a parameter passed
  in from a report-run config (product, application number, period
  start/end), likely a `ReportRun` dataclass everything downstream reads
  from instead of a module-level constant.
- Some report types (PSUR, DSUR) need analyses Version 0 doesn't compute
  yet — cumulative (not just interval) counts, comparison against a prior
  period, literature-source cases. These are new `analyses.py` functions,
  additive rather than a rewrite of existing ones.

## Other Version 1 directions considered (not pursued, for time)

- **Evidence tracing** (click a sentence, see its source data) — natural
  extension of the grounding check, which already computes exactly this
  mapping (packet numbers -> generated text) but currently only surfaces
  pass/fail rather than a per-sentence citation. Would mean returning
  spans instead of a boolean.
- **Versioning** (track dataset/analysis/prompt/model per report) — would
  mean stamping every packet and generated section with a content hash
  and the model string used, stored alongside `review_state.json`.
- **Automated evaluation beyond grounding** — comparing generated
  narrative structure/tone against a rubric, or regenerating a section
  twice and diffing for consistency, as a cheap self-consistency signal.

These weren't built because Version 0's core claim — that the report only
says what the data supports, and that this is checkable — was the higher-
priority thing to get right and prove within the time available, and the
generalization story above shows the architecture doesn't paint itself
into a corner even without implementing every extension.
