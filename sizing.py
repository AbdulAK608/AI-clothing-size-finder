"""
sizing.py

The recommendation engine for the AI Clothing Size Finder.

Takes:
    - user_measurements: dict of body measurement -> cm value
      e.g. {"chest": 102.0, "waist": 84.0, "height": 173.0}
    - size_chart: dict of size label -> dict of measurement -> (min_cm, max_cm)
      e.g. {"M": {"chest": (96, 101), "waist": (81, 86)}, ...}
    - clothing_type: "shirt" | "pants" | "shoes" | "hat" | "unknown"
    - fit_preference: "fitted" | "regular" | "relaxed" | "oversized" | "not_sure"

Returns a dict with:
    - recommended_size: str or None
    - alternative_size: str or None (only if between sizes)
    - confidence: "High" | "Medium" | "Low"
    - explanation: str
    - details: list of per-size comparison dicts (for the results page)

The engine deliberately uses simple, transparent logic so the reasoning
can be inspected and explained line-by-line.
"""

# Which body measurements matter for each clothing category, in priority order.
CATEGORY_MEASUREMENTS = {
    "shirt":  ["chest", "shoulder", "waist"],
    "hoodie": ["chest", "shoulder", "waist"],
    "jacket": ["chest", "shoulder", "waist"],
    "pants":  ["waist", "hips", "inseam"],
    "jeans":  ["waist", "hips", "inseam"],
    "shorts": ["waist", "hips"],
    "shoes":  ["foot_length", "foot_width"],
    "hat":    ["head_circumference"],
}


def get_relevant_measurements(clothing_type):
    """Return the ordered list of measurements that matter for this category."""
    return CATEGORY_MEASUREMENTS.get(
        clothing_type.lower() if clothing_type else "unknown", []
    )


def score_size_against_user(user_measurements, size_measurements, relevant_measurements):
    """
    Score how well one size fits the user.

    Scoring rule:
        - Inside range:              +2
        - Just outside (within 3cm): +1  (near-miss)
        - Way outside (>3cm):         0
        - Missing user measurement:   skipped entirely
    """
    NEAR_MISS_CM = 3.0

    score = 0
    matches, below, above, missing = [], [], [], []

    for m in relevant_measurements:
        user_value = user_measurements.get(m)
        size_range = size_measurements.get(m)

        if user_value is None or size_range is None:
            missing.append(m)
            continue

        lo, hi = size_range

        if lo <= user_value <= hi:
            score += 2
            matches.append(m)
        elif user_value < lo:
            if lo - user_value <= NEAR_MISS_CM:
                score += 1
            below.append(m)
        else:
            if user_value - hi <= NEAR_MISS_CM:
                score += 1
            above.append(m)

    return {
        "score": score,
        "matches": matches,
        "below": below,
        "above": above,
        "missing": missing,
    }


def _fit_preference_bias(fit_preference, size_labels_lo_hi):
    """
    Small, transparent bias based on fit preference.

    Returns dict: size_label -> score adjustment (int).
    Only +/-1 so it can break ties but never override clear evidence.
    """
    adjustments = {label: 0 for label in size_labels_lo_hi}

    if fit_preference == "fitted":
        if size_labels_lo_hi:
            adjustments[size_labels_lo_hi[0]] += 1
            adjustments[size_labels_lo_hi[-1]] -= 1

    elif fit_preference in ("relaxed", "oversized"):
        if size_labels_lo_hi:
            adjustments[size_labels_lo_hi[-1]] += 1
            adjustments[size_labels_lo_hi[0]] -= 1

    # "regular" and "not_sure" -> no bias

    return adjustments


def recommend_size(user_measurements, size_chart, clothing_type="unknown", fit_preference="regular"):
    """
    Main entry point.

    Returns:
        {
          "recommended_size": str | None,
          "alternative_size": str | None,
          "confidence":       "High" | "Medium" | "Low",
          "explanation":      str,
          "details":          list of dicts (per-size breakdown)
        }
    """
    if not size_chart:
        return {
            "recommended_size": None,
            "alternative_size": None,
            "confidence": "Low",
            "explanation": "No size chart was provided.",
            "details": [],
        }

    relevant = get_relevant_measurements(clothing_type)
    if not relevant:
        all_keys = set()
        for size_data in size_chart.values():
            all_keys.update(size_data.keys())
        relevant = sorted(all_keys)

    # Score each size
    details = []
    for size_label, size_measurements in size_chart.items():
        result = score_size_against_user(user_measurements, size_measurements, relevant)
        result["size"] = size_label
        details.append(result)

    # Sort sizes from small to large by first available relevant measurement
    def sort_key(item):
        size_data = size_chart[item["size"]]
        for m in relevant:
            if m in size_data:
                return size_data[m][0]
        return float("inf")

    details_sorted_lo_hi = sorted(details, key=sort_key)
    size_labels_lo_hi = [d["size"] for d in details_sorted_lo_hi]

    # Apply fit preference bias
    bias = _fit_preference_bias(fit_preference, size_labels_lo_hi)
    for d in details:
        d["bias"] = bias.get(d["size"], 0)
        d["final_score"] = d["score"] + d["bias"]

    # Rank
    ranked = sorted(details, key=lambda d: (-d["final_score"], -d["score"]))
    best = ranked[0]

    # Between-size detection
    alternative = None
    if len(ranked) > 1:
        second = ranked[1]
        if second["final_score"] == best["final_score"]:
            alternative = second["size"]

    # Confidence
    matched_count = len(best["matches"])
    provided_count = len([m for m in relevant if user_measurements.get(m) is not None])

    if provided_count == 0:
        confidence = "Low"
    elif matched_count >= 2 and not best["above"] and not best["below"]:
        confidence = "High"
    elif matched_count >= 1 or alternative is not None:
        confidence = "Medium"
    else:
        confidence = "Low"

    explanation = _build_explanation(best, alternative, fit_preference)

    return {
        "recommended_size": best["size"],
        "alternative_size": alternative,
        "confidence": confidence,
        "explanation": explanation,
        "details": details,
    }


