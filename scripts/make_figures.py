#!/usr/bin/env python3
"""Paper figure 1: hard-task gain per kind of added information, N32 and H35 side by side (same x axis).
Reads the same result files and contrasts as scripts/paper_stats.py. Writes paper/fig1-information.png.
    .venv-harness/bin/python scripts/make_figures.py"""
import os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from paper_stats import runs, SETS, boot

# (label, N32 contrast, H35 contrast); each contrast = (tag, treatment agent, control agent)
ROWS = [
    ("Exact location", ("oracle20261103", "agent_e18-o2", "agent_e18"), ("h3620261105", "agent_e18-o2", "agent_e18")),
    ("Failing-test names", ("dose20261105", "agent_e18-d1", "agent_e18"), None),
    ("Statement from issue (Claude)", ("d4520261106", "agent_e18-d4", "agent_e18"), ("h36d4520261106", "agent_e18-d4", "agent_e18")),
    ("Prediction list from issue (Gemma)", ("f1g20261109", "agent_e18-f1g", "agent_e18"), ("f1gh3620261109", "agent_e18-f1g", "agent_e18")),
    ("Prediction list from issue (Claude)", ("f120261109", "agent_e18-f1", "agent_e18"), ("f1h3620261109", "agent_e18-f1", "agent_e18")),
    ("Statement from tests (Gemma)", ("d3g20261107", "agent_e18-d3g", "agent_e18"), ("h36d3g20261108", "agent_e18-d3g", "agent_e18")),
    ("Statement from tests, no new names", ("dose20261106", "agent_e18-d3s", "agent_e18"), ("h36dose20261106", "agent_e18-d3s", "agent_e18")),
    ("Statement from tests (Claude)", ("dose20261105", "agent_e18-d3", "agent_e18"), ("h36dose20261106", "agent_e18-d3", "agent_e18")),
    ("Full test patch", ("oracle20261103", "agent_e18-o3", "agent_e18"), ("h3620261105", "agent_e18-o3", "agent_e18")),
]
BLUE, INK, MUTED, GRID, SURF = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def gain(c, sname):
    if not c:
        return None
    A, B = runs(c[0], c[1]), runs(c[0], c[2])
    ts = sorted(t for t in SETS[sname] if A.get(t) and B.get(t))
    if not ts:
        return None
    d = [st.mean(A[t]) - st.mean(B[t]) for t in ts]
    lo, hi = boot(d)
    return sum(d), lo, hi


fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True, facecolor=SURF)
for ax, sname, idx, title in ((axes[0], "N32", 1, "N32: 32 tasks the agent almost never solves"),
                              (axes[1], "H35", 2, "H36: 35 tasks chosen by features")):
    ax.set_facecolor(SURF)
    for y, row in enumerate(ROWS):
        g = gain(row[idx], sname)
        if g is None:
            ax.text(0.3, y, "not run", va="center", fontsize=8, color=MUTED)
            continue
        d, lo, hi = g
        ax.barh(y, d, height=0.55, color=BLUE, zorder=2)
        ax.plot([lo, hi], [y, y], color=INK, lw=1, zorder=3)
        ax.text(max(d, hi) + 0.4, y, f"{d:+.1f}", va="center", fontsize=8, color=INK)
    ax.axvline(0, color=MUTED, lw=0.8, zorder=1)
    ax.set_xlim(-4, 21)
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    ax.set_title(title, fontsize=9.5, color=INK, loc="left")
    ax.set_xlabel("Tasks solved per pass, minus control (95% CI)", fontsize=8.5, color=MUTED)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
axes[0].set_yticks(range(len(ROWS)), [r[0] for r in ROWS], fontsize=8.5, color=INK)
fig.suptitle("What the agent is missing on hard tasks is behavioral, and not in the issue", fontsize=11, color=INK, x=0.02, ha="left")
fig.text(0.02, 0.01, "Gemma 4 31B (4-bit), agent_e18, 28 tool calls. Within-task differences; task bootstrap CIs. Gold fix (not shown): +31 and +23.5.",
         fontsize=7.5, color=MUTED)
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paper/fig1-information.png")
fig.savefig(out, dpi=200, facecolor=SURF)
print("wrote", out)
