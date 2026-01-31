from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from .geometry import (
    EPS,
    intersection_to_human,
    segment_intersection,
    NoIntersection,
    PointIntersection,
    SegmentIntersection,
)
from .models import Point, Segment


# ----------------------------
#  Pomocnicze narzędzia GUI
# ----------------------------

def _try_parse_float(text: str) -> tuple[bool, float]:
    """Bezpieczne parsowanie float z walidacją."""
    try:
        # Pozwalamy na spacje i przecinki (PL) jako separator dziesiętny.
        text = text.strip().replace(",", ".")
        if text == "":
            return False, 0.0
        return True, float(text)
    except ValueError:
        return False, 0.0


class Viewport:
    """Przekształcenia: świat <-> ekran (Canvas)."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height

        # Skala: px na jednostkę świata.
        self.scale = 40.0

        # Środek świata w środku ekranu.
        self.cx = 0.0
        self.cy = 0.0

    def world_to_screen(self, p: Point) -> tuple[float, float]:
        x = (p.x - self.cx) * self.scale + self.width / 2
        y = self.height / 2 - (p.y - self.cy) * self.scale
        return x, y

    def screen_to_world(self, x: float, y: float) -> Point:
        wx = (x - self.width / 2) / self.scale + self.cx
        wy = (self.height / 2 - y) / self.scale + self.cy
        return Point(wx, wy)

    def zoom_at(self, factor: float, sx: float, sy: float):
        before = self.screen_to_world(sx, sy)
        self.scale = max(5.0, min(400.0, self.scale * factor))
        after = self.screen_to_world(sx, sy)
        # Korygujemy przesunięcie tak, aby punkt pod kursorem pozostał w miejscu.
        self.cx += before.x - after.x
        self.cy += before.y - after.y

    def pan(self, dx_px: float, dy_px: float):
        self.cx -= dx_px / self.scale
        self.cy += dy_px / self.scale


class SegmentIntersectionApp(tk.Tk):
    """Główna aplikacja."""

    HANDLE_R = 7  # promień uchwytu punktu (px)

    def __init__(self):
        super().__init__()
        self.title("Przecięcie dwóch odcinków - Geometria Obliczeniowa")
        self.geometry("1100x700")
        self.minsize(980, 620)

        self._build_ui()

        # Domyślne odcinki w świecie
        self.p1 = Point(-4.0, -1.0)
        self.p2 = Point(4.0, 2.0)
        self.p3 = Point(-2.0, 3.0)
        self.p4 = Point(3.0, -2.0)

        self._active_handle: str | None = None
        self._pan_last: tuple[int, int] | None = None

        self._sync_entries_from_points()
        self._redraw()

    # ----------------------------
    #  Budowanie UI
    # ----------------------------

    def _build_ui(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Panel boczny
        side = ttk.Frame(self, padding=12)
        side.grid(row=0, column=0, sticky="nsw")
        side.columnconfigure(0, weight=1)

        title = ttk.Label(side, text="Zbiór punktów przecięcia\n dwóch odcinków", font=("Segoe UI", 14, "bold"))
        title.grid(row=0, column=0, sticky="w")

        ttk.Separator(side).grid(row=1, column=0, sticky="ew", pady=10)

        # Pola wejściowe
        form = ttk.Frame(side)
        form.grid(row=2, column=0, sticky="ew")
        for i in range(4):
            form.columnconfigure(i, weight=1)

        self.vars = {
            "x1": tk.StringVar(),
            "y1": tk.StringVar(),
            "x2": tk.StringVar(),
            "y2": tk.StringVar(),
            "x3": tk.StringVar(),
            "y3": tk.StringVar(),
            "x4": tk.StringVar(),
            "y4": tk.StringVar(),
        }

        def add_row(r, label, xvar, yvar):
            ttk.Label(form, text=label, font=("Segoe UI", 10, "bold")).grid(row=r, column=0, columnspan=4, sticky="w", pady=(6, 2))
            ttk.Label(form, text="x:").grid(row=r+1, column=0, sticky="e")
            ex = ttk.Entry(form, textvariable=self.vars[xvar], width=10)
            ex.grid(row=r+1, column=1, sticky="ew", padx=(2, 8))
            ttk.Label(form, text="y:").grid(row=r+1, column=2, sticky="e")
            ey = ttk.Entry(form, textvariable=self.vars[yvar], width=10)
            ey.grid(row=r+1, column=3, sticky="ew", padx=(2, 0))
            return ex, ey

        self.entries = []
        self.entries += list(add_row(0, "Odcinek 1 - punkt A", "x1", "y1"))
        self.entries += list(add_row(2, "Odcinek 1 - punkt B", "x2", "y2"))
        self.entries += list(add_row(4, "Odcinek 2 - punkt C", "x3", "y3"))
        self.entries += list(add_row(6, "Odcinek 2 - punkt D", "x4", "y4"))

        # Reakcja na zmiany w polach
        for v in self.vars.values():
            v.trace_add("write", lambda *_: self._on_entries_changed())

        ttk.Separator(side).grid(row=3, column=0, sticky="ew", pady=10)

        # Wynik
        ttk.Label(side, text="Wynik", font=("Segoe UI", 12, "bold")).grid(row=4, column=0, sticky="w")
        self.result_var = tk.StringVar(value="-")
        self.result_label = ttk.Label(side, textvariable=self.result_var, wraplength=320, justify="left")
        self.result_label.grid(row=5, column=0, sticky="w", pady=(4, 0))

        ttk.Separator(side).grid(row=6, column=0, sticky="ew", pady=10)

        # Przyciski
        btns = ttk.Frame(side)
        btns.grid(row=7, column=0, sticky="ew")
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)

        ttk.Button(btns, text="Reset", command=self._reset).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(btns, text="Przykład", command=self._example).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(side, text="Kopiuj wynik", command=self._copy_result).grid(row=8, column=0, sticky="ew", pady=(10, 0))

        hint = (
            "Sterowanie płótnem:\n"
            "- przeciągnij punkty A/B/C/D\n"
            "- zoom: kółko myszy\n"
            "- przesuwanie: środkowy przycisk / przeciąganie\n"
        )
        ttk.Label(side, text=hint, foreground="#555", justify="left").grid(row=9, column=0, sticky="w", pady=(12, 0))

        # Canvas / widok
        self.canvas = tk.Canvas(self, bg="#ffffff", highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="nsew")

        self.viewport = Viewport(800, 600)

        # Zdarzenia
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_left_down)
        self.canvas.bind("<B1-Motion>", self._on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_up)

        # Pan (środkowy)
        self.canvas.bind("<Button-2>", self._on_pan_down)
        self.canvas.bind("<B2-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-2>", self._on_pan_up)
        # Niektóre systemy używają Button-3 jako środkowy - zostawiamy alternatywę:
        self.canvas.bind("<Button-3>", self._on_pan_down)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_up)

        # Zoom: Windows/macOS/Linux różnie wysyłają zdarzenia
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)          # Windows/macOS
        self.canvas.bind("<Button-4>", lambda e: self._on_linux_wheel(1, e))
        self.canvas.bind("<Button-5>", lambda e: self._on_linux_wheel(-1, e))

    # ----------------------------
    #  Logika wejścia
    # ----------------------------

    def _sync_entries_from_points(self):
        self.vars["x1"].set(str(self.p1.x))
        self.vars["y1"].set(str(self.p1.y))
        self.vars["x2"].set(str(self.p2.x))
        self.vars["y2"].set(str(self.p2.y))
        self.vars["x3"].set(str(self.p3.x))
        self.vars["y3"].set(str(self.p3.y))
        self.vars["x4"].set(str(self.p4.x))
        self.vars["y4"].set(str(self.p4.y))

    def _on_entries_changed(self):
        ok, pts = self._read_points_from_entries()
        self._style_entries(ok)
        if ok:
            self.p1, self.p2, self.p3, self.p4 = pts
            self._redraw()

    def _read_points_from_entries(self) -> tuple[bool, tuple[Point, Point, Point, Point]]:
        vals = {}
        for k, var in self.vars.items():
            ok, v = _try_parse_float(var.get())
            if not ok:
                return False, (self.p1, self.p2, self.p3, self.p4)
            vals[k] = v
        return True, (
            Point(vals["x1"], vals["y1"]),
            Point(vals["x2"], vals["y2"]),
            Point(vals["x3"], vals["y3"]),
            Point(vals["x4"], vals["y4"]),
        )

    def _style_entries(self, ok: bool):
        # Prosta informacja wizualna: gdy błąd, ustawiamy czerwone tło.
        # Tk themed widgets nie mają bezpośrednio background na wszystkich platformach,
        # więc stosujemy prostą ramkę przy błędzie.
        style = ttk.Style()
        style.configure("Bad.TEntry", fieldbackground="#ffe6e6")
        for e in self.entries:
            e.configure(style=("TEntry" if ok else "Bad.TEntry"))

    # ----------------------------
    #  Obliczenia i rysowanie
    # ----------------------------

    def _compute_result(self):
        s1 = Segment(self.p1, self.p2)
        s2 = Segment(self.p3, self.p4)
        res = segment_intersection(s1, s2)
        self.result_var.set(intersection_to_human(res))
        return res

    def _redraw(self):
        self.canvas.delete("all")
        self._draw_grid()

        # Odcinki
        self._draw_segment(self.p1, self.p2, color="#1f77b4", width=3, label="1")
        self._draw_segment(self.p3, self.p4, color="#ff7f0e", width=3, label="2")

        # Uchwyty punktów (A,B,C,D)
        self._draw_handle(self.p1, "A", color="#1f77b4")
        self._draw_handle(self.p2, "B", color="#1f77b4")
        self._draw_handle(self.p3, "C", color="#ff7f0e")
        self._draw_handle(self.p4, "D", color="#ff7f0e")

        res = self._compute_result()
        self._draw_intersection(res)

    def _draw_grid(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 2 or h <= 2:
            return

        self.viewport.width = w
        self.viewport.height = h

        # Gęstość siatki w jednostkach świata
        step_world = 1.0
        # Dobieramy krok do skali
        px = step_world * self.viewport.scale
        if px < 25:
            step_world = 2.0
        if px < 14:
            step_world = 5.0
        if px < 9:
            step_world = 10.0

        # Zakres świata widoczny na ekranie
        left = self.viewport.screen_to_world(0, h / 2).x
        right = self.viewport.screen_to_world(w, h / 2).x
        bottom = self.viewport.screen_to_world(w / 2, h).y
        top = self.viewport.screen_to_world(w / 2, 0).y

        # Linie pionowe
        x = (int(left // step_world) - 1) * step_world
        while x <= right + step_world:
            sx1, sy1 = self.viewport.world_to_screen(Point(x, bottom))
            sx2, sy2 = self.viewport.world_to_screen(Point(x, top))
            is_axis = abs(x) <= EPS
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill="#d0d0d0" if not is_axis else "#aaaaaa")
            if is_axis:
                self.canvas.create_text(sx1 + 10, h / 2 + 10, text="0", fill="#777", font=("Segoe UI", 9))
            x += step_world

        # Linie poziome
        y = (int(bottom // step_world) - 1) * step_world
        while y <= top + step_world:
            sx1, sy1 = self.viewport.world_to_screen(Point(left, y))
            sx2, sy2 = self.viewport.world_to_screen(Point(right, y))
            is_axis = abs(y) <= EPS
            self.canvas.create_line(sx1, sy1, sx2, sy2, fill="#d0d0d0" if not is_axis else "#aaaaaa")
            y += step_world

    def _draw_segment(self, a: Point, b: Point, color: str, width: int, label: str):
        x1, y1 = self.viewport.world_to_screen(a)
        x2, y2 = self.viewport.world_to_screen(b)
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        # Mała etykieta odcinka
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        self.canvas.create_text(mx + 10, my - 10, text=f"odc. {label}", fill=color, font=("Segoe UI", 10, "bold"))

    def _draw_handle(self, p: Point, name: str, color: str):
        x, y = self.viewport.world_to_screen(p)
        r = self.HANDLE_R
        self.canvas.create_oval(x - r, y - r, x + r, y + r, outline=color, width=2, fill="#ffffff")
        self.canvas.create_text(x + 14, y - 14, text=name, fill=color, font=("Segoe UI", 11, "bold"))

    def _draw_intersection(self, res):
        if isinstance(res, NoIntersection):
            return

        if isinstance(res, PointIntersection):
            x, y = self.viewport.world_to_screen(res.p)
            r = 6
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="#2ca02c", outline="#2ca02c")
            self.canvas.create_text(x + 10, y + 10, text="P", fill="#2ca02c", font=("Segoe UI", 11, "bold"))
            return

        if isinstance(res, SegmentIntersection):
            a, b = res.s.a, res.s.b
            x1, y1 = self.viewport.world_to_screen(a)
            x2, y2 = self.viewport.world_to_screen(b)
            self.canvas.create_line(x1, y1, x2, y2, fill="#2ca02c", width=6)
            self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2 - 14, text="wspólny odcinek", fill="#2ca02c", font=("Segoe UI", 10, "bold"))

    # ----------------------------
    #  Obsługa myszy
    # ----------------------------

    def _nearest_handle(self, sx: float, sy: float) -> str | None:
        """Zwraca nazwę uchwytu (A/B/C/D) najbliższego kliknięciu."""
        handles = {
            "A": self.p1,
            "B": self.p2,
            "C": self.p3,
            "D": self.p4,
        }
        best = None
        best_d2 = float("inf")
        for name, p in handles.items():
            x, y = self.viewport.world_to_screen(p)
            d2 = (x - sx) ** 2 + (y - sy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best = name
        if best is not None and best_d2 <= (self.HANDLE_R + 6) ** 2:
            return best
        return None

    def _on_left_down(self, event):
        self._active_handle = self._nearest_handle(event.x, event.y)

    def _on_left_drag(self, event):
        if not self._active_handle:
            return
        p = self.viewport.screen_to_world(event.x, event.y)
        if self._active_handle == "A":
            self.p1 = p
        elif self._active_handle == "B":
            self.p2 = p
        elif self._active_handle == "C":
            self.p3 = p
        elif self._active_handle == "D":
            self.p4 = p

        # aktualizujemy pola bez wywoływania rekurencji
        self._sync_entries_from_points()
        self._redraw()

    def _on_left_up(self, _event):
        self._active_handle = None

    def _on_pan_down(self, event):
        self._pan_last = (event.x, event.y)

    def _on_pan_drag(self, event):
        if not self._pan_last:
            return
        lx, ly = self._pan_last
        dx, dy = event.x - lx, event.y - ly
        self.viewport.pan(dx, dy)
        self._pan_last = (event.x, event.y)
        self._redraw()

    def _on_pan_up(self, _event):
        self._pan_last = None

    def _on_mousewheel(self, event):
        # event.delta: 120/-120 na Windows, inne na macOS
        factor = 1.0 + (0.12 if event.delta > 0 else -0.12)
        self.viewport.zoom_at(factor, event.x, event.y)
        self._redraw()

    def _on_linux_wheel(self, direction: int, event):
        factor = 1.0 + (0.12 if direction > 0 else -0.12)
        self.viewport.zoom_at(factor, event.x, event.y)
        self._redraw()

    def _on_resize(self, event):
        self.viewport.width = event.width
        self.viewport.height = event.height
        self._redraw()

    # ----------------------------
    #  Przyciski
    # ----------------------------

    def _reset(self):
        self.p1 = Point(-4.0, -1.0)
        self.p2 = Point(4.0, 2.0)
        self.p3 = Point(-2.0, 3.0)
        self.p4 = Point(3.0, -2.0)
        self.viewport.cx = 0.0
        self.viewport.cy = 0.0
        self.viewport.scale = 40.0
        self._sync_entries_from_points()
        self._redraw()

    def _example(self):
        # Przykład współliniowości i nakładania
        self.p1 = Point(-5.0, 0.0)
        self.p2 = Point(5.0, 0.0)
        self.p3 = Point(-2.0, 0.0)
        self.p4 = Point(8.0, 0.0)
        self._sync_entries_from_points()
        self._redraw()

    def _copy_result(self):
        txt = self.result_var.get()
        self.clipboard_clear()
        self.clipboard_append(txt)
        self.update()  # wymagane przez niektóre systemy
        messagebox.showinfo("Skopiowano", "Wynik został skopiowany do schowka.")


def main():
    # Start aplikacji
    app = SegmentIntersectionApp()
    app.mainloop()
