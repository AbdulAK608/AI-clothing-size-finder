"""
conversions.py

Unit conversion helpers for the AI Clothing Size Finder.

Internal standard:
    - Lengths  -> centimeters (cm)
    - Weights  -> kilograms (kg)
"""

CM_PER_INCH = 2.54
KG_PER_POUND = 0.45359237
INCHES_PER_FOOT = 12


def feet_inches_to_cm(feet, inches):
    """Convert feet + inches to centimeters. Example: (5, 8) -> 172.72."""
    total_inches = (feet * INCHES_PER_FOOT) + inches
    return round(total_inches * CM_PER_INCH, 2)


def inches_to_cm(inches):
    """Convert inches to centimeters."""
    return round(inches * CM_PER_INCH, 2)


def cm_to_inches(cm):
    """Convert centimeters to inches."""
    return round(cm / CM_PER_INCH, 2)


def pounds_to_kg(pounds):
    """Convert pounds to kilograms."""
    return round(pounds * KG_PER_POUND, 2)


def kg_to_pounds(kg):
    """Convert kilograms to pounds."""
    return round(kg / KG_PER_POUND, 2)


def parse_height(text):
    """Parse a height string into centimeters.

    Accepts: "5'8\\"", "5'8", "5 ft 8 in", "173", "173 cm", "68 in".
    Returns None if input can't be understood.
    """
    if text is None:
        return None

    text = text.strip().lower()
    if text == "":
        return None

    if "'" in text or "ft" in text or "feet" in text:
        normalized = (
            text.replace("feet", "'")
                .replace("ft", "'")
                .replace("inches", '"')
                .replace("inch", '"')
                .replace("in", '"')
                .replace(" ", "")
        )
        try:
            parts = normalized.split("'")
            feet = float(parts[0])
            inches_str = parts[1].replace('"', '') if len(parts) > 1 else "0"
            inches = float(inches_str) if inches_str else 0.0
            return feet_inches_to_cm(feet, inches)
        except (ValueError, IndexError):
            return None

    if "cm" in text:
        try:
            return float(text.replace("cm", "").strip())
        except ValueError:
            return None

    if text.endswith("in") or text.endswith("inch") or text.endswith("inches"):
        try:
            number = text.replace("inches", "").replace("inch", "").replace("in", "").strip()
            return inches_to_cm(float(number))
        except ValueError:
            return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_weight(text):
    """Parse a weight string into kilograms.

    Accepts: "208 lb", "208lbs", "94 kg", "94kg", "94".
    Returns None if input can't be understood.
    """
    if text is None:
        return None

    text = text.strip().lower().replace(" ", "")
    if text == "":
        return None

    if text.endswith("lbs") or text.endswith("lb") or text.endswith("pounds"):
        number = text.replace("pounds", "").replace("lbs", "").replace("lb", "")
        try:
            return pounds_to_kg(float(number))
        except ValueError:
            return None

    if text.endswith("kg") or text.endswith("kgs") or text.endswith("kilograms"):
        number = text.replace("kilograms", "").replace("kgs", "").replace("kg", "")
        try:
            return float(number)
        except ValueError:
            return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_length(text, default_unit="cm"):
    """Parse a body-measurement string into centimeters.

    Accepts: "42", "42 in", "42in", "107 cm", "107cm".
    default_unit: "cm" or "in" for bare numbers.
    """
    if text is None:
        return None

    text = text.strip().lower().replace(" ", "")
    if text == "":
        return None

    if text.endswith("cm"):
        try:
            return float(text.replace("cm", ""))
        except ValueError:
            return None

    if text.endswith("in") or text.endswith("inches") or text.endswith("inch"):
        number = text.replace("inches", "").replace("inch", "").replace("in", "")
        try:
            return inches_to_cm(float(number))
        except ValueError:
            return None

    try:
        value = float(text)
    except ValueError:
        return None

    if default_unit == "in":
        return inches_to_cm(value)
    return value


if __name__ == "__main__":
    print("--- Height tests ---")
    print("5'8\"        ->", parse_height("5'8\""), "cm (expect ~172.72)")
    print("5'8         ->", parse_height("5'8"), "cm (expect ~172.72)")
    print("5 ft 8 in   ->", parse_height("5 ft 8 in"), "cm (expect ~172.72)")
    print("173 cm      ->", parse_height("173 cm"), "cm (expect 173.0)")
    print("68 in       ->", parse_height("68 in"), "cm (expect ~172.72)")
    print("173         ->", parse_height("173"), "cm (expect 173.0)")
    print("garbage     ->", parse_height("hello"))

    print("\n--- Weight tests ---")
    print("208 lb      ->", parse_weight("208 lb"), "kg (expect ~94.35)")
    print("208lbs      ->", parse_weight("208lbs"), "kg (expect ~94.35)")
    print("94 kg       ->", parse_weight("94 kg"), "kg (expect 94.0)")
    print("94          ->", parse_weight("94"), "kg (expect 94.0)")

    print("\n--- Length tests ---")
    print("42 in       ->", parse_length("42 in"), "cm (expect ~106.68)")
    print("42          ->", parse_length("42"), "cm (expect 42.0)")
    print("42 (in)     ->", parse_length("42", default_unit="in"), "cm (expect ~106.68)")
    print("107cm       ->", parse_length("107cm"), "cm (expect 107.0)")
    