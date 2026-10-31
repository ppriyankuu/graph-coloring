import pandas as pd
import networkx as nx
from datetime import date, timedelta
from pathlib import Path

DATA_FILE = "synthetic_exam_scheduling_enrollments.csv"
OUTPUT_DIR = Path("exam_scheduler_output")

# ---- EDIT THESE TO MATCH YOUR ASSIGNMENT -------------------------------
START_DATE = date(2026, 11, 16)      # first exam day
EXAM_DATES = None                    # or a fixed list, e.g. [date(2026, 11, 16), date(2026, 11, 18)]
SKIP_WEEKDAYS = {6}                  # Monday=0 ... Sunday=6; {5, 6} skips Sat and Sun
SESSIONS = [("Morning", "09:00-12:00"), ("Afternoon", "13:00-16:00")]
# -------------------------------------------------------------------------


def load_data():
    df = pd.read_csv(DATA_FILE)
    return df.drop_duplicates(subset=["student_id", "subject_code"])


def build_graph(df):
    subjects = (
        df[["subject_code", "subject_name", "subject_type"]]
        .drop_duplicates()
        .sort_values("subject_code")
    )
    G = nx.Graph()
    G.add_nodes_from(subjects["subject_code"])

    students_by_subject = df.groupby("subject_code")["student_id"].apply(set)
    codes = subjects["subject_code"].tolist()

    for i, a in enumerate(codes):
        for b in codes[i + 1:]:
            if students_by_subject[a] & students_by_subject[b]:
                G.add_edge(a, b)
    return G, subjects


def color_graph(G):
    # Try several greedy strategies and keep the one that uses the fewest slots.
    strategies = ["largest_first", "smallest_last", "saturation_largest_first"]
    best = None
    for strategy in strategies:
        colors = nx.coloring.greedy_color(G, strategy=strategy)
        if best is None or max(colors.values()) < max(best[1].values()):
            best = (strategy, colors)
    return best


def make_slots(slot_count):
    """Turn slot numbers into (date, session, time), skipping non-exam days."""
    slots = []
    if EXAM_DATES:
        days = iter(EXAM_DATES)
    else:
        def day_generator():
            d = START_DATE
            while True:
                if d.weekday() not in SKIP_WEEKDAYS:
                    yield d
                d += timedelta(days=1)
        days = day_generator()

    for d in days:
        for session, time in SESSIONS:
            slots.append((d, session, time))
            if len(slots) == slot_count:
                return slots
    raise ValueError(
        f"Need {slot_count} slots but only {len(slots)} are available. "
        "Add more dates or sessions."
    )


def build_timetable(subjects, colors, df):
    slot_count = max(colors.values()) + 1
    slots = make_slots(slot_count)
    enrolled = df.groupby("subject_code")["student_id"].nunique()
    info = subjects.set_index("subject_code")

    rows = []
    for code, color in colors.items():
        d, session, time = slots[color]
        rows.append({
            "slot": color + 1,
            "date": d.strftime("%d-%m-%Y"),
            "weekday": d.strftime("%A"),
            "session": session,
            "time": time,
            "subject_code": code,
            "subject_name": info.loc[code, "subject_name"],
            "subject_type": info.loc[code, "subject_type"],
            "students": int(enrolled[code]),
        })
    timetable = pd.DataFrame(rows).sort_values(["slot", "subject_code"])

    # Compact view: one row per slot
    by_slot = (
        timetable.groupby(["slot", "date", "weekday", "session", "time"])["subject_code"]
        .apply(lambda s: ", ".join(s))
        .reset_index()
        .rename(columns={"subject_code": "subjects"})
    )
    return timetable, by_slot, slot_count


def validate(df, G, colors):
    bad_edges = [(a, b) for a, b in G.edges() if colors[a] == colors[b]]
    mapped = df[["student_id", "subject_code"]].copy()
    mapped["slot"] = mapped["subject_code"].map(colors)
    clashes = [
        s for s, g in mapped.groupby("student_id") if g["slot"].duplicated().any()
    ]
    return bad_edges, clashes


def main():
    if not Path(DATA_FILE).exists():
        raise FileNotFoundError(f"Cannot find {DATA_FILE} in this folder.")

    OUTPUT_DIR.mkdir(exist_ok=True)
    df = load_data()
    G, subjects = build_graph(df)

    strategy, colors = color_graph(G)
    timetable, by_slot, slot_count = build_timetable(subjects, colors, df)

    timetable.to_csv(OUTPUT_DIR / "exam_timetable.csv", index=False)
    by_slot.to_csv(OUTPUT_DIR / "exam_timetable_by_slot.csv", index=False)

    bad_edges, clashes = validate(df, G, colors)

    print("=== SUMMARY ===")
    print("Students:", df["student_id"].nunique())
    print("Subjects (vertices):", G.number_of_nodes())
    print("Conflict edges:", G.number_of_edges())
    print(f"Coloring strategy used: {strategy}")
    print("Time slots needed (colors):", slot_count)

    print("\n=== VALIDATION ===")
    if not bad_edges and not clashes:
        print("PASS: no student has two exams in the same slot.")
    else:
        print("FAIL: conflicting edges:", bad_edges)
        print("FAIL: students with clashes:", clashes)

    print("\n=== FINAL TIMETABLE (by slot) ===")
    print(by_slot.to_string(index=False))

    print("\n=== FINAL TIMETABLE (detailed) ===")
    print(timetable.to_string(index=False))
    print("\nSaved to:", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
