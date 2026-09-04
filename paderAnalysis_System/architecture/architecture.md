# Architecture Diagram

```mermaid
flowchart TD
    A[Raw ICSR Excel<br/>1,068 rows] --> B

    subgraph B[" Python — deterministic layer "]
        B1[Load and clean<br/>Dedupe by version, split reactions]
        B2[Analyses<br/>Counts, trends, breakdowns]
        B1 --> B2
    end

    B --> C[Evidence packets<br/>One scoped JSON per section]

    subgraph D[" LLM layer "]
        D1[System prompt<br/>Constant hard rules]
        D2[Generate section<br/>Prose from packet only]
        D1 --> D2
    end

    C --> D
    D --> E[Grounding check<br/>Every number traced to packet]
    E --> F[Human review<br/>Approve or flag each section]
    F -->|approved| G[Report assembly<br/>Approved sections + case index]
    F -->|flagged| H[Excluded from report]
    G --> I[Final PADER report]

    style B fill:#e1f5ee,stroke:#0f6e56
    style D fill:#faece7,stroke:#993c1d
    style H fill:#fcebeb,stroke:#a32d2d
```

**Legend:** Teal = deterministic Python (no AI). Coral = LLM-involved steps.
Red = sections that fail the grounding check and are excluded rather than
silently included.

## Flow, in words

1. **Raw ICSR data** (Excel) is loaded and cleaned — cases deduplicated by
   keeping the latest report version per case, comma-joined reaction
   fields split into individual records.
2. **Deterministic analyses** compute every required statistic in plain
   Python/pandas — no LLM involvement at this stage.
3. **Evidence packets** are assembled: one small, scoped JSON per report
   section, containing only the numbers that section needs.
4. **The LLM layer** takes one constant system prompt (defining hard rules
   about grounding and tone) plus one packet per call, and generates prose
   for that section only.
5. **A deterministic grounding check** extracts every number in the
   generated text and verifies it appears in the packet that was sent —
   catching any number the model introduced that wasn't actually provided.
6. **Human review**: every section, alongside its packet and grounding
   check result, is marked approved or flagged. Only approved sections
   proceed.
7. **Report assembly** is pure string templating — no LLM call — arranging
   already-approved text and already-computed tables (including the full
   case index) into the final document.
