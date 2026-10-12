"""Script to generate Pareto Chart and Ishikawa Fishbone Diagram from recorded TQM data."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

BASE_DIR = Path(__file__).resolve().parent.parent
QUALITY_DIR = BASE_DIR / "quality"
CHECKSHEET_CSV = QUALITY_DIR / "checksheet.csv"
PARETO_PNG = QUALITY_DIR / "pareto_chart.png"
FISHBONE_PNG = QUALITY_DIR / "fishbone_diagram.png"


def generate_pareto_chart():
    """Generates a Pareto 80/20 analysis chart from recorded checksheet data."""
    categories = []
    counts = []

    with open(CHECKSHEET_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row["Defect_Category"]
            if cat.upper() != "TOTAL":
                categories.append(cat)
                counts.append(int(row["Total_Defects"]))

    # Sort descending
    combined = sorted(zip(categories, counts), key=lambda x: x[1], reverse=True)
    categories, counts = zip(*combined)

    total = sum(counts)
    cumulative_pct = []
    running_sum = 0
    for c in counts:
        running_sum += c
        cumulative_pct.append((running_sum / total) * 100)

    # Plot
    fig, ax1 = plt.subplots(figsize=(10, 5.5), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax1.set_facecolor("#f9fafb")

    # Bar chart for counts
    bars = ax1.bar(categories, counts, color="#4f46e5", width=0.5, edgecolor="#3730a3", zorder=3)
    ax1.set_ylabel("Defect Frequency (Count)", color="#111827", fontsize=11, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor="#111827")
    ax1.set_ylim(0, max(counts) + 2)
    plt.xticks(rotation=20, ha="right", fontsize=9, fontweight="bold")
    ax1.grid(axis="y", linestyle="--", alpha=0.3, zorder=0)

    for bar in bars:
        h = bar.get_height()
        ax1.annotate(
            f"{int(h)}",
            xy=(bar.get_x() + bar.get_width() / 2, h),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=9, fontweight="bold",
            color="#1f2937"
        )

    # Line chart for cumulative percentage on secondary axis
    ax2 = ax1.twinx()
    line = ax2.plot(categories, cumulative_pct, color="#dc2626", marker="o", linewidth=2.2, markersize=6, zorder=4)
    ax2.set_ylabel("Cumulative Percentage (%)", color="#dc2626", fontsize=11, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor="#dc2626")
    ax2.set_ylim(0, 105)

    # 80% Pareto threshold line
    ax2.axhline(80, color="#d97706", linestyle="--", linewidth=1.5, alpha=0.8, label="80% Cutoff Threshold")
    ax2.legend(loc="lower right")

    for i, pct in enumerate(cumulative_pct):
        ax2.annotate(
            f"{pct:.1f}%",
            xy=(i, pct),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=8, fontweight="bold",
            color="#991b1b"
        )

    plt.title(
        "Pareto Analysis of Software Defects — BBAT104 Restaurant Billing System\n"
        "(Sample Size: 14 Defects across 4 QA Phases | Quality Goal: Q08)",
        fontsize=12, fontweight="bold", pad=15
    )
    fig.tight_layout()
    fig.savefig(PARETO_PNG)
    plt.close(fig)
    print(f"Pareto chart successfully generated: {PARETO_PNG}")


def generate_fishbone_diagram():
    """Generates an Ishikawa (Cause-and-Effect) Fishbone diagram for checkout friction."""
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=150)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")
    ax.axis("off")

    # Spine (main horizontal arrow)
    ax.annotate(
        "",
        xy=(10.5, 5), xytext=(0.5, 5),
        arrowprops=dict(arrowstyle="->", lw=3.5, color="#1e293b")
    )

    # Problem Box (Effect)
    bbox_props = dict(boxstyle="square,pad=0.6", fc="#fee2e2", ec="#dc2626", lw=2)
    ax.text(
        10.6, 5,
        "PROBLEM STATEMENT:\nBilling Discrepancies &\nCashier Checkout Friction\n(Quality Goal Q08)",
        ha="left", va="center", fontsize=10, fontweight="bold", color="#991b1b",
        bbox=bbox_props
    )

    branches = [
        # (Top branches: x, label, sub_causes)
        (2.5, "PEOPLE", 7.8, [(2.0, 7.0, "Cashier fatigue"), (2.2, 6.2, "Typing errors"), (2.4, 5.5, "Incomplete training")]),
        (5.5, "PROCESS", 7.8, [(5.0, 7.0, "Manual price checks"), (5.2, 6.2, "Unverified discounts"), (5.4, 5.5, "Delayed order sync")]),
        (8.5, "DATA INTEGRITY", 7.8, [(8.0, 7.0, "Catalog price mutation"), (8.2, 6.2, "Orphaned order items"), (8.4, 5.5, "Unsalted credentials")]),

        # (Bottom branches: x, label, sub_causes)
        (2.5, "TECHNOLOGY", 2.2, [(2.0, 3.0, "IEEE 754 Float rounding"), (2.2, 3.8, "Missing DB transactions"), (2.4, 4.5, "SQLite FK disabled")]),
        (5.5, "INTERFACE (UI)", 2.2, [(5.0, 3.0, "Dark room eye strain"), (5.2, 3.8, "Mouse-only bottleneck"), (5.4, 4.5, "Raw error popups")]),
        (8.5, "ENVIRONMENT", 2.2, [(8.0, 3.0, "Peak rush hour noise"), (8.2, 3.8, "Dim dining ambient light"), (8.4, 4.5, "Multiple register queues")])
    ]

    for x_pos, cat_name, y_label, causes in branches:
        is_top = y_label > 5
        y_spine = 5.0
        y_end = y_label

        # Slanted rib
        ax.plot([x_pos - 1.2, x_pos], [y_end, y_spine], color="#2563eb", lw=2.2)

        # Branch label
        cat_box = dict(boxstyle="round,pad=0.4", fc="#dbeafe", ec="#2563eb", lw=1.5)
        ax.text(
            x_pos - 1.2, y_end + (0.3 if is_top else -0.3),
            cat_name,
            ha="center", va="center", fontsize=10, fontweight="bold", color="#1e40af",
            bbox=cat_box
        )

        # Horizontal bones for sub-causes
        for cx, cy, ctext in causes:
            ax.plot([cx, cx + 1.0], [cy, cy], color="#64748b", lw=1.2, linestyle="-")
            ax.text(
                cx + 0.1, cy + (0.15 if is_top else -0.15),
                ctext,
                ha="left", va="center", fontsize=8, color="#334155"
            )

    ax.set_xlim(0, 13)
    ax.set_ylim(1, 9)
    plt.title(
        "Ishikawa (Fishbone) Cause-and-Effect Analysis Diagram\n"
        "Root Cause Identification for Total Quality Management (BBAT104 — Reg: 2410302024)",
        fontsize=12, fontweight="bold", pad=10
    )
    fig.tight_layout()
    fig.savefig(FISHBONE_PNG)
    plt.close(fig)
    print(f"Fishbone diagram successfully generated: {FISHBONE_PNG}")


if __name__ == "__main__":
    generate_pareto_chart()
    generate_fishbone_diagram()
