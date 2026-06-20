import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import database as db
from models import UserProfile, ACTIVITY_LABELS, HEALTH_GOAL_LABELS, ACTIVITY_MULTIPLIERS, HEALTH_GOALS
from diet_engine import DietEngine

# ── Palette ───────────────────────────────────────────────────────────────────
BG="#0F1923"; PANEL="#162030"; CARD="#1E2D3D"; ACCENT="#00C896"
ACCENT2="#FF6B6B"; ACCENT3="#FFB347"; TEXT="#E8F0F7"; MUTED="#6B8299"
BORDER="#243447"; BTN_FG="#0F1923"

FONT_TITLE=("Helvetica",22,"bold"); FONT_HERO=("Helvetica",32,"bold")
FONT_SUB=("Helvetica",11);         FONT_LABEL=("Helvetica",10)
FONT_CARD_V=("Helvetica",26,"bold"); FONT_CARD_L=("Helvetica",9)
FONT_BTN=("Helvetica",10,"bold");  FONT_H2=("Helvetica",13,"bold")
FONT_SMALL=("Helvetica",9)

# ── Widget helpers ────────────────────────────────────────────────────────────
def _frame(parent, bg=BG, **kw): return tk.Frame(parent, bg=bg, **kw)
def _label(parent, text="", font=FONT_SUB, fg=TEXT, bg=BG, **kw): return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)
def _section_header(parent, text): return _label(parent, text=text, font=FONT_H2, fg=ACCENT, bg=BG)

def _button(parent, text, command, bg=ACCENT, fg=BTN_FG, width=18, **kw):
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, font=FONT_BTN,
                     relief="flat", cursor="hand2", activebackground=ACCENT,
                     activeforeground=BTN_FG, padx=12, pady=6, width=width, **kw)

def _entry(parent, textvariable=None, show=None, width=28):
    kw = dict(textvariable=textvariable, bg=CARD, fg=TEXT, insertbackground=TEXT,
              relief="flat", font=FONT_SUB, highlightbackground=BORDER, highlightthickness=1, width=width)
    if show: kw["show"] = show
    return tk.Entry(parent, **kw)

def _combo(parent, textvariable, values, width=26):
    s = ttk.Style(); s.theme_use("clam")
    s.configure("Dark.TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT,
                selectbackground=CARD, selectforeground=TEXT, bordercolor=BORDER, arrowcolor=ACCENT)
    return ttk.Combobox(parent, textvariable=textvariable, values=values,
                        state="readonly", width=width, style="Dark.TCombobox", font=FONT_SUB)

def _metric_card(parent, label, value, unit="", accent=ACCENT):
    card = _frame(parent, bg=CARD, padx=16, pady=12)
    card.configure(highlightbackground=BORDER, highlightthickness=1)
    _label(card, text=label.upper(), font=FONT_CARD_L, fg=MUTED, bg=CARD).pack()
    _label(card, text=value, font=FONT_CARD_V, fg=accent, bg=CARD).pack()
    if unit: _label(card, text=unit, font=FONT_CARD_L, fg=MUTED, bg=CARD).pack()
    return card

def _scrollable_canvas(parent):
    canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
    sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = _frame(canvas, bg=BG)
    iid = canvas.create_window((0, 0), window=inner, anchor="nw")
    def _cfg(e): canvas.configure(scrollregion=canvas.bbox("all")); canvas.itemconfig(iid, width=canvas.winfo_width())
    inner.bind("<Configure>", _cfg)
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(iid, width=e.width))
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    return inner


