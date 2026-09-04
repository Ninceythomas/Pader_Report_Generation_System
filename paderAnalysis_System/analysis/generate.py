"""
generate.py
-----------
Calls Claude once per report section, using the shared system prompt +
that section's evidence packet. Also runs a lightweight, DETERMINISTIC
grounding check on the output before it's handed to the human reviewer.

WHY a grounding check, and why it's not itself an LLM call:
  The brief's central rule is "the report can only say what the data
  supports." A second LLM call asking "is this grounded?" is tempting but
  weak -- it's the same class of model making the same class of mistake
  it might make in generation, just applied to review. Instead, the check
  here is mechanical: every number that appears in the generated text is
  extracted and verified against the numbers that were actually present in
  the packet sent to the model. If the model wrote a number that isn't in
  its own evidence packet, that's a hard, catchable, deterministic signal
  something went wrong -- not a judgment call.

  This does not catch every failure mode (e.g. a subtle unsupported
  qualitative claim like "clearly concerning" without a number attached).
  That's why grounding-check output feeds the human review step rather
  than auto-approving -- see review/review.py and the README's
  Evaluation section for the full picture.
"""

import json
import os
import re
import urllib.request


API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"


def call_claude(system_prompt, user_content, max_tokens=800):
    """
    Minimal direct call to the Messages API. No SDK dependency, so this
    runs anywhere Python + internet does.

    Requires ANTHROPIC_API_KEY to be set as an environment variable:
        export ANTHROPIC_API_KEY=sk-ant-...
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Run: export ANTHROPIC_API_KEY=your-key-here"
        )

    body = {
        "model": MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_content}],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return "".join(block["text"] for block in data["content"] if block["type"] == "text")


def _extract_numbers_from_packet(packet):
    """
    Pulls every numeric value out of the FULL packet (both
    approved_analysis_results and reporting_period -- dates and IDs there
    are also legitimate, packet-sourced numbers a section is allowed to
    mention, e.g. the reporting period start/end dates), as strings, so
    they can be checked for presence in the generated text.

    Also decomposes date strings like "2024-12-27" and range labels like
    "18-64" into their component numbers, since the generated prose may
    reasonably reformat "2024-12-27" as "December 2024" or similar and
    still be grounded.
    """
    numbers = set()

    def add_number(n):
        s = str(n)
        numbers.add(s)
        # also add without leading zeros (e.g. "06" -> "6") and as int-if-whole
        try:
            f = float(s)
            if f == int(f):
                numbers.add(str(int(f)))
        except ValueError:
            pass

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(k)   # dict KEYS can carry numbers too, e.g. "Adult (18-64yr)"
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, bool):
            pass  # booleans are not data points to ground against
        elif isinstance(obj, (int, float)):
            add_number(obj)
        elif isinstance(obj, str):
            # decompose any embedded numeric substrings (dates, ranges, IDs)
            for piece in re.findall(r"\d+", obj):
                add_number(piece)
                add_number(piece.lstrip("0") or "0")  # strip leading zeros

    walk(packet.get("approved_analysis_results", {}))
    walk(packet.get("reporting_period", {}))
    return numbers


# Fixed regulatory/domain terms that legitimately contain a number but are
# not derived from the dataset (e.g. "15-day Alert" is a defined regulatory
# term, not a computed figure). Kept short and explicit -- anything not in
# this list must trace back to the packet.
DOMAIN_TERM_NUMBERS = {"15"}  # "15-day Alert" reporting category


def grounding_check(generated_text, packet):
    """
    Extracts every standalone number the model wrote (including comma-
    grouped numbers like "1,023", which are normalized to "1023" before
    comparison) and flags any that do not appear anywhere in the packet's
    numbers. Returns a dict the human reviewer sees alongside the
    generated section.

    This is a coarse, deliberately mechanical check -- see module
    docstring for why it's intentionally not another LLM call.
    """
    packet_numbers = _extract_numbers_from_packet(packet)

    # Match comma-grouped numbers as a single token first (e.g. "1,023"),
    # then strip the commas before comparing -- so "1,023" is checked as
    # "1023", not accidentally split into "1" and "023".
    raw_tokens = re.findall(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+(?:\.\d+)?\b", generated_text)
    written_numbers = set(t.replace(",", "") for t in raw_tokens)

    unsupported = sorted(
        written_numbers - packet_numbers - DOMAIN_TERM_NUMBERS,
        key=lambda x: float(x),
    )

    return {
        "passed": len(unsupported) == 0,
        "unsupported_numbers": unsupported,
        "packet_numbers_available": sorted(packet_numbers, key=lambda x: float(x)),
    }


def generate_section(section_key, packet, system_prompt):
    """
    Generates prose for one section and runs the grounding check.
    Returns a dict ready for the human review queue.
    """
    user_content = (
        "Evidence packet:\n\n"
        + json.dumps(packet, indent=2, default=str)
        + "\n\nWrite this section now, following the instructions in the packet "
          "and the hard rules in your system prompt."
    )
    text = call_claude(system_prompt, user_content)
    check = grounding_check(text, packet)

    return {
        "section_key": section_key,
        "section_name": packet["section"],
        "packet": packet,
        "generated_text": text.strip(),
        "grounding_check": check,
        "review_status": "pending",  # human sets this to "approved" or "flagged"
    }
