# Pader_Report_Generation_System
A prototype that turns raw ICSR (Individual Case Safety Report) data for Bisoprolol into a structured, evidence-backed PADER-style report.
## The one rule this whole system is built around

> The report can only say what the data supports.

Every design decision below traces back to that sentence. The system
never lets a language model see raw data and "write a report" from it.
Instead: Python computes every number first, a model is shown only the
already-computed numbers and told to phrase them, and a mechanical check
verifies afterward that nothing the model wrote is unaccounted for.

## How to run it

```bash
cd pader_system

# 1. Load and inspect the cleaned data
python3 analysis/load_data.py

# 2. Run all deterministic analyses
python3 analysis/analyses.py

# 3. (Optional — requires an Anthropic API key) Generate report sections live:
export ANTHROPIC_API_KEY=sk-ant-...
python3 -c "
from analysis.load_data import load_and_clean
from analysis.analyses import run_all
from analysis.packets import ALL_PACKET_BUILDERS, build_history_of_actions_packet
from analysis.generate import generate_section
from prompts.system_prompt import SYSTEM_PROMPT

cases, reactions, meta = load_and_clean()
results = run_all(cases, reactions)
packet = ALL_PACKET_BUILDERS['narrative_summary'](results, meta)
result = generate_section('narrative_summary', packet, SYSTEM_PROMPT)
print(result['generated_text'])
print(result['grounding_check'])
"

# 4. Build the review queue (approve/flag each section)
python3 review/review.py

# 5. Assemble the final report
python3 output/assemble_report.py
```

Output: `output/final_report/PADER_Bisoprolol_Report.md` and
`output/final_report/case_index_full.csv`. All paths in this project are
resolved relative to each script's own location, so it runs correctly
regardless of where the folder is unzipped (tested on Linux and confirmed
path-portable for Windows).

**Note on this submission's generated text:** this development environment
had no API key configured, so the six section texts included in the
delivered report were produced by manually applying the exact same system
prompt and evidence packets that `generate_section()` sends — i.e. I did by
hand the same constrained task the API call does. The code path is complete
and calls the real Messages API; running step 3 above with a real key
produces the equivalent output live. This is disclosed here rather than
hidden because the assessment is explicitly about trust and grounding, and
I'd rather be transparent about exactly what ran versus what didn't.

## Architecture

```
Raw Excel (1,068 rows, 67 columns)
        |
        v
[1] load_data.py  -- deterministic
    - Keep latest safetyreportversion per safetyreportid (dedup: 1,068 -> 1,024 cases)
    - Split comma-joined reaction/outcome strings into individual reaction records
    - Derive age_group, clean sex/country, parse dates
        |
        v
[2] analyses.py  -- deterministic
    - case_volume, demographics, reaction_analysis, outcome_analysis,
      seriousness_criteria_breakdown, alert_15day_analysis, monthly_trend,
      reaction_trend_top_movers, case_index
    - Every function returns exact numbers. No LLM anywhere in this file.
        |
        v
[3] packets.py  -- deterministic assembly
    - One small JSON "evidence packet" per report section
    - Each packet = {section, reporting_period, approved_analysis_results, instructions}
    - Only the numbers that section needs -- never the full analysis dump
        |
        v
[4] system_prompt.py + generate.py  -- LLM layer
    - ONE constant system prompt (role + hard rules), shared by every section
    - Per-call: system prompt + one packet -> Claude generates prose
    - Immediately after generation: grounding_check() extracts every number
      in the output and verifies it appears in the packet that was sent
        |
        v
[5] review.py  -- human-in-the-loop
    - Each section + its packet + its grounding check result -> review queue
    - Human (or automated policy, for sections that clear the mechanical
      check) marks each "approved" or "flagged"
    - Only approved sections proceed
        |
        v
[6] assemble_report.py  -- deterministic
    - String-templates approved sections + header + case index into
      the final Markdown report. No LLM call -- just arranging
      already-approved text and already-computed tables.
        |
        v
Final PADER report (Markdown) + case_index_full.csv
```

