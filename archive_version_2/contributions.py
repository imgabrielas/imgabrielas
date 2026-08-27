"""
Generate a GitHub-README-friendly contribution plot from contributions.csv.

Reads daily contribution counts, plots:
  - one point per day, colored by GitHub-style intensity level (shades of blue)
  - a solid blue line connecting the daily points
  - a dashed purple step-line for the weekly total (right-hand axis)
  - a dotted grey horizontal line for the overall daily average

Output is a transparent PNG that reads on both light and dark GitHub themes.

Usage:
    python contributions.py
    python contributions.py --csv contributions.csv --out contribution_graph.png
"""

import argparse
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

# Blue ramp for contribution levels, low -> high (single hue, varying lightness
# so it stays a "sequential" read, same idea as GitHub's own graph).
LEVEL_COLORS = {
    0: "#8b93a1",  # no contributions - neutral grey, reads on light & dark bg
    1: "#8fc4ee",  # 1-3
    2: "#4a97dc",  # 4-7
    3: "#1c72c4",  # 8-10
    4: "#0f4f8f",  # 11-14
}
LEVEL_LABELS = ["0", "1-3", "4-7", "8-10", "11-14"]

DAILY_LINE_COLOR = "#4a97dc"      # solid line connecting daily points
WEEKLY_LINE_COLOR = "#8957e5"     # dashed step line, weekly total
AVERAGE_LINE_COLOR = "#9aa4ae"    # dotted horizontal reference line
GRID_AXIS_COLOR = "#9aa4ae"       # light grey axis/grid/spines

POINT_SIZE = 70


def level_for(n: int) -> int:
    if n <= 0:
        return 0
    if n <= 3:
        return 1
    if n <= 7:
        return 2
    if n <= 10:
        return 3
    return 4


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

def load_data(csv_path: str, year: int) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep=";")
    df["num_contributions"] = pd.to_numeric(df["num_contributions"], errors="coerce")
    df = df.dropna(subset=["num_contributions"]).copy()
    df["num_contributions"] = df["num_contributions"].astype(int)

    df["date"] = pd.to_datetime(
        df["date"] + f"-{year}", format="%d-%b-%Y"
    )
    df = df.sort_values("date").reset_index(drop=True)
    return df


def weekly_totals(df: pd.DataFrame) -> pd.DataFrame:
    weekly = (
        df.set_index("date")["num_contributions"]
        .resample("W-MON", label="left", closed="left")
        .sum()
        .reset_index()
        .rename(columns={"num_contributions": "weekly_total"})
    )
    weekly["week_end"] = weekly["date"] + pd.Timedelta(days=7)
    return weekly


# --------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------

def make_plot(df: pd.DataFrame, out_path: str) -> None:
    weekly = weekly_totals(df)
    average = df["num_contributions"].mean()
    colors = [LEVEL_COLORS[level_for(n)] for n in df["num_contributions"]]

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")

    # daily connecting line + points colored by level
    ax.plot(
        df["date"], df["num_contributions"],
        "-", color=DAILY_LINE_COLOR, linewidth=1.5, alpha=0.9, zorder=2,
    )
    ax.scatter(
        df["date"], df["num_contributions"],
        c=colors, s=POINT_SIZE, zorder=3, edgecolors="none",
    )

    # overall average, dotted reference line
    ax.axhline(
        average, color=AVERAGE_LINE_COLOR, linestyle=":", linewidth=1.5,
        zorder=1, label=f"Average ({average:.1f}/day)",
    )

    ax.set_ylabel("Contributions", color=GRID_AXIS_COLOR)
    ax.set_xlabel("")

    # weekly total, dashed step line on its own axis (very different scale)
    ax2 = ax.twinx()
    ax2.set_facecolor("none")
    for _, row in weekly.iterrows():
        ax2.plot(
            [row["date"], row["week_end"]], [row["weekly_total"]] * 2,
            "--", color=WEEKLY_LINE_COLOR, linewidth=1.5, zorder=2,
        )
    ax2.plot([], [], "--", color=WEEKLY_LINE_COLOR, label="Weekly total")
    ax2.set_ylabel("Weekly total", color=WEEKLY_LINE_COLOR)
    ax2.tick_params(axis="y", colors=WEEKLY_LINE_COLOR)
    for spine in ax2.spines.values():
        spine.set_visible(False)

    # axis styling - light grey, recessive
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    fig.autofmt_xdate(rotation=45)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color(GRID_AXIS_COLOR)
    ax.tick_params(colors=GRID_AXIS_COLOR)
    ax.grid(True, axis="y", color=GRID_AXIS_COLOR, alpha=0.25, linewidth=0.7)
    ax.set_axisbelow(True)

    # small level legend, GitHub-style "Less -> More", top right
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="", markersize=7,
                   markerfacecolor=LEVEL_COLORS[i], markeredgecolor="none")
        for i in range(5)
    ]
    level_legend = ax.legend(
        handles, LEVEL_LABELS, loc="upper right", frameon=False,
        labelcolor=GRID_AXIS_COLOR, fontsize=8, ncol=5,
        columnspacing=0.8, handletextpad=0.3, title="Contributions",
        title_fontsize=8, bbox_to_anchor=(1, 1),
    )
    level_legend.get_title().set_color(GRID_AXIS_COLOR)
    ax.add_artist(level_legend)

    # line legend (average / weekly total), directly under the level legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(
        lines1 + lines2, labels1 + labels2,
        loc="upper right", frameon=False, labelcolor=GRID_AXIS_COLOR,
        fontsize=9, bbox_to_anchor=(1, 0.93),
    )

    fig.tight_layout()
    fig.savefig(out_path, transparent=True, dpi=200, bbox_inches="tight")
    plt.close(fig)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="contributions.csv", help="Path to the contributions CSV file")
    parser.add_argument("--out", default="contribution_graph.png", help="Path to write the output PNG")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Year to assume for dates in the CSV")
    args = parser.parse_args()

    df = load_data(args.csv, args.year)
    make_plot(df, args.out)
    print(f"Wrote {args.out} ({len(df)} days plotted)")


if __name__ == "__main__":
    main()
