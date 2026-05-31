
from __future__ import annotations

import base64
import io
import tkinter as tk
from typing import TYPE_CHECKING, Optional, Union

from ..visualization import build_gantt_figure

if TYPE_CHECKING:
    from ..gui import SchedulerGUI
    from .models import Scenario

# Claude Code–style log typography and colors
LOG_FONT_FAMILY = "JetBrains Mono"
LOG_FONT = (LOG_FONT_FAMILY, 12)
LOG_FONT_BOLD = (LOG_FONT_FAMILY, 12, "bold")
LOG_BG = "#1c1c1c"
LOG_FG = "#d4d4d4"

# Tag names used in the log Text widget
_HEADER_TAG = "header"
_PHASE_TAG = "phase"
_OK_TAG = "ok"
_WARN_TAG = "warn"
_ERR_TAG = "err"
_MONO_TAG = "mono"

_NATURAL_FIG_WIDTH = 14.0
_MIN_FIG_HEIGHT = 6.0
_ROW_HEIGHT_INCHES = 0.6
_ZOOM_STEP = 1.25
_MIN_ZOOM = 0.1
_MAX_ZOOM = 4.0


def configure_log_tags(text_widget: tk.Text) -> None:

    text_widget.tag_configure(_HEADER_TAG, foreground="#6ea8fe", font=LOG_FONT_BOLD)
    text_widget.tag_configure(_PHASE_TAG, foreground="#bc8cff", font=LOG_FONT_BOLD)
    text_widget.tag_configure(_OK_TAG, foreground="#3fb950", font=LOG_FONT)
    text_widget.tag_configure(_WARN_TAG, foreground="#d29922", font=LOG_FONT)
    text_widget.tag_configure(_ERR_TAG, foreground="#f85149", font=LOG_FONT)
    text_widget.tag_configure(_MONO_TAG, foreground="#8b949e", font=LOG_FONT)


def configure_log_widget(text_widget: tk.Text) -> None:

    text_widget.configure(
        font=LOG_FONT,
        bg=LOG_BG,
        fg=LOG_FG,
        insertbackground=LOG_FG,
        selectbackground="#404040",
        relief="flat",
        borderwidth=0,
    )
    configure_log_tags(text_widget)


def _pick_tag(line: str) -> Optional[str]:

    if line.startswith("SCENARIO ") or line.startswith("SCENARIO:"):
        return _HEADER_TAG
    if line.startswith("PHASE ") or line.startswith("Processing "):
        return _PHASE_TAG
    if "✓" in line:
        return _OK_TAG
    if "❌" in line:
        return _ERR_TAG
    if "Warning" in line:
        return _WARN_TAG
    if line.startswith("Resource") or line.startswith("-") or line.startswith("="):
        return _MONO_TAG
    return None


def render_logs(app: "SchedulerGUI", text: str) -> None:

    lines = text.splitlines()
    app.log_text.configure(state="normal")
    app.log_text.delete("1.0", tk.END)

    for line in lines:
        tag = _pick_tag(line)
        if tag:
            app.log_text.insert(tk.END, line + "\n", (tag,))
        else:
            app.log_text.insert(tk.END, line + "\n")

    app.log_text.see(tk.END)
    app.log_text.configure(state="disabled")


def _count_gantt_rows(schedule) -> int:
    return max(len(schedule), 1)


def _natural_figsize(num_rows: int) -> tuple[float, float]:
    return (_NATURAL_FIG_WIDTH, max(_MIN_FIG_HEIGHT, num_rows * _ROW_HEIGHT_INCHES))


def _figure_to_photo(fig) -> tk.PhotoImage:
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    buf = io.BytesIO()
    FigureCanvasAgg(fig).print_png(buf)
    buf.seek(0)
    return tk.PhotoImage(data=base64.b64encode(buf.getvalue()))


def _canvas_viewport(app: "SchedulerGUI") -> tuple[int, int]:
    app.diagram_canvas.update_idletasks()
    width = app.diagram_canvas.winfo_width()
    height = app.diagram_canvas.winfo_height()
    if width <= 1:
        width = 800
    if height <= 1:
        height = 420
    return width, height


def _resolve_zoom(app: "SchedulerGUI", num_rows: int) -> float:
    zoom = app._diagram_zoom
    if zoom != "fit":
        return float(zoom)

    viewport_w, viewport_h = _canvas_viewport(app)
    natural_w, natural_h = _natural_figsize(num_rows)
    dpi = 100.0
    return min(viewport_w / (natural_w * dpi), viewport_h / (natural_h * dpi))


def _zoom_label_text(zoom: Union[str, float]) -> str:
    if zoom == "fit":
        return "Fit"
    return f"{int(round(float(zoom) * 100))}%"


def _draw_diagram(app: "SchedulerGUI", scenario: "Scenario") -> None:
    schedule = scenario.schedule or []
    num_rows = _count_gantt_rows(schedule)
    zoom = _resolve_zoom(app, num_rows)
    natural_w, natural_h = _natural_figsize(num_rows)
    figsize = (natural_w * zoom, natural_h * zoom)

    fig = build_gantt_figure(
        schedule,
        title=f"{scenario.name} - Makespan={scenario.optimal_makespan}",
        figsize=figsize,
    )
    photo = _figure_to_photo(fig)
    app.diagram_image = photo

    canvas = app.diagram_canvas
    if app.diagram_canvas_item is not None:
        canvas.delete(app.diagram_canvas_item)

    app.diagram_canvas_item = canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas.configure(scrollregion=(0, 0, photo.width(), photo.height()))
    canvas.xview_moveto(0)
    canvas.yview_moveto(0)

    app.diagram_zoom_label.configure(text=_zoom_label_text(app._diagram_zoom))


def render_diagram(app: "SchedulerGUI", scenario: "Scenario") -> None:
    app._diagram_current_scenario = scenario
    app._diagram_zoom = "fit"
    app.after_idle(lambda: _draw_diagram(app, scenario))


def set_diagram_zoom(app: "SchedulerGUI", zoom: Union[str, float]) -> None:
    if app._diagram_current_scenario is None:
        return
    app._diagram_zoom = zoom
    _draw_diagram(app, app._diagram_current_scenario)


def zoom_diagram_in(app: "SchedulerGUI") -> None:
    if app._diagram_current_scenario is None:
        return
    current = _resolve_zoom(app, _count_gantt_rows(app._diagram_current_scenario.schedule or []))
    if app._diagram_zoom == "fit":
        current = min(1.0, current)
    else:
        current = float(app._diagram_zoom)
    app._diagram_zoom = min(_MAX_ZOOM, current * _ZOOM_STEP)
    _draw_diagram(app, app._diagram_current_scenario)


def zoom_diagram_out(app: "SchedulerGUI") -> None:
    if app._diagram_current_scenario is None:
        return
    current = _resolve_zoom(app, _count_gantt_rows(app._diagram_current_scenario.schedule or []))
    if app._diagram_zoom == "fit":
        current = min(1.0, current)
    else:
        current = float(app._diagram_zoom)
    app._diagram_zoom = max(_MIN_ZOOM, current / _ZOOM_STEP)
    _draw_diagram(app, app._diagram_current_scenario)


def on_diagram_canvas_configure(app: "SchedulerGUI", _event=None) -> None:
    if app._diagram_current_scenario is None or app._diagram_zoom != "fit":
        return

    after_id = getattr(app, "_diagram_configure_after", None)
    if after_id is not None:
        app.after_cancel(after_id)

    scenario = app._diagram_current_scenario
    app._diagram_configure_after = app.after(120, lambda: _draw_diagram(app, scenario))
