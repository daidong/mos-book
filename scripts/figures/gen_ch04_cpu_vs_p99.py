#!/usr/bin/env python3
"""
Generate the Chapter 4 opening figure: average CPU vs p99 latency
during the payment-service incident sketched in the chapter opener
and revisited in section 4.6.

The point of the figure is pedagogical, not empirical: it shows the
asymmetry that the chapter opens with. Average CPU rises from ~55%
to ~70% (well below any sane alarm threshold), while p99 latency
jumps from 8 ms to ~120 ms. This is the canonical "CPU utilization
is fine, but p99 is terrible" pattern that scheduling-latency
explains.

Numbers are synthetic but plausible. Seeded RNG; rerunning produces
the same figure bit-for-bit.

Output: src/part2-process-scheduling/ch04-processes-threads/figures/avg-cpu-vs-p99-incident.svg

Run from repo root:
    python3 scripts/figures/gen_ch04_cpu_vs_p99.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Palette — kept in sync with theme/css/academic.css :root variables.
# ---------------------------------------------------------------------------
NAVY = "#1f3a66"        # --mos-accent
OXBLOOD = "#6b3f1d"     # --mos-accent-2
INK = "#1a1a1a"         # --mos-ink
BODY = "#2a2a2a"        # --mos-body
MUTED = "#5a5a5a"       # --mos-muted (axis labels)
FAINT = "#8a8478"       # --mos-faint (annotation labels)
RULE = "#c7c2b3"        # --mos-rule (gridlines)


# ---------------------------------------------------------------------------
# Synthetic time series.
# ---------------------------------------------------------------------------
def synthesize() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (t_minutes, cpu_percent, p99_ms) for the incident."""
    rng = np.random.default_rng(seed=42)

    # 1-second resolution, from -10 min to +30 min around the incident.
    t = np.arange(-10 * 60, 30 * 60, 1) / 60.0  # minutes

    # CPU: ~55% baseline, jumps to ~70% at t=0 with 1/f-ish noise.
    baseline_cpu = 55.0 + 1.6 * rng.standard_normal(len(t))
    after_cpu = 70.0 + 2.0 * rng.standard_normal(len(t))
    # Smooth ramp over ~30 s so the transition is visible but not artificial.
    ramp = 1.0 / (1.0 + np.exp(-(t * 60 - 0) / 8.0))
    cpu = baseline_cpu * (1 - ramp) + after_cpu * ramp
    cpu = np.clip(cpu, 0, 100)

    # p99 latency: ~8 ms baseline, jumps to ~120 ms with heavy variance
    # because tail latency is noisy by definition.
    baseline_p99 = 8.0 + 1.2 * np.abs(rng.standard_normal(len(t)))
    # Use a log-normal-ish bump for the contended period.
    after_p99 = 110.0 * np.exp(0.18 * rng.standard_normal(len(t)))
    p99 = baseline_p99 * (1 - ramp) + after_p99 * ramp

    return t, cpu, p99


