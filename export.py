import os
from datetime import datetime
import pandas as pd
from tkinter import filedialog, messagebox
import database as db
from models import UserProfile


def _ts(): return datetime.now().strftime("%Y%m%d_%H%M%S")

def _ask_dir():
    f = filedialog.askdirectory(title="Choose export folder", mustexist=True)
    return f or None


def export_meals(profile: UserProfile, folder: str) -> str:
    rows = db.get_meals_for_user(profile.id)
    if not rows: return ""
    df = pd.DataFrame([dict(r) for r in rows],
                      columns=["id","user_id","food_name","calories","protein_g","carbs_g","fats_g","logged_at"])
    df.drop(columns=["user_id"], inplace=True)
    df.rename(columns={"id":"Meal ID","food_name":"Food","calories":"Calories (kcal)",
                        "protein_g":"Protein (g)","carbs_g":"Carbs (g)","fats_g":"Fat (g)","logged_at":"Date"}, inplace=True)
    for col in ["Calories (kcal)","Protein (g)","Carbs (g)","Fat (g)"]:
        df[col] = df[col].round(1)
    path = os.path.join(folder, f"meals_{profile.name}_{_ts()}.csv")
    df.to_csv(path, index=False)
    return path


def export_water(profile: UserProfile, folder: str) -> str:
    rows = db.get_all_data_for_export(profile.id)["water"]
    if not rows: return ""
    df = pd.DataFrame([dict(r) for r in rows], columns=["id","user_id","amount_ml","logged_at"])
    df.drop(columns=["user_id"], inplace=True)
    df.rename(columns={"id":"Entry ID","amount_ml":"Amount (ml)","logged_at":"Date"}, inplace=True)
    path = os.path.join(folder, f"water_{profile.name}_{_ts()}.csv")
    df.to_csv(path, index=False)
    return path


def export_daily_summary(profile: UserProfile, folder: str) -> str:
    meal_rows = db.get_meals_for_user(profile.id)
    water_rows = db.get_all_data_for_export(profile.id)["water"]

    if meal_rows:
        mdf = pd.DataFrame([dict(r) for r in meal_rows],
                           columns=["id","user_id","food_name","calories","protein_g","carbs_g","fats_g","logged_at"])
        daily = mdf.groupby("logged_at").agg(
            total_calories=("calories","sum"), total_protein=("protein_g","sum"),
            total_carbs=("carbs_g","sum"), total_fat=("fats_g","sum")).reset_index()
    else:
        daily = pd.DataFrame(columns=["logged_at","total_calories","total_protein","total_carbs","total_fat"])

    if water_rows:
        wdf = pd.DataFrame([dict(r) for r in water_rows], columns=["id","user_id","amount_ml","logged_at"])
        dw = wdf.groupby("logged_at").agg(total_water_ml=("amount_ml","sum")).reset_index()
    else:
        dw = pd.DataFrame(columns=["logged_at","total_water_ml"])

    summary = pd.merge(daily, dw, on="logged_at", how="outer").fillna(0).sort_values("logged_at")
    t = profile.daily_calorie_target
    summary["calorie_target"] = t
    summary["calories_vs_goal"] = (summary["total_calories"] - t).round(1)
    for c in ["total_calories","total_protein","total_carbs","total_fat","total_water_ml","calories_vs_goal"]:
        summary[c] = summary[c].round(1)
    summary.rename(columns={
        "logged_at":"Date","total_calories":"Total Calories (kcal)","total_protein":"Protein (g)",
        "total_carbs":"Carbs (g)","total_fat":"Fat (g)","total_water_ml":"Water (ml)",
        "calorie_target":"Calorie Target (kcal)","calories_vs_goal":"vs Target (kcal)"}, inplace=True)
    if summary.empty: return ""
    path = os.path.join(folder, f"daily_summary_{profile.name}_{_ts()}.csv")
    summary.to_csv(path, index=False)
    return path


def export_all(master_widget, profile: UserProfile) -> None:
    folder = _ask_dir()
    if not folder: return
    written, skipped = [], []
    for label, fn in [("Meal log", export_meals), ("Water intake", export_water), ("Daily summary", export_daily_summary)]:
        try:
            path = fn(profile, folder)
            if path: written.append(f"  ✓  {label}\n      {os.path.basename(path)}")
            else: skipped.append(f"  –  {label}  (no data)")
        except Exception as e:
            skipped.append(f"  ✗  {label}  (error: {e})")
    parts = []
    if written: parts.append("Exported to:\n  " + folder + "\n\n" + "\n\n".join(written))
    if skipped: parts.append("\nSkipped:\n" + "\n".join(skipped))
    if written: messagebox.showinfo("Export Complete", "\n".join(parts))
    else: messagebox.showwarning("Export", "No data to export.\n" + "\n".join(skipped))
