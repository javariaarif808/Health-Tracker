import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.patches as mpatches
import pandas as pd
import database as db
from models import UserProfile

BG="#0F1923"; PANEL="#162030"; CARD="#1E2D3D"; ACCENT="#00C896"
ACCENT2="#FF6B6B"; ACCENT3="#FFB347"; MUTED="#6B8299"; TEXT="#E8F0F7"; BORDER="#243447"

MPL_RC = {
    "figure.facecolor":BG,"axes.facecolor":PANEL,"axes.edgecolor":BORDER,
    "axes.labelcolor":MUTED,"axes.titlecolor":TEXT,"xtick.color":MUTED,
    "ytick.color":MUTED,"grid.color":BORDER,"grid.linestyle":"--","grid.alpha":0.6,
    "text.color":TEXT,"legend.facecolor":CARD,"legend.edgecolor":BORDER,"legend.labelcolor":TEXT,
}
def _rc():
    for k, v in MPL_RC.items(): matplotlib.rcParams[k] = v


class _ChartWindow(tk.Toplevel):
    WIDTH, HEIGHT = 820, 520

    def __init__(self, master, profile: UserProfile, title: str):
        super().__init__(master)
        self.profile = profile
        self.title(title)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.configure(bg=BG)
        self.resizable(True, True)
        _rc(); self._build()

    def _build(self):
        nav = tk.Frame(self, bg=PANEL); nav.pack(fill="x")
        tk.Label(nav, text=self.title(), font=("Helvetica",12,"bold"), fg=ACCENT, bg=PANEL).pack(side="left", padx=16, pady=8)
        tk.Button(nav, text="✕  Close", command=self.destroy, bg=PANEL, fg=MUTED, relief="flat", cursor="hand2").pack(side="right", padx=12)
        self.fig = Figure(figsize=(self.WIDTH/96, (self.HEIGHT-60)/96), dpi=96)
        self._draw()
        canvas = FigureCanvasTkAgg(self.fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0,12))
        tb = tk.Frame(self, bg=BG); tb.pack(fill="x")
        toolbar = NavigationToolbar2Tk(canvas, tb)
        toolbar.config(background=BG)
        toolbar._message_label.config(background=BG, foreground=MUTED)
        toolbar.update()

    def _draw(self): raise NotImplementedError


class DailyCaloriesChart(_ChartWindow):
    def __init__(self, master, profile): super().__init__(master, profile, "Daily Calories — Last 7 Days")

    def _draw(self):
        rows = db.get_daily_calorie_totals(self.profile.id, days=7)
        today = date.today()
        day_range = [(today - timedelta(days=6-i)) for i in range(7)]
        day_map = {r["day"]: r["total_calories"] for r in rows}
        labels = [d.strftime("%a\n%d %b") for d in day_range]
        values = [day_map.get(str(d), 0) for d in day_range]
        ax = self.fig.add_subplot(111)
        ax.set_title("Calories Consumed Per Day", fontsize=13, pad=14)
        ax.set_ylabel("Calories (kcal)", labelpad=10)
        x = range(len(labels))
        bars = ax.bar(x, values, color=ACCENT, width=0.55, zorder=3, edgecolor=BG, linewidth=0.8)
        if bars: bars[-1].set_color(ACCENT3)
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+8, f"{val:.0f}",
                        ha="center", va="bottom", fontsize=8, color=TEXT)
        target = self.profile.daily_calorie_target
        ax.axhline(y=target, color=ACCENT2, linewidth=1.5, linestyle="--", zorder=4)
        ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=8)
        ax.set_xlim(-0.6, len(labels)-0.4)
        ax.set_ylim(0, max(max(values, default=0), target)*1.2+100)
        ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
        handles = [mpatches.Patch(color=ACCENT2, label=f"Target: {target:.0f} kcal"),
                   mpatches.Patch(color=ACCENT3, label="Today")]
        ax.legend(handles=handles, fontsize=9)
        self.fig.tight_layout()


