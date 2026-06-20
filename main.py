import os, sys, tkinter as tk
from tkinter import ttk, messagebox
import threading

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

import database as db
from models import UserProfile
from dashboard import (
    App as _BaseApp, DashboardScreen,
    BG, PANEL, CARD, ACCENT, ACCENT2, ACCENT3, TEXT, MUTED, BORDER, BTN_FG,
    FONT_BTN, FONT_SUB, FONT_LABEL, FONT_H2, FONT_SMALL, FONT_CARD_L, FONT_HERO,
    _frame, _label, _button, _entry, _section_header,
)
import charts, export, api_service


def _make_tree(parent, columns, widths, height=12):
    style = ttk.Style()
    style.configure("API.Treeview", background=CARD, foreground=TEXT,
                    fieldbackground=CARD, rowheight=26, font=FONT_SUB, borderwidth=0)
    style.configure("API.Treeview.Heading", background=PANEL, foreground=ACCENT,
                    font=FONT_BTN, relief="flat")
    style.map("API.Treeview", background=[("selected", BORDER)])
    frame = _frame(parent, bg=BG)
    frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
    tree = ttk.Treeview(frame, columns=columns, show="headings", style="API.Treeview", height=height)
    for col, w in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=w, anchor="center", minwidth=w)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return tree


def _status_bar(parent):
    lbl = _label(parent, text="", font=FONT_SMALL, fg=MUTED, bg=BG)
    lbl.pack(anchor="w", padx=14, pady=(0, 4))
    return lbl


