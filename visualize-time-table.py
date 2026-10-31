import textwrap
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

OUTPUT_DIR = Path("exam_scheduler_output")
TIMETABLE_CSV = OUTPUT_DIR / "exam_timetable.csv"

CORE_COLOR = "#BFD7EA"
ELECTIVE_COLOR = "#FFD6A5"
SESSION_COLORS = {"Morning": "#EAF2FB", "Afternoon": "#FFF3E3"}


def load():
    df = pd.read_csv(TIMETABLE_CSV)
    df["date_dt"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    return df


def plot_timetable_grid(df, path):
    """Calendar-style table: one row per date, one column per session."""
    sessions = list(dict.fromkeys(df.sort_values("slot")["session"]))
    dates = sorted(df["date_dt"].unique())

    def cell_text(day, session):
        sub = df[(df["date_dt"] == day) & (df["session"] == session)]
        if sub.empty:
            return "-"
        codes = [
            c + ("*" if t == "OPEN_ELECTIVE" else "")
            for c, t in zip(sub["subject_code"], sub["subject_type"])
        ]
        return textwrap.fill(", ".join(codes), width=38)

    rows = []
    for d in dates:
        label = pd.Timestamp(d).strftime("%d-%m-%Y\n%A")
        rows.append([label] + [cell_text(d, s) for s in sessions])

    time_by_session = df.drop_duplicates("session").set_index("session")["time"]
    headers = ["Date"] + [f"{s}\n({time_by_session[s]})" for s in sessions]

    row_lines = [max(c.count("\n") + 1 for c in r) for r in rows]
    fig_h = 1.2 + 0.32 * sum(row_lines) + 0.2 * len(rows)
    fig, ax = plt.subplots(figsize=(4 + 5 * len(sessions), fig_h))
    ax.axis("off")

    table = ax.table(
        cellText=rows, colLabels=headers, loc="center", cellLoc="center",
        colWidths=[0.16] + [0.84 / len(sessions)] * len(sessions),
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)

    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor("#7A7A7A")
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor("#3D5A80")
            cell.set_text_props(color="white", weight="bold")
            cell.set_height(0.08)
        else:
            cell.set_height(0.035 * row_lines[r - 1] + 0.03)
            if c == 0:
                cell.set_facecolor("#E6E6E6")
                cell.set_text_props(weight="bold")
            else:
                cell.set_facecolor(SESSION_COLORS.get(sessions[c - 1], "white"))

    ax.set_title("Final Exam Timetable  (* = open elective)", fontsize=13, pad=12)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close(fig)


def plot_slot_summary(df, path):
    """Bars per slot: subjects (core vs elective) and total students sitting."""
    slots = sorted(df["slot"].unique())
    counts = df.pivot_table(
        index="slot", columns="subject_type", values="subject_code",
        aggfunc="count", fill_value=0,
    ).reindex(slots, fill_value=0)
    students = df.groupby("slot")["students"].sum().reindex(slots)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(8, len(slots) * 0.9), 9), sharex=True)
    x = range(len(slots))

    core = counts["CORE"] if "CORE" in counts else pd.Series(0, index=slots)
    elec = counts["OPEN_ELECTIVE"] if "OPEN_ELECTIVE" in counts else pd.Series(0, index=slots)
    ax1.bar(x, core, color=CORE_COLOR, edgecolor="#3D5A80", label="Core")
    ax1.bar(x, elec, bottom=core, color=ELECTIVE_COLOR, edgecolor="#B5651D", label="Open elective")
    ax1.set_ylabel("Subjects in slot")
    ax1.set_title("Subjects per exam slot")
    ax1.legend()

    ax2.bar(x, students, color="#9DB4C0", edgecolor="#3D5A80")
    ax2.set_ylabel("Student enrollments in slot")
    ax2.set_title("Students sitting exams per slot")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(
        [f"Slot {s}\n{df[df.slot == s]['date'].iloc[0]}\n{df[df.slot == s]['session'].iloc[0]}"
         for s in slots], fontsize=7)

    for ax in (ax1, ax2):
        ax.grid(axis="y", alpha=0.3)
        ax.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close(fig)


def plot_day_load(df, path):
    """Total subjects per exam day, split by session."""
    per_day = df.pivot_table(
        index="date_dt", columns="session", values="subject_code",
        aggfunc="count", fill_value=0,
    ).sort_index()
    labels = [d.strftime("%d-%m\n%a") for d in per_day.index]

    fig, ax = plt.subplots(figsize=(max(7, len(per_day) * 1.1), 5))
    bottom = pd.Series(0, index=per_day.index)
    for session in per_day.columns:
        ax.bar(range(len(per_day)), per_day[session], bottom=bottom,
               color=SESSION_COLORS.get(session, "#DDD"), edgecolor="#555",
               label=session)
        bottom = bottom + per_day[session]

    ax.set_xticks(range(len(per_day)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Number of subjects")
    ax.set_title("Exam load per day")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close(fig)


def main():
    if not TIMETABLE_CSV.exists():
        raise FileNotFoundError(
            f"Cannot find {TIMETABLE_CSV}. Run the scheduler script first."
        )
    df = load()
    plot_timetable_grid(df, OUTPUT_DIR / "timetable_grid.png")
    plot_slot_summary(df, OUTPUT_DIR / "slot_summary.png")
    plot_day_load(df, OUTPUT_DIR / "day_load.png")
    print("Saved to", OUTPUT_DIR.resolve())
    print(" - timetable_grid.png\n - slot_summary.png\n - day_load.png")


if __name__ == "__main__":
    main()