class WeeklyTrendChart(_ChartWindow):
    WIDTH, HEIGHT = 860, 540
    def __init__(self, master, profile): super().__init__(master, profile, "Weekly Calorie Trend — Last 14 Days")

    def _draw(self):
        rows = db.get_daily_calorie_totals(self.profile.id, days=14)
        today = date.today()
        day_range = [(today - timedelta(days=13-i)) for i in range(14)]
        day_map = {r["day"]: r["total_calories"] for r in rows}
        labels = [d.strftime("%d %b") for d in day_range]
        values = [day_map.get(str(d), 0) for d in day_range]
        df = pd.DataFrame({"day": labels, "calories": values})
        df["rolling"] = df["calories"].rolling(window=3, min_periods=1).mean()
        ax = self.fig.add_subplot(111)
        ax.set_title("14-Day Calorie Trend", fontsize=13, pad=14)
        ax.set_ylabel("Calories (kcal)", labelpad=10)
        x = list(range(len(labels)))
        ax.bar(x, df["calories"], color=ACCENT, alpha=0.25, width=0.6, zorder=2)
        ax.plot(x, df["calories"].tolist(), color=ACCENT, linewidth=2, marker="o", markersize=5, zorder=4, label="Daily Total")
        ax.plot(x, df["rolling"].tolist(), color=ACCENT3, linewidth=2, linestyle="-.", zorder=5, label="3-Day Average")
        ax.fill_between(x, df["calories"].tolist(), alpha=0.08, color=ACCENT, zorder=1)
        target = self.profile.daily_calorie_target
        ax.axhline(y=target, color=ACCENT2, linewidth=1.5, linestyle="--", zorder=3, label=f"Target: {target:.0f} kcal")
        ax.set_xticks(x); ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.set_xlim(-0.6, len(labels)-0.4)
        ax.set_ylim(0, max(max(values, default=0), target)*1.25+100)
        ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True); ax.legend(fontsize=9)
        self.fig.tight_layout()


class MacroPieChart(_ChartWindow):
    WIDTH, HEIGHT = 860, 500
    def __init__(self, master, profile): super().__init__(master, profile, "Macro Distribution — Today vs Target")

    def _draw(self):
        macros = db.get_macro_totals_today(self.profile.id)
        actual = {"Protein": macros["protein_g"] or 0, "Carbs": macros["carbs_g"] or 0, "Fat": macros["fats_g"] or 0}
        tgt = self.profile.macro_targets
        target = {"Protein": tgt["protein_g"], "Carbs": tgt["carbs_g"], "Fat": tgt["fats_g"]}
        colors = [ACCENT, ACCENT3, ACCENT2]
        ax1, ax2 = self.fig.add_subplot(121), self.fig.add_subplot(122)

        def donut(ax, data, title):
            vals = list(data.values()); total = sum(vals)
            if total == 0:
                ax.pie([1], colors=[BORDER], startangle=90, wedgeprops=dict(width=0.45, edgecolor=BG, linewidth=2))
                ax.text(0, 0, "No data", ha="center", va="center", fontsize=10, color=MUTED)
            else:
                _, _, ats = ax.pie(vals, autopct=lambda p: f"{p:.0f}%" if p > 4 else "",
                                   colors=colors, startangle=90,
                                   wedgeprops=dict(width=0.48, edgecolor=BG, linewidth=2), pctdistance=0.75)
                for at in ats: at.set_fontsize(9); at.set_color(BG); at.set_fontweight("bold")
                ax.text(0, 0, f"{total:.0f}g\ntotal", ha="center", va="center",
                        fontsize=9, color=TEXT, fontweight="bold", linespacing=1.5)
            ax.set_title(title, fontsize=11, pad=14)

        donut(ax1, actual, "Today's Intake"); donut(ax2, target, "Daily Target")
        labels = list(actual.keys())
        self.fig.legend(
            handles=[mpatches.Patch(color=c, label=f"{l}  ({actual[l]:.0f}g / {target[l]:.0f}g target)")
                     for c, l in zip(colors, labels)],
            loc="lower center", ncol=3, fontsize=9, framealpha=0.0, bbox_to_anchor=(0.5, 0.01))
        self.fig.suptitle(f"Macros for {date.today().strftime('%d %b %Y')}", fontsize=12, color=TEXT, y=0.97)
        self.fig.tight_layout(rect=[0, 0.08, 1, 0.95])


def open_daily_calories(master, profile): DailyCaloriesChart(master, profile)
def open_weekly_trend(master, profile): WeeklyTrendChart(master, profile)
def open_macro_pie(master, profile): MacroPieChart(master, profile)
