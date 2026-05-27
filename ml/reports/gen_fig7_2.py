"""Generate Figure 7.2 — Lab vs field vs composited end-to-end accuracy bar chart."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUT = Path(__file__).resolve().parent / "lab_vs_field_accuracy.png"

# Data (all end-to-end accuracy, ctrl / deployed cascade)
labels = [
    "Lab\n(tomato20k, n=6,683)",
    "Field\n(PlantDoc test, n=79)",
    "Composited\n(lab-leaf + field-bg, n=165)",
    "Field-leaf +\nwhite-bg (Exp. 4, n=79)",
]
values = [97.19, 77.2, 65.5, 46.8]

# Colour encoding: green = good, amber = degraded, red = worst
colors = ["#2E7D32", "#F9A825", "#E65100", "#B71C1C"]

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(labels))
bars = ax.bar(x, values, color=colors, edgecolor="white", linewidth=0.8, width=0.55, zorder=3)

# Value labels on bars
for bar, val in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.9,
        f"{val:.1f}%",
        ha="center", va="bottom", fontsize=12, fontweight="bold", color="#333333"
    )

# Horizontal reference line at 90% (NFR-03 threshold)
ax.axhline(y=90, color="#555555", linestyle="--", linewidth=1.0, zorder=2)
ax.text(len(labels) - 0.08, 90.8, "NFR-03 target (90%)", ha="right", va="bottom",
        fontsize=8, color="#555555", style="italic")

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=9)
ax.set_ylabel("End-to-end accuracy (%)", fontsize=10)
ax.set_ylim(0, 105)
ax.set_xlim(-0.5, len(labels) - 0.5)
ax.yaxis.grid(True, linestyle=":", alpha=0.5, zorder=0)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(axis="x", length=0)

ax.set_title(
    "TomatoCare Cascade — End-to-end Accuracy Under Four Test Conditions\n"
    "(Deployed ctrl model; lab = tomato20k held-out; field = PlantDoc; composited = lab leaves on field backgrounds)",
    fontsize=9, pad=10, color="#333333"
)

plt.tight_layout()
fig.savefig(str(OUT), dpi=150, bbox_inches="tight")
print(f"[ok] wrote {OUT}  ({OUT.stat().st_size:,} bytes)")
