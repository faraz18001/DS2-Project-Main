"""
topic_mapper.py — Keyword-to-topic tagging engine.

Uses a keyword frequency scoring approach to assign topic labels
to extracted questions. Keyword maps are derived from Cambridge
syllabuses and stored as JSON files.
"""

import json
import re


def load_keyword_map(path):
    """
    Load the keyword-to-topic mapping JSON file.

    Expected format:
    {
        "9702": {
            "Kinematics": ["velocity", "acceleration", "displacement", ...],
            "Dynamics": ["force", "newton", "momentum", ...],
            ...
        }
    }

    Args:
        path: str, path to keyword_map.json.

    Returns:
        dict mapping subject_code → topic → list of keywords.
    """
    with open(path, "r") as f:
        return json.load(f)


def tag_question(question_text, subject_code, keyword_map):
    """
    based on "bag of words text classification" algorithm
    Assign one or more topic labels to a question based on keyword frequency.

    Steps:
    1. Normalize the question text (lowercase, strip punctuation).
    2. For each topic in the keyword map for this subject, count how many
       of its keywords appear in the text.
    3. Rank topics by hit count; assign the top-scoring topic(s).
    4. If no keywords match, tag as "Uncategorized".

    Args:
        question_text: str, raw text of the question.
        subject_code: str, e.g. "9702".
        keyword_map: dict, loaded from load_keyword_map().

    Returns:
        list of str, topic labels (usually 1, sometimes 2 for cross-topic).
    """
    if subject_code not in keyword_map:
        return ["Uncategorized"]

    # Normalize: lowercase, strip markdown formatting and punctuation
    normalized = question_text.lower()
    normalized = re.sub(r'[*_#\[\]()!]', ' ', normalized)   # strip markdown
    normalized = re.sub(r'[^a-z0-9\s-]', ' ', normalized)   # keep only alphanum
    words = normalized.split()

    topics_for_subject = keyword_map[subject_code]

    # Score each topic by counting keyword hits
    scores = {}
    for topic, keywords in topics_for_subject.items():
        count = 0
        for keyword in keywords:
            # Keywords can be multi-word (e.g. "specific heat"), so check
            # against the full normalized text for those, and against the
            # word list for single-word keywords.
            if ' ' in keyword:
                # Multi-word keyword: search in full text
                count += normalized.count(keyword.lower())
            else:
                # Single-word keyword: count occurrences in word list
                kw_lower = keyword.lower()
                count += words.count(kw_lower)
        if count > 0:
            scores[topic] = count

    if not scores:
        return ["Uncategorized"]

    # Sort topics by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print(ranked)
    

    # Always include the top topic
    best_score = ranked[0][1]
    result = [ranked[0][0]]

    # Include a second topic only if it scores at least 60% of the best
    # if len(ranked) > 1 and ranked[1][1] >= best_score * 0.6:
    #     result.append(ranked[1][0])

    for item in ranked[1:]:
        if item[1] >= best_score * 0.6:
            result.append(item[0])

    return result


def build_composite_keys(subject_code, topics , paper_type):
    """
    Construct composite index keys from subject, topics, and paper type.

    Example: subject="9702", topics=["Kinematics"], paper_type="P2"
             → ["9702_Kinematics_P2"]

    Args:
        subject_code: str.
        topics: list of str.
        paper_type: str.

    Returns:
        list of composite key strings.
    """
    keys = []
    for topic in topics:
        keys.append(f"{subject_code}_{topic}_{paper_type}")
    return keys


"""
res = tag_question("calculate the velocity and mass", "9702", {
    "5054": {
        "Measurement": ["measure", "unit", "prefix", "error", "accuracy", "precision", "instrument", "reading", "scale", "uncertainty", "vernier", "micrometer", "caliper"],
        "Kinematics": ["velocity", "acceleration", "displacement", "speed", "distance", "time", "gradient", "slope", "graph", "motion", "deceleration", "free fall", "terminal"],
        "Forces": ["force", "newton", "weight", "friction", "tension", "moment", "torque", "equilibrium", "pivot", "resultant", "balanced", "unbalanced", "spring", "hooke", "extension", "load", "pressure", "density"],
        "Energy": ["work", "kinetic", "potential", "power", "efficiency", "joule", "watt", "conservation", "energy", "gravitational potential"],
        "Thermal Physics": ["temperature", "heat", "thermal", "conduction", "convection", "radiation", "specific heat", "boiling", "melting", "evaporation", "latent", "expansion", "thermometer", "celsius", "kelvin"],
        "Waves": ["wave", "frequency", "wavelength", "amplitude", "oscillation", "sound", "light", "diffraction", "refraction", "reflection", "lens", "mirror", "prism", "spectrum", "electromagnetic", "transverse", "longitudinal", "period"],
        "Electricity": ["current", "voltage", "resistance", "circuit", "ohm", "series", "parallel", "cell", "battery", "wire", "resistor", "ammeter", "voltmeter", "diode", "thermistor", "ldr", "potential divider", "electromotive"],
        "Magnetism": ["magnetic", "field", "electromagnet", "motor", "generator", "induced", "solenoid", "compass", "relay", "transformer", "induction", "alternating", "direct current"],
        "Nuclear Physics": ["nucleus", "atom", "proton", "neutron", "electron", "radioactive", "decay", "half-life", "alpha", "beta", "gamma", "isotope", "nucleon", "atomic number", "mass number", "fission", "fusion"]
    },
    "9702": {
        "Kinematics": ["velocity", "acceleration", "displacement", "speed", "slope", "gradient", "vector"],
        "Dynamics": ["force", "newton", "momentum", "impulse", "mass", "friction", "tension", "weight"],
        "Energy": ["work", "kinetic", "potential", "power", "efficiency", "joule", "watt"]
    }
}
)
"""