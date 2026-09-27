"""
app.py

Flask web app for the AI Clothing Size Finder.

Stage 9: full form -> sizing engine -> results page.
For now, uses a hardcoded demo size chart. Scraping and manual
size-chart input are added in later stages.
"""

from flask import Flask, render_template, request

from conversions import parse_height, parse_weight, parse_length
from sizing import recommend_size

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Demo size charts (centimeters). These stand in for real product charts
# until scraping and manual input are implemented.
# ---------------------------------------------------------------------------
DEMO_CHARTS = {
    "shirt": {
        "S":  {"chest": (86, 96),   "waist": (76, 81),  "shoulder": (42, 44)},
        "M":  {"chest": (96, 101),  "waist": (81, 86),  "shoulder": (44, 46)},
        "L":  {"chest": (101, 107), "waist": (86, 94),  "shoulder": (46, 49)},
        "XL": {"chest": (107, 117), "waist": (94, 104), "shoulder": (49, 52)},
    },
    "pants": {
        "30": {"waist": (76, 79), "hips": (94, 97),  "inseam": (78, 81)},
        "32": {"waist": (81, 84), "hips": (99, 102), "inseam": (78, 81)},
        "34": {"waist": (86, 89), "hips": (104, 107),"inseam": (79, 82)},
    },
    "shoes": {
        "US 9":  {"foot_length": (26.0, 26.7), "foot_width": (9.5, 10.0)},
        "US 10": {"foot_length": (26.7, 27.3), "foot_width": (9.8, 10.3)},
        "US 11": {"foot_length": (27.3, 28.0), "foot_width": (10.1, 10.6)},
    },
    "hat": {
        "S/M": {"head_circumference": (54, 57)},
        "L/XL": {"head_circumference": (57, 61)},
    },
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/results", methods=["POST"])
def results():
    print("FORM DATA:", dict(request.form))
    form = request.form

    

    # --- 1. Parse basics -------------------------------------------------
    height_cm = parse_height(form.get("height", ""))
    weight_kg = parse_weight(form.get("weight", ""))

    clothing_type = (form.get("clothing_type") or "unknown").lower()
    fit_preference = form.get("fit_preference") or "regular"
    unit = form.get("unit", "cm")

    # --- 2. Parse body measurements --------------------------------------
    # We map form field names -> canonical measurement keys used by sizing.py
    measurement_fields = [
        "chest", "waist", "hips", "shoulder", "sleeve",
        "inseam", "thigh", "foot_length", "foot_width", "head_circumference",
    ]

    user_measurements = {}
    for field in measurement_fields:
        raw = form.get(field, "").strip()
        if not raw:
            continue
        value_cm = parse_length(raw, default_unit=unit)
        if value_cm is not None:
            user_measurements[field] = value_cm

    if height_cm is not None:
        user_measurements["height"] = height_cm
    if weight_kg is not None:
        user_measurements["weight"] = weight_kg

    # --- 3. Pick a size chart --------------------------------------------
    size_chart = DEMO_CHARTS.get(clothing_type)
    if size_chart is None:
        return render_template(
            "results.html",
            error=(
                "We don't have a demo chart for that clothing type yet. "
                "Try 'Shirt', 'Pants', 'Shoes', or 'Hat'."
            ),
            result=None,
            user_display={},
            size_chart={},
            chart_measurements=[],
        )

    # --- 4. Run the recommendation engine --------------------------------
    result = recommend_size(
        user_measurements=user_measurements,
        size_chart=size_chart,
        clothing_type=clothing_type,
        fit_preference=fit_preference,
    )

    # If the engine couldn't recommend anything, show a friendly message.
    if not result["recommended_size"]:
        return render_template(
            "results.html",
            error=(
                "We couldn't recommend a size because none of the "
                "relevant measurements matched the chart. "
                "Try filling in more measurements."
            ),
            result=None,
            user_display={},
            size_chart=size_chart,
            chart_measurements=sorted({m for s in size_chart.values() for m in s}),
        )

    # --- 5. Prepare display values ---------------------------------------
    # Show the user what they entered, in the units they used where practical.
    user_display = {
        "height": form.get("height", ""),
        "weight": form.get("weight", ""),
        "chest": form.get("chest", ""),
        "waist": form.get("waist", ""),
        "hips": form.get("hips", ""),
        "shoulder": form.get("shoulder", ""),
        "sleeve": form.get("sleeve", ""),
        "inseam": form.get("inseam", ""),
        "thigh": form.get("thigh", ""),
        "foot_length": form.get("foot_length", ""),
        "foot_width": form.get("foot_width", ""),
        "head_circumference": form.get("head_circumference", ""),
    }

    chart_measurements = sorted({m for s in size_chart.values() for m in s})

    return render_template(
        "results.html",
        result=result,
        user_display=user_display,
        size_chart=size_chart,
        chart_measurements=chart_measurements,
    )


if __name__ == "__main__":
    app.run(debug=True)

