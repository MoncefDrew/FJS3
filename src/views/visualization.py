from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def build_resource_tasks(
    schedule: List[Tuple[int, int, float, float]]
) -> Dict[int, List[Tuple[int, float, float]]]:
    resource_tasks: Dict[int, List[Tuple[int, float, float]]] = {}
    for resource, job, start, duration in schedule:
        if resource not in resource_tasks:
            resource_tasks[resource] = []
        resource_tasks[resource].append((job, start, duration))
    return resource_tasks


def build_gantt_figure(
    schedule: List[Tuple[int, int, float, float]],
    title: str = "Gantt Chart - Optimal Schedule",
    figsize: Tuple[float, float] | None = None,
) -> Figure:
    if not schedule:
        return Figure()

    resource_tasks = build_resource_tasks(schedule)

    y_labels: List[str] = []
    y_positions: Dict[str, float] = {}
    y_pos = 0.0
    resource_boundaries: List[float] = []

    for resource in sorted(resource_tasks.keys()):
        tasks = resource_tasks[resource]
        tasks.sort(key=lambda x: x[1])

        for job, start, duration in tasks:
            label = f"R{resource + 1} - J{job + 1}"
            y_labels.append(label)
            y_positions[label] = y_pos
            y_pos += 1.0

        resource_boundaries.append(y_pos - 0.5)
        y_pos += 0.8

    num_rows = max(len(y_labels), 1)
    if figsize is None:
        figsize = (14.0, max(6.0, num_rows * 0.6))

    fig = Figure(figsize=figsize)
    ax = fig.add_subplot(111)

    label_font = max(6, min(10, int(figsize[1] * 72 / num_rows / 2.2)))
    title_font = max(10, min(14, label_font + 3))
    axis_font = max(8, min(12, label_font + 1))
    bar_height = max(0.35, min(0.6, figsize[1] / num_rows * 0.55))

    colors = [
        "#3498db",
        "#e74c3c",
        "#2ecc71",
        "#f39c12",
        "#9b59b6",
        "#e67e22",
        "#1abc9c",
    ]

    for resource, job, start, duration in schedule:
        label = f"R{resource + 1} - J{job + 1}"
        y_position = y_positions[label]
        color = colors[job % len(colors)]

        ax.barh(
            y_position,
            duration,
            left=start,
            height=bar_height,
            color=color,
            edgecolor="black",
            linewidth=0.7,
            alpha=0.85,
        )

        ax.text(
            start + duration / 2,
            y_position,
            f"J{job + 1}",
            ha="center",
            va="center",
            fontweight="bold",
            color="white",
            fontsize=label_font,
        )

    for boundary in resource_boundaries[:-1]:
        ax.axhline(y=boundary, color="gray", linestyle="--", linewidth=2, alpha=0.5)

    y_tick_positions = [y_positions[label] for label in y_labels]
    ax.set_yticks(y_tick_positions)
    ax.set_yticklabels(y_labels, fontsize=label_font)
    ax.set_xlabel("Time", fontsize=axis_font, fontweight="bold")
    ax.set_ylabel("Resources (with Jobs)", fontsize=axis_font, fontweight="bold")
    ax.set_title(title, fontsize=title_font, fontweight="bold")
    ax.grid(axis="x", alpha=0.3, linestyle=":", linewidth=0.8)

    fig.tight_layout()
    return fig



def build_stats_figure(
    num_resources: int,
    resource_busy: Dict[int, float],
    resource_idle: Dict[int, float],
    title: str = "Resource Utilization",
) -> Figure:
    fig = Figure(figsize=(10, 4))
    ax = fig.add_subplot(111)

    resources = [f"R{r + 1}" for r in range(num_resources)]
    busy_times = [resource_busy.get(r, 0.0) for r in range(num_resources)]
    idle_times = [resource_idle.get(r, 0.0) for r in range(num_resources)]

    ax.bar(resources, busy_times, label="Busy Time", color="#3498db", edgecolor="black")
    ax.bar(resources, idle_times, bottom=busy_times, label="Idle Time", color="#ecf0f1", edgecolor="black")

    ax.set_ylabel("Time", fontsize=10, fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.legend()
    ax.grid(axis="y", alpha=0.3, linestyle=":", linewidth=0.8)

    fig.tight_layout()
    return fig