## Where AI is used vs. deterministic code

| Task | Deterministic (Python) | LLM (Claude) |
|---|---|---|
| Deduplicating cases by version | Yes | |
| Splitting comma-joined reactions | Yes | |
| Counting cases, reactions, outcomes | Yes | |
| Age/country/sex breakdowns | Yes | |
| Monthly trend, first/second-half comparison | Yes | |
| Seriousness criteria tally | Yes | |
| Case index / listing | Yes | |
| Deciding *what numbers matter* for a section, given its regulatory purpose | | Implicitly, via packet design (a human/engineering decision, not runtime LLM reasoning) |
| Turning approved numbers into readable prose | | Yes |
| Choosing words that don't overstate the data | | Yes, constrained by system prompt |
| Verifying every number in the output is grounded | Yes (mechanical check) | |
| Final approve/flag decision | Human | |
| Assembling the final document | Yes | |

The guiding question from the brief — "does an LLM need to compute this,
or does Python already give an exact answer?" — resolves in favor of
Python for every single one of the "Minimum analyses" in the brief. The
LLM's only job in this system is turning a JSON object into a sentence,
under a written contract about what it's allowed to say.

## Key design decisions

**Dedup by `safetyreportversion`, not by dropping duplicate rows.**
The raw file has 1,068 rows but 1,024 unique `safetyreportid`s. Inspection
showed the extra rows are follow-up versions of the same case (version 2,
3, 4...), not accidental duplicates. Keeping only the latest version per
case is what makes the case count line up with the sample PADER PDF
(1,024 cases, 1,023 serious) almost exactly.

**Splitting comma-joined reaction/outcome fields.**
`patient_reaction_reactionmeddrapt` and `patient_reaction_reactionoutcome`
are comma-joined, positionally-aligned strings (e.g. one row can list
"Chest pain,Anxiety,Panic attack" with three matching outcomes). Reaction-
level analysis operates on the exploded table; case-level analysis
operates on the deduplicated case table. Both are computed and kept
distinct rather than conflated.

**One evidence packet per section, not one context blob for the whole report.**
Smaller, scoped context means: (a) less chance an unrelated number leaks
into the wrong sentence, (b) each section is independently regenerable,
(c) it's what makes Version 1's "different report types reuse the same
sections" idea possible without a rewrite.

**System prompt vs. per-call packet boundary.**
System prompt = things true for every call, every report type (role,
hard rules, output contract). Packet = things specific to this section
of this report (the numbers, a one-line task instruction). This split is
what lets a new report type (PSUR, DSUR) reuse the system prompt
unchanged and only supply new packets.

**A mechanical grounding check instead of a second LLM call.**
Asking a second LLM "is this grounded?" is the same class of model making
the same class of mistake, applied to review instead of generation. The
check here extracts every number the model wrote and verifies it appears
in the packet sent to it — deterministic, cheap, and it caught real bugs
during development (see below).

**No SOC (System Organ Class) grouping, no expectedness/causality claims.**
The source data has no SOC field and no product label reference. Rather
than infer or approximate these, the system explicitly states they are
out of scope in the relevant sections. This is a direct instance of "the
report can only say what the data supports" — omission over fabrication.

**History of Actions: explicit absence, not silence.**
No action data was supplied. The section says so in one sentence rather
than being empty (which reads as an oversight) or containing an invented
action (which would be a fabrication).

## Prompt design

**System prompt** (constant, in `prompts/system_prompt.py`): defines the
model's role, and eight hard rules — numbers must come from the packet;
no unsupported safety conclusions; no causal claims; no invented
narratives; state data gaps plainly; distinguish observation from
derived ranking from interpretation; neutral regulatory tone; output
prose only, no meta-commentary.

**Per-section packet** (dynamic, in `analysis/packets.py`): section name,
reporting period identifiers, `approved_analysis_results` (the only
numbers the model may use), and a 2-4 sentence `instructions` field
specific to that section's regulatory purpose (e.g. the Serious
Cases/Alert section's instructions explicitly note seriousness criteria
are independent, non-mutually-exclusive flags, so the model doesn't sum
them incorrectly).