class ApiSettingsDialog(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("API Key Settings")
        self.geometry("560x420")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._build()

    def _build(self):
        nav = _frame(self, bg=PANEL); nav.pack(fill="x")
        _label(nav, text="  API Key Settings", font=("Helvetica",12,"bold"), fg=ACCENT, bg=PANEL).pack(side="left", pady=10)
        tk.Button(nav, text="✕", command=self.destroy, bg=PANEL, fg=MUTED, relief="flat", cursor="hand2", font=FONT_BTN).pack(side="right", padx=12)

        keys = api_service.load_keys()
        info = _frame(self, bg=CARD); info.pack(fill="x", padx=20, pady=(16, 8))
        info.configure(highlightbackground=BORDER, highlightthickness=1)
        for line in ["• Open Food Facts — FREE, no key needed. Always active.",
                     "• Nutritionix — free at developer.nutritionix.com (500 calls/day)",
                     "• Spoonacular — free at spoonacular.com/food-api (150 calls/day)"]:
            _label(info, text=line, font=FONT_SMALL, fg=MUTED, bg=CARD, justify="left").pack(anchor="w", padx=12, pady=2)

        form = _frame(self, bg=BG); form.pack(padx=20, fill="x")
        def field(label, key_name, show=False):
            f = _frame(form, bg=BG); f.pack(fill="x", pady=6)
            _label(f, text=label, font=FONT_LABEL, fg=MUTED, bg=BG).pack(anchor="w")
            var = tk.StringVar(value=keys.get(key_name, ""))
            _entry(f, textvariable=var, width=58, show="•" if show else None).pack(fill="x")
            return var, key_name

        self._fields = [
            field("Nutritionix App ID",  "nutritionix_app_id"),
            field("Nutritionix App Key", "nutritionix_app_key", show=True),
            field("Spoonacular API Key", "spoonacular_key",     show=True),
        ]
        btn_row = _frame(self, bg=BG); btn_row.pack(pady=16)
        _button(btn_row, "Save Keys", self._save, width=16).pack(side="left", padx=8)
        _button(btn_row, "Cancel", self.destroy, bg=CARD, fg=MUTED, width=12).pack(side="left")

    def _save(self):
        keys = api_service.load_keys()
        for var, key_name in self._fields:
            keys[key_name] = var.get().strip()
        api_service.save_keys(keys)
        messagebox.showinfo("API Keys", "Keys saved successfully.")
        self.destroy()


class LiveFoodBrowser(tk.Toplevel):
    def __init__(self, master, dashboard: DashboardScreen):
        super().__init__(master)
        self.dashboard = dashboard
        self.title("Live Food Search")
        self.geometry("820x560")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._results = []; self._searching = False
        self._build()

    def _build(self):
        nav = _frame(self, bg=PANEL); nav.pack(fill="x")
        _label(nav, text="  🔍  Live Food Search", font=("Helvetica",12,"bold"), fg=ACCENT, bg=PANEL).pack(side="left", pady=8)
        tk.Button(nav, text="⚙  API Keys", command=lambda: ApiSettingsDialog(self), bg=PANEL, fg=MUTED, relief="flat", cursor="hand2", font=FONT_SMALL).pack(side="right", padx=4)
        tk.Button(nav, text="✕", command=self.destroy, bg=PANEL, fg=MUTED, relief="flat", cursor="hand2", font=FONT_BTN).pack(side="right", padx=8)

        badge_row = _frame(self, bg=BG); badge_row.pack(fill="x", padx=14, pady=(8, 0))
        _label(badge_row, text="Sources active:", font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")
        for src, color in [("Open Food Facts",ACCENT),("Nutritionix*",ACCENT3),("Spoonacular*","#5BC4F5")]:
            _label(badge_row, text=f"  ● {src}", font=FONT_SMALL, fg=color, bg=BG).pack(side="left")
        _label(badge_row, text="   * = requires free API key (⚙)", font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")

        sf = _frame(self, bg=BG); sf.pack(fill="x", padx=14, pady=(8, 4))
        self._search_var = tk.StringVar()
        e = _entry(sf, textvariable=self._search_var, width=44)
        e.pack(side="left", padx=(0, 8))
        e.bind("<Return>", lambda _: self._do_search())
        _button(sf, "Search", self._do_search, width=10).pack(side="left")
        self._btn_clear = _button(sf, "Clear", self._clear, bg=CARD, fg=MUTED, width=8)
        self._btn_clear.pack(side="left", padx=6)
        self._lbl_count = _label(sf, text="", font=FONT_SMALL, fg=MUTED, bg=BG)
        self._lbl_count.pack(side="right")

        self._status = _status_bar(self)
        cols   = ("Food","Brand / Source","kcal","Protein g","Carbs g","Fat g","Serving","Source")
        widths = [210, 120, 60, 75, 65, 60, 80, 100]
        self._tree = _make_tree(self, cols, widths, height=14)
        self._tree.bind("<Double-1>", lambda _: self._log_selected())
        self._tree.column("Source", width=0, minwidth=0, stretch=False)

        filter_row = _frame(self, bg=BG); filter_row.pack(fill="x", padx=14, pady=(0, 4))
        _label(filter_row, text="Filter:", font=FONT_SMALL, fg=MUTED, bg=BG).pack(side="left")
        self._filter_var = tk.StringVar(value="All")
        for src in ["All","Open Food Facts","Nutritionix","Spoonacular"]:
            tk.Radiobutton(filter_row, text=src, variable=self._filter_var, value=src,
                           command=self._apply_filter, bg=BG, fg=TEXT, selectcolor=CARD,
                           activebackground=BG, activeforeground=ACCENT, font=FONT_SMALL).pack(side="left", padx=6)

        btn_row = _frame(self, bg=BG); btn_row.pack(pady=(0, 10))
        _button(btn_row, "Log Selected →", self._log_selected, width=18).pack(side="left", padx=6)
        _button(btn_row, "Close", self.destroy, bg=CARD, fg=MUTED, width=10).pack(side="left")

    def _do_search(self):
        query = self._search_var.get().strip()
        if not query or self._searching: return
        self._searching = True; self._results = []
        self._tree.delete(*self._tree.get_children())
        self._status.config(text="⏳  Searching all sources…", fg=ACCENT3)
        self._lbl_count.config(text="")
        api_service.search_all_apis(query, callback=self._on_results,
                                    error_callback=self._on_error, max_per_source=15)

    def _on_results(self, items): self.after(0, self._render_results, items)

    def _on_error(self, msg):
        self.after(0, lambda: (self._status.config(text=f"⚠  {msg}", fg=ACCENT2),
                               self._lbl_count.config(text="0 results"),
                               setattr(self, '_searching', False)))

    def _render_results(self, items):
        self._results = items; self._searching = False
        self._apply_filter()
        self._status.config(text=f"✓  Found {len(items)} results.", fg=ACCENT)
        self._lbl_count.config(text=f"{len(items)} items")

    def _apply_filter(self):
        f = self._filter_var.get()
        self._tree.delete(*self._tree.get_children())
        shown = 0
        for r in self._results:
            if f != "All" and r.get("source", "") != f: continue
            self._tree.insert("", "end", values=(
                r.get("food_name",""), r.get("brand","") or r.get("source",""),
                r.get("calories",0), r.get("protein_g",0), r.get("carbs_g",0),
                r.get("fats_g",0), r.get("serving","100g"), r.get("source",""),
            ))
            shown += 1
        self._lbl_count.config(text=f"{shown} shown")

    def _clear(self):
        self._search_var.set(""); self._results = []
        self._tree.delete(*self._tree.get_children())
        self._status.config(text="", fg=MUTED); self._lbl_count.config(text="")

    def _log_selected(self):
        sel = self._tree.selection()
        if not sel: messagebox.showinfo("Food Search", "Select a food row first."); return
        food, _, cal, pro, carb, fat, _, _ = self._tree.item(sel[0], "values")
        mv = self.dashboard._meal_vars
        mv[0].set(food); mv[1].set(cal); mv[2].set(pro); mv[3].set(carb); mv[4].set(fat)
        self.destroy()


class ExerciseTracker(tk.Toplevel):
    def __init__(self, master, profile: UserProfile):
        super().__init__(master)
        self.profile = profile
        self.title("Exercise Calorie Tracker")
        self.geometry("660x500")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build()

    def _build(self):
        nav = _frame(self, bg=PANEL); nav.pack(fill="x")
        _label(nav, text="  🏃  Exercise Calorie Tracker", font=("Helvetica",12,"bold"), fg=ACCENT, bg=PANEL).pack(side="left", pady=8)
        tk.Button(nav, text="⚙  API Keys", command=lambda: ApiSettingsDialog(self), bg=PANEL, fg=MUTED, relief="flat", cursor="hand2", font=FONT_SMALL).pack(side="right", padx=4)
        tk.Button(nav, text="✕", command=self.destroy, bg=PANEL, fg=MUTED, relief="flat", cursor="hand2", font=FONT_BTN).pack(side="right", padx=8)

        info = _frame(self, bg=CARD); info.pack(fill="x", padx=14, pady=(12, 0))
        info.configure(highlightbackground=BORDER, highlightthickness=1)
        _label(info, text='Describe your workout — e.g. "ran 5km, 30 min cycling, 20 pushups"',
               font=FONT_SMALL, fg=MUTED, bg=CARD).pack(padx=12, pady=8)

        sf = _frame(self, bg=BG); sf.pack(fill="x", padx=14, pady=(10, 4))
        self._query_var = tk.StringVar()
        e = _entry(sf, textvariable=self._query_var, width=50)
        e.pack(side="left", padx=(0, 8))
        e.bind("<Return>", lambda _: self._search())
        _button(sf, "Calculate", self._search, width=12).pack(side="left")
        self._status = _status_bar(self)
        self._tree = _make_tree(self, ("Exercise","Duration (min)","Calories Burned"), [280,140,160], height=8)

        total_f = _frame(self, bg=CARD); total_f.pack(fill="x", padx=14, pady=4)
        total_f.configure(highlightbackground=BORDER, highlightthickness=1)
        self._lbl_total = _label(total_f, text="Total calories burned:  —", font=FONT_H2, fg=ACCENT3, bg=CARD)
        self._lbl_total.pack(pady=10)
        _label(self, text="Powered by Nutritionix API  (requires free key — ⚙ API Keys above)",
               font=FONT_SMALL, fg=MUTED, bg=BG).pack(pady=(0, 8))

    def _search(self):
        query = self._query_var.get().strip()
        if not query: return
        self._status.config(text="⏳  Calculating…", fg=ACCENT3)
        self._tree.delete(*self._tree.get_children())
        self._lbl_total.config(text="Total calories burned:  —")
        api_service.get_exercise_calories_async(
            query, weight_kg=self.profile.weight_kg, age=self.profile.age,
            gender=self.profile.gender, callback=self._on_results, error_callback=self._on_error)

    def _on_results(self, items): self.after(0, self._render, items)
    def _on_error(self, msg): self.after(0, lambda: self._status.config(text=f"⚠  {msg}", fg=ACCENT2))

    def _render(self, items):
        total = 0.0
        for ex in items:
            self._tree.insert("", "end", values=(ex["name"], ex["duration_min"], f"{ex['calories_burned']:.0f} kcal"))
            total += ex["calories_burned"]
        self._lbl_total.config(text=f"Total calories burned:  {total:.0f} kcal")
        self._status.config(text=f"✓  {len(items)} exercise(s) found.", fg=ACCENT)


class RecipeSuggestions(tk.Toplevel):
    def __init__(self, master, profile: UserProfile):
        super().__init__(master)
        self.profile = profile
        self.title("Recipe Suggestions")
        self.geometry("820x580")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build(); self._load()

    def _build(self):
        nav = _frame(self, bg=PANEL); nav.pack(fill="x")
        _label(nav, text="  🍳  Recipe Suggestions", font=("Helvetica",12,"bold"), fg=ACCENT, bg=PANEL).pack(side="left", pady=8)
        tk.Button(nav, text="⚙  API Keys", command=lambda: ApiSettingsDialog(self), bg=PANEL, fg=MUTED, relief="flat", cursor="hand2", font=FONT_SMALL).pack(side="right", padx=4)
        tk.Button(nav, text="✕", command=self.destroy, bg=PANEL, fg=MUTED, relief="flat", cursor="hand2", font=FONT_BTN).pack(side="right", padx=8)

        goal_labels = {"weight_loss":"Weight Loss 🥗","muscle_gain":"Muscle Gain 💪","maintenance":"Maintenance ⚖️"}
        g = goal_labels.get(self.profile.health_goal, self.profile.health_goal)
        info = _frame(self, bg=CARD); info.pack(fill="x", padx=14, pady=(10, 0))
        info.configure(highlightbackground=BORDER, highlightthickness=1)
        row = _frame(info, bg=CARD); row.pack(pady=8)
        _label(row, text="Recipes matched to your goal:  ", font=FONT_SUB, fg=MUTED, bg=CARD).pack(side="left")
        _label(row, text=g, font=("Helvetica",11,"bold"), fg=ACCENT3, bg=CARD).pack(side="left")
        _button(row, "🔄 Refresh", self._load, width=12, bg=PANEL, fg=MUTED).pack(side="right", padx=8)

        self._status = _status_bar(self)
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._cards_frame = _frame(canvas, bg=BG)
        iid = canvas.create_window((0, 0), window=self._cards_frame, anchor="nw")
        def _cfg(e): canvas.configure(scrollregion=canvas.bbox("all")); canvas.itemconfig(iid, width=canvas.winfo_width())
        self._cards_frame.bind("<Configure>", _cfg)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(iid, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        _label(self, text="Powered by Spoonacular API  (requires free key — ⚙ API Keys above)",
               font=FONT_SMALL, fg=MUTED, bg=BG).pack(pady=4)

    def _load(self):
        for w in self._cards_frame.winfo_children(): w.destroy()
        self._status.config(text="⏳  Loading recipes…", fg=ACCENT3)
        api_service.get_recipes_async(self.profile.health_goal,
                                      callback=self._on_results, error_callback=self._on_error)

    def _on_results(self, recipes): self.after(0, self._render, recipes)
    def _on_error(self, msg): self.after(0, lambda: self._status.config(text=f"⚠  {msg}", fg=ACCENT2))

    def _render(self, recipes):
        for w in self._cards_frame.winfo_children(): w.destroy()
        if not recipes:
            _label(self._cards_frame, text="No recipes found. Check your API key.", font=FONT_SUB, fg=ACCENT2, bg=BG).pack(pady=40)
            self._status.config(text="No results.", fg=ACCENT2); return
        self._status.config(text=f"✓  {len(recipes)} recipes loaded.", fg=ACCENT)
        for r in recipes:
            card = _frame(self._cards_frame, bg=CARD); card.pack(fill="x", padx=14, pady=5)
            card.configure(highlightbackground=BORDER, highlightthickness=1)
            top = _frame(card, bg=CARD); top.pack(fill="x", padx=12, pady=(10, 4))
            _label(top, text=r["title"], font=("Helvetica",11,"bold"), fg=TEXT, bg=CARD).pack(side="left")
            _label(top, text=f"⏱  {r['ready_in_minutes']} min", font=FONT_SMALL, fg=MUTED, bg=CARD).pack(side="right")
            macros = _frame(card, bg=CARD); macros.pack(fill="x", padx=12, pady=(0, 4))
            for val, lbl, color in [(f"{r['calories']:.0f} kcal","Calories",ACCENT),
                                     (f"{r['protein_g']:.0f}g","Protein",ACCENT3),
                                     (f"{r['carbs_g']:.0f}g","Carbs","#5BC4F5"),
                                     (f"{r['fats_g']:.0f}g","Fat",ACCENT2)]:
                m = _frame(macros, bg=CARD); m.pack(side="left", padx=(0, 20))
                _label(m, text=val, font=("Helvetica",12,"bold"), fg=color, bg=CARD).pack()
                _label(m, text=lbl, font=FONT_CARD_L, fg=MUTED, bg=CARD).pack()
            if r.get("url"):
                url = r["url"]
                link = tk.Label(card, text=f"🔗  View full recipe →  {url[:60]}…",
                                font=FONT_SMALL, fg=ACCENT3, bg=CARD, cursor="hand2")
                link.pack(anchor="w", padx=12, pady=(0, 8))
                link.bind("<Button-1>", lambda e, u=url: __import__("webbrowser").open(u))


class HealthTrackApp(_BaseApp):
    def __init__(self):
        self._toolbar_frame = None
        super().__init__()
        self.title("HealthTrack Pro")
        self.minsize(900, 750)

    def launch_dashboard(self, profile: UserProfile):
     if self._toolbar_frame and self._toolbar_frame.winfo_exists():
        self._toolbar_frame.destroy()
     self._toolbar_frame = self._build_toolbar (profile)
     super().launch_dashboard(profile)
     self._active_dashboard = self._current

    def show_auth(self):
        if self._toolbar_frame and self._toolbar_frame.winfo_exists():
            self._toolbar_frame.destroy(); self._toolbar_frame = None
        super().show_auth()

    def _build_toolbar(self, profile: UserProfile):
        bar = tk.Frame(self, bg=PANEL); bar.pack(side="top", fill="x")
        tk.Frame(bar, bg=BORDER, height=1).pack(fill="x")
        btn_row = _frame(bar, bg=PANEL); btn_row.pack(pady=6)

        def sep(): _label(btn_row, text=" │ ", fg=BORDER, bg=PANEL, font=FONT_H2).pack(side="left")
        def tb_btn(text, cmd, color=CARD):
            tk.Button(btn_row, text=text, command=cmd, bg=color,
                      fg=TEXT if color==CARD else BTN_FG, font=FONT_BTN,
                      relief="flat", cursor="hand2", padx=10, pady=4,
                      activebackground=ACCENT, activeforeground=BTN_FG).pack(side="left", padx=3)

        _label(btn_row, text="Charts:", fg=MUTED, bg=PANEL, font=FONT_LABEL).pack(side="left", padx=(14, 4))
        tb_btn("📊 Daily Cal",  lambda: charts.open_daily_calories(self, profile))
        tb_btn("📈 Weekly",     lambda: charts.open_weekly_trend(self, profile))
        tb_btn("🥧 Macros",     lambda: charts.open_macro_pie(self, profile))
        sep()
        _label(btn_row, text="Live:", fg=MUTED, bg=PANEL, font=FONT_LABEL).pack(side="left", padx=(4, 4))
        tb_btn("🔍 Food Search",  self._open_food_search)
        tb_btn("🏃 Exercise",     lambda: ExerciseTracker(self, profile))
        tb_btn("🍳 Recipes",      lambda: RecipeSuggestions(self, profile))
        sep()
        tb_btn("💾 Export CSV",   lambda: export.export_all(self, profile))
        tb_btn("⚙ API Keys",      lambda: ApiSettingsDialog(self), color=PANEL)
        return bar

    def _open_food_search(self):
        if hasattr(self, "_active_dashboard"):
            LiveFoodBrowser(self, self._active_dashboard)


def _check_dependencies():
    missing = [p for p in ("matplotlib","pandas") if not __import__("importlib").util.find_spec(p)]
    if missing:
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Missing Dependencies",
            "Packages not installed:\n\n" + "\n".join(f"  • {p}" for p in missing) +
            "\n\nRun:  pip install -r requirements.txt")
        root.destroy(); return False
    return True


if __name__ == "__main__":
    if not _check_dependencies(): sys.exit(1)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    api_service.load_keys()
    db.initialize_database()
    HealthTrackApp().mainloop()
