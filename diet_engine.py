import random
from models import UserProfile

_WL = {
    "breakfast": [("Oatmeal with Berries",320,10,55,6),("Greek Yogurt Parfait",280,18,32,6),
                  ("Veggie Egg White Omelette",220,22,8,8),("Whole-Grain Toast + Avocado",310,9,38,14)],
    "lunch":     [("Grilled Chicken Salad",380,42,18,12),("Lentil Vegetable Soup",310,18,48,4),
                  ("Tuna Lettuce Wraps",290,35,14,8),("Quinoa & Roasted Veggie Bowl",400,16,60,10)],
    "dinner":    [("Baked Salmon + Steamed Broccoli",420,45,12,20),("Turkey Stir-Fry with Zucchini",370,38,22,12),
                  ("Chicken & Sweet Potato",410,40,38,10),("Shrimp & Cauliflower Rice",330,36,20,10)],
    "snack":     [("Apple + Almond Butter",200,5,28,9),("Celery + Hummus",130,5,16,6),
                  ("Cottage Cheese (½ cup)",110,14,5,2),("Hard-Boiled Eggs (2)",155,12,1,10)],
}
_MG = {
    "breakfast": [("Scrambled Eggs + Whole-Grain Toast",480,32,42,16),("Protein Pancakes + Banana",520,38,58,10),
                  ("Greek Yogurt + Granola + Nuts",490,24,56,18),("Oatmeal + Protein Shake",550,40,62,12)],
    "lunch":     [("Grilled Chicken Rice Bowl",650,52,72,14),("Beef & Quinoa Salad",620,48,55,18),
                  ("Tuna Pasta with Olive Oil",600,44,66,14),("Salmon & Brown Rice",640,50,65,16)],
    "dinner":    [("Steak + Mashed Sweet Potato",700,55,60,20),("Chicken Breast + Rice + Veggies",680,58,68,14),
                  ("Pork Tenderloin + Quinoa",660,52,62,18),("Ground Turkey Pasta",720,50,78,16)],
    "snack":     [("Protein Shake + Banana",310,30,40,4),("Peanut Butter Rice Cakes",280,10,36,10),
                  ("Mixed Nuts + Cheese Slice",300,12,14,22),("Cottage Cheese + Pineapple",220,20,26,2)],
}
_MT = {
    "breakfast": [("Whole-Grain Cereal + Milk",380,14,60,10),("Avocado Toast + Poached Egg",410,18,42,18),
                  ("Smoothie Bowl",360,12,58,10),("French Toast + Fresh Fruit",420,16,62,12)],
    "lunch":     [("Mediterranean Wrap",500,28,52,18),("Chicken Caesar Salad",480,38,28,22),
                  ("Veggie Burrito Bowl",520,20,72,14),("Turkey & Avocado Sandwich",490,32,48,16)],
    "dinner":    [("Pasta Primavera with Chicken",580,36,68,14),("Salmon with Roasted Vegetables",540,44,40,20),
                  ("Chicken Tikka Masala + Rice",600,40,66,16),("Beef Tacos (2) + Salad",560,36,52,20)],
    "snack":     [("Trail Mix (¼ cup)",180,5,18,10),("Fruit & Yogurt Cup",160,8,28,2),
                  ("Whole-Grain Crackers + Cheese",200,10,22,8),("Dark Chocolate + Almonds",210,5,20,14)],
}
_LIBRARY = {"weight_loss": _WL, "muscle_gain": _MG, "maintenance": _MT}

_TIPS = {
    "weight_loss": [
        "Eat slowly — it takes ~20 minutes for satiety signals to reach your brain.",
        "Prioritise protein at every meal to preserve muscle while in a deficit.",
        "Drink a glass of water before each meal to reduce overall intake.",
        "Choose high-volume, low-calorie foods (vegetables, broth soups) to stay full.",
        "Avoid liquid calories: sodas, juices, and alcohol add up quickly.",
        "Aim for 7-9 hours of sleep; poor sleep raises hunger hormones.",
        "Prepare meals in advance to avoid impulsive high-calorie choices.",
    ],
    "muscle_gain": [
        "Distribute protein evenly across 4-5 meals for optimal muscle protein synthesis.",
        "Consume a protein + carb meal within 30-60 minutes after training.",
        "Don't skip carbohydrates — they fuel training and spare muscle protein.",
        "Track your surplus carefully; excessive fat gain slows progress.",
        "Stay hydrated: even mild dehydration reduces strength output.",
        "Prioritise compound lifts (squat, deadlift, bench, row) for maximum stimulus.",
        "Aim for progressive overload — add weight or reps each week.",
    ],
    "maintenance": [
        "Use the plate method: ½ vegetables, ¼ protein, ¼ whole grains.",
        "Weigh yourself weekly (same time, same conditions) to spot drifts early.",
        "Focus on food quality, not just calories — micronutrients matter.",
        "Allow flexible eating 10-20% of the time to maintain long-term adherence.",
        "Keep an eye on portion sizes even when eating nutritious foods.",
        "Regular moderate exercise supports appetite regulation.",
        "Stay mindful of stress eating — emotions often masquerade as hunger.",
    ],
}


class DietEngine:
    def __init__(self, profile: UserProfile):
        self.profile = profile
        self._lib = _LIBRARY.get(profile.health_goal, _MT)

    def generate_meal_plan(self) -> dict:
        meals = {slot: random.choice(opts) for slot, opts in self._lib.items()}
        totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fats_g": 0.0}
        for _, c, p, carb, f in meals.values():
            totals["calories"] += c; totals["protein_g"] += p
            totals["carbs_g"] += carb; totals["fats_g"] += f
        totals = {k: round(v, 1) for k, v in totals.items()}
        goal_notes = {
            "weight_loss": f"Targeting ~500 kcal deficit. Goal: {self.profile.daily_calorie_target:.0f} kcal (TDEE {self.profile.tdee:.0f} kcal). Consistent adherence = ~0.45 kg/week fat loss.",
            "muscle_gain": f"Lean bulk with ~300 kcal surplus. Goal: {self.profile.daily_calorie_target:.0f} kcal (TDEE {self.profile.tdee:.0f} kcal). Pair with progressive resistance training.",
            "maintenance": f"Maintain at {self.profile.daily_calorie_target:.0f} kcal/day (TDEE {self.profile.tdee:.0f} kcal). Focus on diet quality and consistent activity.",
        }
        return {
            "goal": self.profile.health_goal,
            "calorie_target": self.profile.daily_calorie_target,
            "macro_targets": self.profile.macro_targets,
            "meals": meals, "totals": totals,
            "tips": random.sample(_TIPS[self.profile.health_goal], k=4),
            "notes": goal_notes.get(self.profile.health_goal, ""),
        }

    def get_all_tips(self) -> list:
        return _TIPS.get(self.profile.health_goal, [])

    def evaluate_day(self, calories_consumed: float, water_ml: float) -> dict:
        ct, wt = self.profile.daily_calorie_target, self.profile.daily_water_target_ml
        cp = (calories_consumed / ct * 100) if ct else 0
        wp = (water_ml / wt * 100) if wt else 0
        def rate(p): return "On Track ✓" if 85 <= p <= 115 else ("Below Target" if p < 85 else "Above Target")
        return {
            "calorie_status": rate(cp), "water_status": rate(wp),
            "calorie_pct": round(cp, 1), "water_pct": round(wp, 1),
            "calories_remaining": max(0, round(ct - calories_consumed, 1)),
            "water_remaining_ml": max(0, round(wt - water_ml, 1)),
        }