def _build_explanation(best, alternative, fit_preference):
    """Produce a short, human-readable explanation string."""
    parts = []

    if best["matches"]:
        parts.append(
            "Your " + ", ".join(best["matches"]) +
            f" measurement(s) fall within the {best['size']} range."
        )

    if best["below"]:
        parts.append(
            "Your " + ", ".join(best["below"]) +
            f" is slightly below the {best['size']} minimum."
        )

    if best["above"]:
        parts.append(
            "Your " + ", ".join(best["above"]) +
            f" is slightly above the {best['size']} maximum."
        )

    if alternative:
        parts.append(
            f"You also fit {alternative} closely. Fit preference "
            f"'{fit_preference}' was used to break the tie."
        )

    if not parts:
        parts.append("Not enough measurements to give a clear explanation.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Self-tests: run  python sizing.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    shirt_chart = {
        "S":  {"chest": (86, 96),   "waist": (76, 81),  "shoulder": (42, 44)},
        "M":  {"chest": (96, 101),  "waist": (81, 86),  "shoulder": (44, 46)},
        "L":  {"chest": (101, 107), "waist": (86, 94),  "shoulder": (46, 49)},
        "XL": {"chest": (107, 117), "waist": (94, 104), "shoulder": (49, 52)},
    }

    print("=" * 60)
    print("Test 1: Clear Large match, regular fit")
    print("=" * 60)
    user = {"chest": 103.0, "waist": 88.0, "shoulder": 47.0}
    r = recommend_size(user, shirt_chart, "shirt", "regular")
    print("Recommended:", r["recommended_size"])
    print("Alternative:", r["alternative_size"])
    print("Confidence: ", r["confidence"])
    print("Explanation:", r["explanation"])

    print()
    print("=" * 60)
    print("Test 2: Between M and L, fitted preference")
    print("=" * 60)
    user = {"chest": 100.5, "waist": 83.5, "shoulder": 45.0}
    r = recommend_size(user, shirt_chart, "shirt", "fitted")
    print("Recommended:", r["recommended_size"])
    print("Alternative:", r["alternative_size"])
    print("Confidence: ", r["confidence"])
    print("Explanation:", r["explanation"])

    print()
    print("=" * 60)
    print("Test 3: Same measurements, oversized preference")
    print("=" * 60)
    r = recommend_size(user, shirt_chart, "shirt", "oversized")
    print("Recommended:", r["recommended_size"])
    print("Alternative:", r["alternative_size"])
    print("Confidence: ", r["confidence"])
    print("Explanation:", r["explanation"])

    print()
    print("=" * 60)
    print("Test 4: Only chest provided")
    print("=" * 60)
    r = recommend_size({"chest": 99.0}, shirt_chart, "shirt", "regular")
    print("Recommended:", r["recommended_size"])
    print("Confidence: ", r["confidence"])
    print("Explanation:", r["explanation"])

    print()
    print("=" * 60)
    print("Test 5: No size chart")
    print("=" * 60)
    r = recommend_size({"chest": 100}, {}, "shirt")
    print("Recommended:", r["recommended_size"])
    print("Confidence: ", r["confidence"])
    print("Explanation:", r["explanation"])

    print()
    print("=" * 60)
    print("Test 6: Pants chart")
    print("=" * 60)
    pants_chart = {
        "30": {"waist": (76, 79), "hips": (94, 97),  "inseam": (78, 81)},
        "32": {"waist": (81, 84), "hips": (99, 102), "inseam": (78, 81)},
        "34": {"waist": (86, 89), "hips": (104, 107),"inseam": (79, 82)},
    }
    user = {"waist": 82.0, "hips": 100.0, "inseam": 80.0}
    r = recommend_size(user, pants_chart, "pants", "regular")
    print("Recommended:", r["recommended_size"])
    print("Confidence: ", r["confidence"])
    print("Explanation:", r["explanation"])

    