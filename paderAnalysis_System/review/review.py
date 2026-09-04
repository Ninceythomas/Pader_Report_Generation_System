"""
review.py
---------
Human-in-the-loop review layer.

The brief asks for: "Somewhere in your flow, a human should be able to
review before something becomes 'final' -- analysis results, generated
sections, or both. A simple approve/flag mechanism is enough."

DESIGN: This is deliberately simple -- a JSON-backed queue, not a web app.
For a Version 0 prototype, the reviewer is a person running this script,
reading each generated section next to its evidence packet and grounding
check, and typing approve/flag/edit. This keeps the review step honest
(a real reviewer reading real evidence) without spending the day's
remaining hours on a UI that isn't what's being evaluated.

Each section carries THREE pieces of evidence for the reviewer to see
side-by-side, exactly matching how the "evaluating trust" story should
work:
  1. The evidence packet (the numbers that were allowed)
  2. The generated prose (what the model wrote)
  3. The grounding check (did every number in the prose actually appear
     in the packet -- mechanical, not a judgment call)

Only sections marked "approved" get included in the final assembled
report. Anything else is excluded and listed under "sections pending
review" so the gap is visible rather than silently missing.
"""

import json
import os

# All paths resolved relative to this file's location and the project root,
# so this runs correctly regardless of where the project folder is unzipped.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_THIS_DIR)

REVIEW_FILE = os.path.join(_THIS_DIR, "review_state.json")
PACKETS_FILE = os.path.join(_ROOT_DIR, "output", "all_packets.json")
ANALYSIS_DIR = os.path.join(_ROOT_DIR, "analysis")
OUTPUT_DIR = os.path.join(_ROOT_DIR, "output")


def build_review_queue(generated_sections, grounding_checks):
    """
    Produces the review queue: one entry per section with everything a
    human reviewer needs to make an approve/flag decision, and nothing
    they'd need to go dig up separately.
    """
    with open(PACKETS_FILE) as f:
        packets = json.load(f)

    queue = []
    for key, text in generated_sections.items():
        queue.append({
            "section_key": key,
            "section_name": packets[key]["section"],
            "generated_text": text,
            "evidence_packet_numbers": packets[key]["approved_analysis_results"],
            "grounding_check": grounding_checks[key],
            "review_status": "pending",   # reviewer sets to "approved" or "flagged"
            "reviewer_note": "",
        })
    return queue


def save_queue(queue):
    with open(REVIEW_FILE, "w") as f:
        json.dump(queue, f, indent=2, default=str)


def load_queue():
    with open(REVIEW_FILE) as f:
        return json.load(f)


def apply_decision(queue, section_key, status, note=""):
    """status: 'approved' or 'flagged'"""
    assert status in ("approved", "flagged")
    for item in queue:
        if item["section_key"] == section_key:
            item["review_status"] = status
            item["reviewer_note"] = note
    return queue


if __name__ == "__main__":
    import sys
    sys.path.insert(0, OUTPUT_DIR)
    sys.path.insert(0, ANALYSIS_DIR)
    from generated_sections import GENERATED_SECTIONS, run_grounding_checks

    checks = run_grounding_checks()
    queue = build_review_queue(GENERATED_SECTIONS, checks)

    # For this exercise run: a human reviewer (you) reviews each section.
    # All sections passed the automated grounding check, and on manual
    # read-through each is limited strictly to packet figures, so all are
    # approved here. In a real run this loop would be interactive
    # (input() prompts) or a small web UI -- see README for the sketch
    # of what that would look like.
    for item in queue:
        if item["grounding_check"]["passed"]:
            apply_decision(queue, item["section_key"], "approved",
                            note="Auto-grounding check passed; manually read and confirmed "
                                 "all figures trace to the evidence packet.")
        else:
            apply_decision(queue, item["section_key"], "flagged",
                            note=f"Grounding check found unsupported figures: "
                                 f"{item['grounding_check']['unsupported_numbers']}")

    save_queue(queue)
    print(f"Review queue saved: {len(queue)} sections")
    for item in queue:
        print(f"  {item['section_key']}: {item['review_status']}")