# ---------------------------------------------------------------------------
# Plot.
# ---------------------------------------------------------------------------
def render(out_path: Path) -> None:
    t, cpu, p99 = synthesize()

    plt.rcParams.update({
        "font.family": "serif",
        # Prefer Source Serif 4 (loaded by the site's Google Fonts) on the
        # web; fall back to whatever serif is available locally.
        "font.serif": [
            "Source Serif 4", "Source Serif Pro",
            "Charter", "Georgia", "DejaVu Serif", "serif",
        ],
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": BODY,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": RULE,
        "grid.linewidth": 0.6,
        "grid.linestyle": "-",
    })

    fig, (ax_cpu, ax_p99) = plt.subplots(
        2, 1, sharex=True,
        figsize=(10.0, 5.8),
        gridspec_kw={"height_ratios": [1.0, 1.0], "hspace": 0.22},
    )
    fig.patch.set_alpha(0.0)  # transparent: paper bg shows through

    # Faint card behind labels so they read clearly against gridlines
    # and noisy traces. Tinted to the chapter's paper tone (--mos-tint).
    label_bbox = dict(
        boxstyle="round,pad=0.25",
        facecolor="#f8f6ef",
        edgecolor="none",
        alpha=0.85,
    )

    # --- Top: CPU ----------------------------------------------------------
    ax_cpu.set_facecolor("none")
    ax_cpu.plot(t, cpu, color=NAVY, linewidth=1.4, alpha=0.95)
    ax_cpu.set_ylim(0, 100)
    ax_cpu.set_yticks([0, 25, 50, 75, 100])
    ax_cpu.set_ylabel("Average CPU (%)", color=NAVY)
    ax_cpu.tick_params(axis="y", colors=NAVY)
    ax_cpu.spines["left"].set_color(NAVY)
    ax_cpu.grid(True, axis="y", alpha=0.6)

    # Alarm threshold reference line.
    ax_cpu.axhline(80, color=FAINT, linewidth=0.8, linestyle=(0, (3, 3)))
    ax_cpu.text(
        29.5, 81.5, "alarm threshold (80%)",
        ha="right", va="bottom",
        color=FAINT, fontsize=10, fontstyle="italic",
    )

    # Highlight pre/post CPU plateau values.
    ax_cpu.text(
        -9.0, 45, "≈ 55%", color=NAVY, fontsize=11,
        ha="left", va="center", fontweight="bold",
        bbox=label_bbox,
    )
    ax_cpu.text(
        29.0, 60, "≈ 70%", color=NAVY, fontsize=11,
        ha="right", va="center", fontweight="bold",
        bbox=label_bbox,
    )

    # --- Bottom: p99 -------------------------------------------------------
    ax_p99.set_facecolor("none")
    ax_p99.plot(t, p99, color=OXBLOOD, linewidth=1.2, alpha=0.85)
    ax_p99.set_ylim(0, 220)
    ax_p99.set_yticks([0, 50, 100, 150, 200])
    ax_p99.set_ylabel("p99 latency (ms)", color=OXBLOOD)
    ax_p99.tick_params(axis="y", colors=OXBLOOD)
    ax_p99.spines["left"].set_color(OXBLOOD)
    ax_p99.grid(True, axis="y", alpha=0.6)

    # SLO line.
    ax_p99.axhline(50, color=FAINT, linewidth=0.8, linestyle=(0, (3, 3)))
    ax_p99.text(
        29.5, 53, "SLO p99 = 50 ms",
        ha="right", va="bottom",
        color=FAINT, fontsize=10, fontstyle="italic",
    )

    # Pre/post p99 plateau values.
    ax_p99.text(
        -9.0, 30, "≈ 8 ms", color=OXBLOOD, fontsize=11,
        ha="left", va="center", fontweight="bold",
        bbox=label_bbox,
    )
    ax_p99.text(
        29.0, 195, "≈ 120 ms (median of\nthe contended period)",
        color=OXBLOOD, fontsize=10.5,
        ha="right", va="top", fontweight="bold",
        bbox=label_bbox,
    )

    # --- Shared x-axis -----------------------------------------------------
    ax_p99.set_xlabel("Time relative to batch-job start (minutes)", color=BODY)
    ax_p99.set_xlim(-10, 30)
    ax_p99.set_xticks([-10, -5, 0, 5, 10, 15, 20, 25, 30])

    # Vertical line at t=0 across both panels.
    for ax in (ax_cpu, ax_p99):
        ax.axvline(0, color=INK, linewidth=0.9, alpha=0.55)

    # "Batch job starts" annotation, anchored to top axis only so it does
    # not duplicate.
    ax_cpu.text(
        0.6, 96, "log-compaction\nbatch starts (02:00)",
        color=INK, fontsize=10.5, ha="left", va="top",
        fontstyle="italic",
        bbox=label_bbox,
    )

    # Tighten the layout so the x-axis label has room.
    fig.subplots_adjust(left=0.085, right=0.985, top=0.97, bottom=0.10)

    # Save -----------------------------------------------------------------
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        out_path,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.18,
        transparent=True,
        metadata={"Date": None},  # avoid timestamping the SVG
    )
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent.parent
    out_path = (
        repo_root
        / "src/part2-process-scheduling/ch04-processes-threads/figures"
        / "avg-cpu-vs-p99-incident.svg"
    )
    render(out_path)


if __name__ == "__main__":
    main()
