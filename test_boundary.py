from sizing import recommend_size

chart = {
    "M": {"chest": (96, 101),  "waist": (81, 86), "shoulder": (44, 46)},
    "L": {"chest": (101, 107), "waist": (86, 94), "shoulder": (46, 49)},
}

user = {"chest": 101.0, "waist": 86.0, "shoulder": 46.0}

for fit in ["fitted", "regular", "relaxed", "oversized"]:
    r = recommend_size(user, chart, "shirt", fit)
    print(f"{fit:10s} -> {r['recommended_size']}  (alt: {r['alternative_size']})")

    