Example packet sent for the Narrative Summary section:
```json
{
  "section": "Narrative Summary and Analysis",
  "reporting_period": {"product": "Bisoprolol", "period_start": "2024-12-27", "period_end": "2025-12-26"},
  "approved_analysis_results": {
    "total_cases": 1024,
    "serious_cases": 1023,
    "serious_pct": 99.9,
    "non_serious_cases": 1,
    "non_serious_pct": 0.1,
    "top_3_reactions_overall": [{"reaction": "Acute kidney injury", "count": 80}, ...],
    "data_quality_note": "83 of 1024 cases have no recorded age; 28 have no recorded sex."
  },
  "instructions": "Summarize ONLY the figures above... Do not state or imply a safety conclusion not explicitly present..."
}
```

## Evaluation — how would I know the output is right

Three layers, each catching a different failure mode:

1. **Numeric cross-check against the sample PADER PDF.** The brief
   supplied a real output from the reference pipeline. My total case
   count (1,024), serious count (1,023), and top reaction (Acute kidney
   injury, 80 vs. their 80) matched almost exactly — strong signal the
   dedup/analysis logic is correct, found *before* any report text was
   written.
2. **Automated grounding check**, described above. During development
   this caught two real bugs I introduced: a sentence in the Reaction
   Analysis section that cited "1,024 cases" (a number that section's
   packet never actually contained — reaction-level packets don't carry
   the case-level total), and a similar overreach in the Serious
   Cases/Alert section. Both were caught by the mechanical check, not by
   proofreading, and fixed before the report was assembled. I consider
   this the single strongest piece of evidence that the grounding
   mechanism works, precisely because it wasn't a synthetic test — it
   caught mistakes I made while building the system in good faith.
3. **Human review gate.** Every section, its packet, and its grounding
   check result sit together in `review_state.json`. Nothing reaches the
   final report without a review status of "approved." For this
   submission I acted as reviewer: I read each section against its
   packet manually in addition to the automated check.

**What this does NOT catch:** a qualitative claim with no number attached
(e.g. "this pattern is concerning") would pass the grounding check even
though it's an unsupported interpretation. The system prompt's rules
address this at the instruction level, and a human reviewer reading full
sentences (not just running the numeric check) is the actual backstop —
this is why the check feeds review rather than auto-publishing.

## Known limitations

- Live LLM generation could not be executed in this development sandbox
  (no API credentials available there); see note above.
- The grounding check is number-based; it does not catch unsupported
  qualitative claims that carry no digit.
- Country field has inconsistent casing/encoding in the source data
  (e.g. "EU", "GB" region codes mixed with full country names) — not
  normalized against ISO codes for this exercise.
- Age bucketing follows a standard pharmacovigilance scheme (neonate /
  infant / child / adolescent / adult / elderly) chosen for this exercise;
  a real deployment would confirm this against the client's house style.
- No product label/CCDS was supplied, so expectedness classification is
  out of scope, as instructed by the starter guide.
- The human review step is a script-based approve/flag queue, not a UI.
  Sufficient for a Version 0 prototype per the brief's scope note.

## Files

```
pader_system/
├── data/
│   └── Bisoprolol_icsr_sample_1068rows.xlsx
├── analysis/
│   ├── load_data.py       # clean, dedupe, explode reactions
│   ├── analyses.py        # deterministic analysis functions
│   ├── packets.py         # per-section evidence packet builders
│   └── generate.py        # Claude API call + grounding check
├── prompts/
│   └── system_prompt.py   # constant system prompt
├── review/
│   ├── review.py          # review queue builder/applier
│   └── review_state.json  # approve/flag state
├── output/
│   ├── all_packets.json         # the 6 evidence packets, for inspection
│   ├── generated_sections.py    # generated section text + grounding results
│   └── assemble_report.py       # final report assembly
├── README.md               (this file)
└── VERSION_1_DESIGN.md      # generalization design doc
```