# ── Auth Screen ───────────────────────────────────────────────────────────────
class AuthScreen(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=BG)
        self.master = master
        self._build()

    def _build(self):
        top = _frame(self, bg=BG); top.pack(pady=(48, 8))
        _label(top, text="HealthTrack", font=FONT_HERO, fg=ACCENT, bg=BG).pack()
        _label(top, text="PRO", font=("Helvetica",14,"bold"), fg=ACCENT3, bg=BG).pack()
        _label(top, text="Your personal health companion", font=FONT_SMALL, fg=MUTED, bg=BG).pack(pady=(2,0))

        tab_row = _frame(self, bg=BG); tab_row.pack(pady=(24, 0))
        self._btn_login = tk.Button(tab_row, text="Log In", font=FONT_BTN,
            command=lambda: self._switch("login"), bg=ACCENT, fg=BTN_FG, relief="flat", padx=24, pady=6, cursor="hand2")
        self._btn_login.grid(row=0, column=0, padx=(0, 2))
        self._btn_reg = tk.Button(tab_row, text="Register", font=FONT_BTN,
            command=lambda: self._switch("register"), bg=CARD, fg=MUTED, relief="flat", padx=24, pady=6, cursor="hand2")
        self._btn_reg.grid(row=0, column=1)

        self._form_host = _frame(self, bg=BG)
        self._form_host.pack(pady=12, padx=40)
        self._build_login_form()

    def _clear_form(self):
        for w in self._form_host.winfo_children(): w.destroy()

    def _switch(self, mode):
        active, inactive = dict(bg=ACCENT, fg=BTN_FG), dict(bg=CARD, fg=MUTED)
        if mode == "login":
            self._btn_login.config(**active); self._btn_reg.config(**inactive)
            self._clear_form(); self._build_login_form()
        else:
            self._btn_reg.config(**active); self._btn_login.config(**inactive)
            self._clear_form(); self._build_register_form()

    def _field_row(self, parent, label):
        row = _frame(parent, bg=BG); row.pack(fill="x", pady=4)
        _label(row, text=label, font=FONT_LABEL, fg=MUTED, bg=BG).pack(anchor="w")
        var = tk.StringVar()
        _entry(row, textvariable=var).pack(fill="x")
        return var

    def _build_login_form(self):
        host = self._form_host
        _label(host, text="Welcome back", font=FONT_H2, fg=TEXT, bg=BG).pack(pady=(8, 16))
        self._login_name = self._field_row(host, "Your name")
        _button(host, "Log In", self._do_login, width=32).pack(pady=(16, 4))
        _label(host, text="Don't have an account? Switch to Register above.", font=FONT_SMALL, fg=MUTED, bg=BG).pack()

    def _build_register_form(self):
        host = self._form_host
        canvas = tk.Canvas(host, bg=BG, highlightthickness=0, width=380, height=460)
        sb = ttk.Scrollbar(host, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        inner = _frame(canvas, bg=BG)
        iid = canvas.create_window((0, 0), window=inner, anchor="nw")
        def _cfg(e): canvas.configure(scrollregion=canvas.bbox("all")); canvas.itemconfig(iid, width=canvas.winfo_width())
        inner.bind("<Configure>", _cfg)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(iid, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        def row(label):
            f = _frame(inner, bg=BG); f.pack(fill="x", pady=4)
            _label(f, text=label, font=FONT_LABEL, fg=MUTED, bg=BG).pack(anchor="w")
            var = tk.StringVar()
            _entry(f, textvariable=var, width=42).pack(fill="x")
            return var

        def combo_row(label, opts):
            f = _frame(inner, bg=BG); f.pack(fill="x", pady=4)
            _label(f, text=label, font=FONT_LABEL, fg=MUTED, bg=BG).pack(anchor="w")
            var = tk.StringVar()
            _combo(f, var, list(opts.values()), width=40).pack(fill="x")
            return var, list(opts.keys())

        _label(inner, text="Create your account", font=FONT_H2, fg=TEXT, bg=BG).pack(pady=(8, 12))
        self._reg_name   = row("Full name")
        self._reg_age    = row("Age")
        self._reg_weight = row("Weight (kg)")
        self._reg_height = row("Height (cm)")

        gf = _frame(inner, bg=BG); gf.pack(fill="x", pady=4)
        _label(gf, text="Biological sex", font=FONT_LABEL, fg=MUTED, bg=BG).pack(anchor="w")
        self._reg_gender = tk.StringVar(value="male")
        gr = _frame(gf, bg=BG); gr.pack(anchor="w")
        for val, lbl in [("male","Male"),("female","Female")]:
            tk.Radiobutton(gr, text=lbl, variable=self._reg_gender, value=val, bg=BG, fg=TEXT,
                           selectcolor=CARD, activebackground=BG, activeforeground=ACCENT,
                           font=FONT_SUB).pack(side="left", padx=(0,12))

        self._reg_activity_var, self._reg_activity_keys = combo_row("Activity level", ACTIVITY_LABELS)
        self._reg_goal_var, self._reg_goal_keys = combo_row("Health goal", HEALTH_GOAL_LABELS)
        _button(inner, "Create Account", self._do_register, width=38).pack(pady=(16, 4))

    def _do_login(self):
        name = self._login_name.get().strip()
        if not name: messagebox.showerror("Login", "Please enter your name."); return
        row = db.get_user_by_name(name)
        if not row: messagebox.showerror("Login", f"No account found for '{name}'.\nPlease register first."); return
        self.master.launch_dashboard(UserProfile.from_db_row(row))

    def _do_register(self):
        errors = []
        name = self._reg_name.get().strip()
        if not name: errors.append("Name is required.")

        def _parse(getter, cast, lo, hi, err, fallback):
            try:
                v = cast(getter()); assert lo <= v <= hi; return v
            except Exception: errors.append(err); return fallback

        age    = _parse(self._reg_age.get,    int,   5,  120, "Age must be 5-120.",         0)
        weight = _parse(self._reg_weight.get, float, 20, 500, "Weight must be 20-500 kg.",  0)
        height = _parse(self._reg_height.get, float, 50, 280, "Height must be 50-280 cm.",  0)

        act_label  = self._reg_activity_var.get()
        goal_label = self._reg_goal_var.get()
        if not act_label:  errors.append("Please select an activity level.")
        if not goal_label: errors.append("Please select a health goal.")
        if errors: messagebox.showerror("Registration Error", "\n".join(errors)); return

        if db.get_user_by_name(name):
            messagebox.showerror("Registration", f"An account for '{name}' already exists."); return

        act_key  = self._reg_activity_keys[list(ACTIVITY_LABELS.values()).index(act_label)]
        goal_key = self._reg_goal_keys[list(HEALTH_GOAL_LABELS.values()).index(goal_label)]
        db.create_user(name, age, weight, height, self._reg_gender.get(), act_key, goal_key)
        profile = UserProfile.from_db_row(db.get_user_by_name(name))
        messagebox.showinfo("Welcome!", f"Account created! Welcome, {name} 🎉")
        self.master.launch_dashboard(profile)


# ── Dashboard Screen ──────────────────────────────────────────────────────────
class DashboardScreen(tk.Frame):
    def __init__(self, master, profile: UserProfile):
        super().__init__(master, bg=BG)
        self.master = master; self.profile = profile
        self.engine = DietEngine(profile); self._plan = None
        self._build(); self.refresh_metrics()

    def _build(self):
        self._build_navbar(); self._build_metric_cards(); self._build_notebook()

    def _build_navbar(self):
        nav = _frame(self, bg=PANEL); nav.pack(fill="x")
        _label(nav, text=" HealthTrack PRO", font=("Helvetica",14,"bold"), fg=ACCENT, bg=PANEL).pack(side="left", padx=16, pady=10)
        right = _frame(nav, bg=PANEL); right.pack(side="right", padx=16)
        _label(right, text=f"👤  {self.profile.name}", font=FONT_SUB, fg=TEXT, bg=PANEL).pack(side="left", padx=(0,20))
        _label(right, text=f"📅  {date.today().strftime('%d %b %Y')}", font=FONT_SUB, fg=MUTED, bg=PANEL).pack(side="left", padx=(0,20))
        _button(right, "Log Out", self._logout, bg=CARD, fg=MUTED, width=8).pack(side="left")

    def _build_metric_cards(self):
        bar = _frame(self, bg=BG); bar.pack(fill="x", padx=20, pady=(16,0))
        s = self.profile.summary()
        for i, (lbl, val, unit, color) in enumerate([
            ("BMI",          f"{s['bmi']}",                     s["bmi_category"], ACCENT),
            ("BMR",          f"{s['bmr']:.0f}",                 "kcal / day",      ACCENT3),
            ("Calorie Goal", f"{s['daily_calorie_target']:.0f}", "kcal / day",      ACCENT),
            ("Water Target", f"{s['daily_water_target_ml']:.0f}","ml / day",        "#5BC4F5"),
        ]):
            _metric_card(bar, lbl, val, unit, accent=color).grid(row=0, column=i, padx=8, pady=4, sticky="nsew")
            bar.columnconfigure(i, weight=1)

        today_bar = _frame(self, bg=BG); today_bar.pack(fill="x", padx=20, pady=6)
        self._lbl_cal_today   = _label(today_bar, font=FONT_SUB, fg=TEXT, bg=BG)
        self._lbl_cal_today.pack(side="left", padx=(8,32))
        self._lbl_water_today = _label(today_bar, font=FONT_SUB, fg=TEXT, bg=BG)
        self._lbl_water_today.pack(side="left")
        self._lbl_eval = _label(today_bar, font=FONT_SUB, fg=ACCENT, bg=BG)
        self._lbl_eval.pack(side="right", padx=8)

    def _build_notebook(self):
        s = ttk.Style()
        s.configure("Dark.TNotebook", background=BG, borderwidth=0, tabmargins=[4,4,0,0])
        s.configure("Dark.TNotebook.Tab", background=CARD, foreground=MUTED, padding=[14,6], font=FONT_BTN, borderwidth=0)
        s.map("Dark.TNotebook.Tab", background=[("selected",ACCENT)], foreground=[("selected",BTN_FG)])
        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill="both", expand=True, padx=20, pady=12)
        for tab, label in [(self._make_meals_tab(nb),"🍽  Meals"),
                           (self._make_water_tab(nb),"💧  Water"),
                           (self._make_diet_tab(nb),"🥗  Diet Plan"),
                           (self._make_profile_tab(nb),"👤  Profile")]:
            nb.add(tab, text=label)

    # ── Meals Tab ─────────────────────────────────────────────────────────────
    def _make_meals_tab(self, parent):
        tab = _frame(parent, bg=BG)
        form = _frame(tab, bg=CARD); form.pack(fill="x", padx=8, pady=8)
        form.configure(highlightbackground=BORDER, highlightthickness=1)
        _section_header(form, "Log a Meal").grid(row=0, column=0, columnspan=6, sticky="w", padx=12, pady=(10,6))
        self._meal_vars = []
        for col, (lbl, width) in enumerate([("Food Name",20),("Calories",8),("Protein (g)",8),("Carbs (g)",8),("Fat (g)",8)]):
            f = _frame(form, bg=CARD); f.grid(row=1, column=col, padx=8, pady=(0,10), sticky="w")
            _label(f, text=lbl, font=FONT_LABEL, fg=MUTED, bg=CARD).pack(anchor="w")
            var = tk.StringVar()
            _entry(f, textvariable=var, width=width).pack()
            self._meal_vars.append(var)
        _button(form, "Add Meal", self._log_meal, width=12).grid(row=1, column=5, padx=12, pady=(0,10), sticky="s")

        _section_header(tab, "Today's Meals").pack(anchor="w", padx=10, pady=(8,4))
        s = ttk.Style()
        s.configure("Dark.Treeview", background=CARD, foreground=TEXT, fieldbackground=CARD, rowheight=26, font=FONT_SUB, borderwidth=0)
        s.configure("Dark.Treeview.Heading", background=PANEL, foreground=ACCENT, font=FONT_BTN, relief="flat")
        s.map("Dark.Treeview", background=[("selected", BORDER)])
        tf = _frame(tab, bg=BG); tf.pack(fill="both", expand=True, padx=8, pady=(0,8))
        cols = ("Food","kcal","Protein","Carbs","Fat","Date")
        self._meal_tree = ttk.Treeview(tf, columns=cols, show="headings", style="Dark.Treeview", height=10)
        for col, w in zip(cols, [200,70,80,70,60,90]):
            self._meal_tree.heading(col, text=col); self._meal_tree.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self._meal_tree.yview)
        self._meal_tree.configure(yscrollcommand=sb.set)
        self._meal_tree.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        _button(tab, "Delete Selected", self._delete_meal, bg=ACCENT2, fg=TEXT, width=18).pack(pady=4)
        self._refresh_meal_table()
        return tab

    def _log_meal(self):
        name_v, cal_v, pro_v, carb_v, fat_v = self._meal_vars
        errors = []
        name = name_v.get().strip()
        if not name: errors.append("Food name is required.")
        def _num(v, label):
            try: x = float(v.get()); assert x >= 0; return x
            except Exception: errors.append(f"{label} must be a non-negative number."); return 0
        cal = _num(cal_v,"Calories"); pro = _num(pro_v,"Protein")
        carb = _num(carb_v,"Carbs"); fat = _num(fat_v,"Fat")
        if errors: messagebox.showerror("Meal Log", "\n".join(errors)); return
        db.log_meal(self.profile.id, name, cal, pro, carb, fat)
        for v in self._meal_vars: v.set("")
        self._refresh_meal_table(); self.refresh_metrics()

    def _refresh_meal_table(self):
        self._meal_tree.delete(*self._meal_tree.get_children())
        for meal in db.get_meals_for_user(self.profile.id, for_date=str(date.today())):
            self._meal_tree.insert("", "end", iid=meal["id"], values=(
                meal["food_name"], f"{meal['calories']:.0f}",
                f"{meal['protein_g']:.1f} g", f"{meal['carbs_g']:.1f} g",
                f"{meal['fats_g']:.1f} g", meal["logged_at"]))

    def _delete_meal(self):
        sel = self._meal_tree.selection()
        if not sel: messagebox.showinfo("Delete", "Select a meal row first."); return
        if messagebox.askyesno("Delete", "Delete the selected meal?"):
            db.delete_meal(int(sel[0])); self._refresh_meal_table(); self.refresh_metrics()

    # ── Water Tab ─────────────────────────────────────────────────────────────
    def _make_water_tab(self, parent):
        tab = _frame(parent, bg=BG)
        _section_header(tab, "Water Intake Tracker").pack(pady=(16,8))
        presets = _frame(tab, bg=BG); presets.pack()
        for ml in [150, 250, 350, 500]:
            _button(presets, f"+{ml} ml", lambda m=ml: self._log_water(m), width=10).pack(side="left", padx=6)
        custom = _frame(tab, bg=BG); custom.pack(pady=12)
        _label(custom, text="Custom amount (ml):", fg=MUTED, bg=BG).pack(side="left", padx=(0,8))
        self._water_custom = tk.StringVar()
        _entry(custom, textvariable=self._water_custom, width=10).pack(side="left")
        _button(custom, "Add", lambda: self._log_water(None), width=8).pack(side="left", padx=8)

        info = _frame(tab, bg=CARD); info.pack(padx=40, pady=16, fill="x")
        info.configure(highlightbackground=BORDER, highlightthickness=1)
        _label(info, text="Today's Progress", font=FONT_H2, fg=TEXT, bg=CARD).pack(pady=(12,4))
        self._lbl_water_amount = _label(info, text="— ml", font=FONT_HERO, fg="#5BC4F5", bg=CARD)
        self._lbl_water_amount.pack()
        self._lbl_water_target_disp = _label(info, text="", font=FONT_SUB, fg=MUTED, bg=CARD)
        self._lbl_water_target_disp.pack(pady=(0,4))
        s = ttk.Style(); s.configure("Water.Horizontal.TProgressbar", troughcolor=BORDER, background="#5BC4F5", thickness=14)
        self._water_progress = ttk.Progressbar(info, orient="horizontal", length=320, mode="determinate",
                                                maximum=100, style="Water.Horizontal.TProgressbar")
        self._water_progress.pack(pady=(4,16))
        self._refresh_water_display()
        return tab

    def _log_water(self, preset_ml):
        if preset_ml is None:
            try: preset_ml = float(self._water_custom.get()); assert preset_ml > 0
            except Exception: messagebox.showerror("Water", "Enter a valid positive amount in ml."); return
            self._water_custom.set("")
        db.log_water(self.profile.id, preset_ml)
        self._refresh_water_display(); self.refresh_metrics()

    def _refresh_water_display(self):
        total = db.get_water_today(self.profile.id)
        target = self.profile.daily_water_target_ml
        pct = min(100, (total/target*100) if target else 0)
        self._lbl_water_amount.config(text=f"{total:.0f} ml")
        self._lbl_water_target_disp.config(text=f"Target: {target:.0f} ml  ({pct:.0f}% reached)")
        self._water_progress["value"] = pct

    # ── Diet Plan Tab ─────────────────────────────────────────────────────────
    def _make_diet_tab(self, parent):
        tab = _frame(parent, bg=BG)
        top = _frame(tab, bg=BG); top.pack(fill="x", padx=16, pady=(12,0))
        _section_header(top, "Personalised Diet Plan").pack(side="left")
        _button(top, "🔄  Regenerate", self._regenerate_plan, width=16).pack(side="right")
        self._diet_inner = _scrollable_canvas(tab)
        self._render_diet_plan()
        return tab

    def _regenerate_plan(self):
        self._plan = None
        for w in self._diet_inner.winfo_children(): w.destroy()
        self._render_diet_plan()

    def _render_diet_plan(self):
        if self._plan is None: self._plan = self.engine.generate_meal_plan()
        plan = self._plan; inner = self._diet_inner
        SLOTS = {"breakfast":"☀️  Breakfast","lunch":"🌤  Lunch","dinner":"🌙  Dinner","snack":"🍎  Snack"}

        note_f = _frame(inner, bg=CARD); note_f.pack(fill="x", padx=12, pady=(12,4))
        note_f.configure(highlightbackground=BORDER, highlightthickness=1)
        _label(note_f, text=plan["notes"], font=FONT_SMALL, fg=TEXT, bg=CARD, wraplength=640, justify="left").pack(padx=12, pady=8)

        meals_f = _frame(inner, bg=BG); meals_f.pack(fill="x", padx=12, pady=4)
        for col, (slot, slot_label) in enumerate(SLOTS.items()):
            name, cal, pro, carb, fat = plan["meals"][slot]
            card = _frame(meals_f, bg=CARD)
            card.configure(highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
            meals_f.columnconfigure(col, weight=1)
            _label(card, text=slot_label, font=FONT_LABEL, fg=ACCENT3, bg=CARD).pack(pady=(8,2))
            _label(card, text=name, font=("Helvetica",10,"bold"), fg=TEXT, bg=CARD, wraplength=140, justify="center").pack(padx=6)
            _label(card, text=f"{cal} kcal", font=FONT_H2, fg=ACCENT, bg=CARD).pack(pady=4)
            for macro, val, unit in [("Protein",pro,"g"),("Carbs",carb,"g"),("Fat",fat,"g")]:
                _label(card, text=f"{macro}: {val}{unit}", font=FONT_SMALL, fg=MUTED, bg=CARD).pack()
            _label(card, text="", bg=CARD).pack(pady=4)

        t = plan["totals"]
        tot_f = _frame(inner, bg=PANEL); tot_f.pack(fill="x", padx=12, pady=6)
        tot_f.configure(highlightbackground=BORDER, highlightthickness=1)
        _label(tot_f, text="Plan Totals", font=FONT_H2, fg=TEXT, bg=PANEL).pack(pady=(8,4))
        row_f = _frame(tot_f, bg=PANEL); row_f.pack()
        for lbl, val in [("Calories",f"{t['calories']:.0f} kcal"),("Protein",f"{t['protein_g']:.0f} g"),
                          ("Carbs",f"{t['carbs_g']:.0f} g"),("Fat",f"{t['fats_g']:.0f} g")]:
            c = _frame(row_f, bg=PANEL); c.pack(side="left", padx=20, pady=8)
            _label(c, text=val, font=("Helvetica",16,"bold"), fg=ACCENT, bg=PANEL).pack()
            _label(c, text=lbl, font=FONT_CARD_L, fg=MUTED, bg=PANEL).pack()

        _section_header(inner, "Nutrition Tips").pack(anchor="w", padx=14, pady=(12,4))
        for tip in plan["tips"]:
            tf = _frame(inner, bg=CARD); tf.pack(fill="x", padx=12, pady=3)
            tf.configure(highlightbackground=BORDER, highlightthickness=1)
            _label(tf, text=f"  ›  {tip}", font=FONT_SMALL, fg=TEXT, bg=CARD, wraplength=680, justify="left").pack(anchor="w", padx=8, pady=6)

    # ── Profile Tab ───────────────────────────────────────────────────────────
    def _make_profile_tab(self, parent):
        tab = _frame(parent, bg=BG)
        _section_header(tab, "Your Profile").pack(pady=(16,12))
        form = _frame(tab, bg=CARD); form.pack(padx=40, pady=4, fill="x")
        form.configure(highlightbackground=BORDER, highlightthickness=1)

        def row(label, default, width=22):
            f = _frame(form, bg=CARD); f.pack(fill="x", padx=16, pady=5)
            _label(f, text=label, font=FONT_LABEL, fg=MUTED, bg=CARD, width=20, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            _entry(f, textvariable=var, width=width).pack(side="left")
            return var

        def combo_row(label, opts, current_key):
            f = _frame(form, bg=CARD); f.pack(fill="x", padx=16, pady=5)
            _label(f, text=label, font=FONT_LABEL, fg=MUTED, bg=CARD, width=20, anchor="w").pack(side="left")
            var = tk.StringVar(value=opts.get(current_key, ""))
            _combo(f, var, list(opts.values()), width=30).pack(side="left")
            return var

        p = self.profile
        self._prof_age      = row("Age",         str(p.age))
        self._prof_weight   = row("Weight (kg)", str(p.weight_kg))
        self._prof_height   = row("Height (cm)", str(p.height_cm))
        self._prof_activity = combo_row("Activity Level", ACTIVITY_LABELS, p.activity_level)
        self._prof_goal     = combo_row("Health Goal",    HEALTH_GOAL_LABELS, p.health_goal)
        _button(form, "Save Changes", self._save_profile, width=20).pack(pady=12)

        _section_header(tab, "Calculated Metrics").pack(pady=(16,8))
        self._prof_stats = _frame(tab, bg=CARD)
        self._prof_stats.pack(padx=40, fill="x")
        self._prof_stats.configure(highlightbackground=BORDER, highlightthickness=1)
        self._render_profile_stats()
        return tab

    def _render_profile_stats(self):
        for w in self._prof_stats.winfo_children(): w.destroy()
        s = self.profile.summary(); mt = self.profile.macro_targets
        for lbl, val in [("BMI", f"{s['bmi']}  ({s['bmi_category']})"),
                          ("BMR", f"{s['bmr']:.0f} kcal/day"),
                          ("TDEE", f"{s['tdee']:.0f} kcal/day"),
                          ("Calorie Goal", f"{s['daily_calorie_target']:.0f} kcal/day"),
                          ("Water Target", f"{s['daily_water_target_ml']:.0f} ml/day"),
                          ("Protein Target", f"{mt['protein_g']} g/day"),
                          ("Carbs Target", f"{mt['carbs_g']} g/day"),
                          ("Fat Target", f"{mt['fats_g']} g/day")]:
            rf = _frame(self._prof_stats, bg=CARD); rf.pack(fill="x", padx=16, pady=3)
            _label(rf, text=lbl, font=FONT_LABEL, fg=MUTED, bg=CARD, width=22, anchor="w").pack(side="left")
            _label(rf, text=val, font=FONT_SUB, fg=TEXT, bg=CARD).pack(side="left")
        _label(self._prof_stats, text="", bg=CARD).pack(pady=4)

    def _save_profile(self):
        errors = []
        def _parse(getter, cast, lo, hi, err, fallback):
            try: v = cast(getter()); assert lo <= v <= hi; return v
            except Exception: errors.append(err); return fallback
        age    = _parse(self._prof_age.get,    int,   5,  120, "Age must be 5-120.",        self.profile.age)
        weight = _parse(self._prof_weight.get, float, 20, 500, "Weight must be 20-500 kg.", self.profile.weight_kg)
        height = _parse(self._prof_height.get, float, 50, 280, "Height must be 50-280 cm.", self.profile.height_cm)
        if errors: messagebox.showerror("Profile", "\n".join(errors)); return

        act_label  = self._prof_activity.get()
        goal_label = self._prof_goal.get()
        act_key  = list(ACTIVITY_MULTIPLIERS.keys())[list(ACTIVITY_LABELS.values()).index(act_label)]
        goal_key = HEALTH_GOALS[list(HEALTH_GOAL_LABELS.values()).index(goal_label)]

        db.update_user(self.profile.id, weight, height, age, act_key, goal_key)
        self.profile.age = age; self.profile.weight_kg = weight; self.profile.height_cm = height
        self.profile.activity_level = act_key; self.profile.health_goal = goal_key
        self.engine = DietEngine(self.profile); self._plan = None
        self._render_profile_stats(); self.refresh_metrics()
        messagebox.showinfo("Profile", "Profile updated successfully.")

    def refresh_metrics(self):
        macros = db.get_macro_totals_today(self.profile.id)
        cal_today = macros["calories"] or 0.0
        water_today = db.get_water_today(self.profile.id)
        self._lbl_cal_today.config(text=f"🍽  Today: {cal_today:.0f} kcal consumed")
        self._lbl_water_today.config(text=f"💧  Today: {water_today:.0f} ml water")
        ev = self.engine.evaluate_day(cal_today, water_today)
        self._lbl_eval.config(text=f"Calories {ev['calorie_status']}   |   Water {ev['water_status']}")
        self._refresh_water_display()

    def _logout(self):
        if messagebox.askyesno("Log Out", "Return to the login screen?"): self.master.show_auth()


# ── Root App ──────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HealthTrack Pro")
        self.geometry("1000x560"); self.minsize(860, 500)
        self.configure(bg=BG)
        db.initialize_database()
        self._current = None; self.show_auth()

    def _swap(self, new_frame):
        if self._current: self._current.destroy()
        self._current = new_frame
        new_frame.pack(fill="both", expand=True)

    def show_auth(self): self._swap(AuthScreen(self))
    def launch_dashboard(self, profile): self._swap(DashboardScreen(self, profile))


if __name__ == "__main__":
    App().mainloop()
