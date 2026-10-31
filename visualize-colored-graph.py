import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from pathlib import Path

DATA_FILE = "synthetic_exam_scheduling_enrollments.csv"
OUTPUT_DIR = Path("exam_scheduler_output")
TIMETABLE_CSV = OUTPUT_DIR / "exam_timetable.csv"

# Light fills so the dark subject codes stay readable
PALETTE = [
    "#A6CEE3", "#FDBF6F", "#B2DF8A", "#FB9A99", "#CAB2D6", "#FFFF99",
    "#8DD3C7", "#FCCDE5", "#D9D9D9", "#BEBADA", "#FDB462", "#80B1D3",
    "#B3DE69", "#FFED6F", "#CCEBC5", "#E5C494", "#F4A582", "#92C5DE",
    "#C7E9C0", "#DADAEB",
]


def build_graph(df):
    subjects = df[["subject_code", "subject_type"]].drop_duplicates().sort_values("subject_code")
    G = nx.Graph()
    for row in subjects.itertuples(index=False):
        G.add_node(row.subject_code, subject_type=row.subject_type)

    students = df.groupby("subject_code")["student_id"].apply(set)
    codes = subjects["subject_code"].tolist()
    for i, a in enumerate(codes):
        for b in codes[i + 1:]:
            if students[a] & students[b]:
                G.add_edge(a, b)
    return G


def main():
    for f in (Path(DATA_FILE), TIMETABLE_CSV):
        if not f.exists():
            raise FileNotFoundError(f"Cannot find {f}. Run the scheduler script first.")

    enrollments = pd.read_csv(DATA_FILE).drop_duplicates(subset=["student_id", "subject_code"])
    timetable = pd.read_csv(TIMETABLE_CSV)

    G = build_graph(enrollments)

    # The slot number of each subject IS its color from the scheduler
    slot_of = timetable.set_index("subject_code")["slot"].to_dict()
    slot_info = (
        timetable.drop_duplicates("slot").sort_values("slot")
        .set_index("slot")[["date", "session"]].to_dict("index")
    )
    slots = sorted(slot_info)
    if len(slots) > len(PALETTE):
        raise ValueError("More slots than palette colors; add colors to PALETTE.")
    color_of_slot = {s: PALETTE[i] for i, s in enumerate(slots)}

    # Check the coloring: no edge may join two vertices with the same slot
    bad = [(a, b) for a, b in G.edges() if slot_of[a] == slot_of[b]]
    print("Vertices:", G.number_of_nodes())
    print("Edges:", G.number_of_edges())
    print("Colors (slots) used:", len(slots))
    print("Valid coloring:", "YES" if not bad else f"NO, bad edges: {bad}")

    pos = nx.spring_layout(G, seed=42, k=0.8, iterations=150)
    core = [n for n in G if G.nodes[n]["subject_type"] == "CORE"]
    elec = [n for n in G if G.nodes[n]["subject_type"] == "OPEN_ELECTIVE"]

    fig, ax = plt.subplots(figsize=(18, 13))
    nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.25, width=0.7)
    nx.draw_networkx_nodes(
        G, pos, nodelist=core, ax=ax, node_shape="o", node_size=800,
        node_color=[color_of_slot[slot_of[n]] for n in core],
        edgecolors="#333333", linewidths=1.1,
    )
    nx.draw_networkx_nodes(
        G, pos, nodelist=elec, ax=ax, node_shape="s", node_size=950,
        node_color=[color_of_slot[slot_of[n]] for n in elec],
        edgecolors="#333333", linewidths=1.1,
    )
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_color="#1B1B1B")

    slot_handles = [
        Patch(facecolor=color_of_slot[s], edgecolor="#333333",
              label=f"Slot {s}: {slot_info[s]['date']} {slot_info[s]['session']}")
        for s in slots
    ]
    shape_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
               markeredgecolor="#333333", markersize=11, label="Core subject"),
        Line2D([0], [0], marker="s", color="w", markerfacecolor="white",
               markeredgecolor="#333333", markersize=11, label="Open elective"),
    ]
    ax.legend(handles=slot_handles + shape_handles, loc="upper left",
              bbox_to_anchor=(1.01, 1), fontsize=8, title="Color = exam slot")

    ax.set_title(f"Colored Exam Conflict Graph ({len(slots)} colors = {len(slots)} time slots)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "colored_conflict_graph.png", dpi=300, bbox_inches="tight")
    plt.show()
    print("Saved:", (OUTPUT_DIR / "colored_conflict_graph.png").resolve())


if __name__ == "__main__":
    main()
