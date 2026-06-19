from dataclasses import dataclass

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2, "lightly_active": 1.375,
    "moderately_active": 1.55, "very_active": 1.725, "extra_active": 1.9,
}
ACTIVITY_LABELS = {
    "sedentary": "Sedentary (little/no exercise)",
    "lightly_active": "Lightly Active (1-3 days/week)",
    "moderately_active": "Moderately Active (3-5 days/week)",
    "very_active": "Very Active (6-7 days/week)",
    "extra_active": "Extra Active (physical job + exercise)",
}
HEALTH_GOALS = ["weight_loss", "muscle_gain", "maintenance"]
HEALTH_GOAL_LABELS = {
    "weight_loss": "Weight Loss",
    "muscle_gain": "Muscle Gain",
    "maintenance": "Maintenance",
}


@dataclass
class UserProfile:
    id: int
    name: str
    age: int
    weight_kg: float
    height_cm: float
    gender: str
    activity_level: str
    health_goal: str

    @classmethod
    def from_db_row(cls, row) -> "UserProfile":
        return cls(id=row["id"], name=row["name"], age=row["age"],
                   weight_kg=row["weight_kg"], height_cm=row["height_cm"],
                   gender=row["gender"], activity_level=row["activity_level"],
                   health_goal=row["health_goal"])

    @property
    def bmi(self) -> float:
        return round(self.weight_kg / (self.height_cm / 100) ** 2, 1)

    @property
    def bmi_category(self) -> str:
        b = self.bmi
        if b < 18.5: return "Underweight"
        if b < 25.0: return "Normal weight"
        if b < 30.0: return "Overweight"
        return "Obese"

    @property
    def bmr(self) -> float:
        if self.gender.lower() == "female":
            return round(447.593 + 9.247*self.weight_kg + 3.098*self.height_cm - 4.330*self.age, 1)
        return round(88.362 + 13.397*self.weight_kg + 4.799*self.height_cm - 5.677*self.age, 1)

    @property
    def tdee(self) -> float:
        return round(self.bmr * ACTIVITY_MULTIPLIERS.get(self.activity_level, 1.2), 1)

    @property
    def daily_calorie_target(self) -> float:
        delta = {"weight_loss": -500, "muscle_gain": 300, "maintenance": 0}
        return max(1200, round(self.tdee + delta.get(self.health_goal, 0), 1))

    @property
    def daily_water_target_ml(self) -> float:
        return round(self.weight_kg * 35 / 50) * 50

    @property
    def macro_targets(self) -> dict:
        cal = self.daily_calorie_target
        ratios = {"weight_loss": (.40,.30,.30), "muscle_gain": (.35,.45,.20), "maintenance": (.30,.40,.30)}
        p, c, f = ratios.get(self.health_goal, (.30,.40,.30))
        return {"protein_g": round(cal*p/4,1), "carbs_g": round(cal*c/4,1), "fats_g": round(cal*f/9,1)}

    def summary(self) -> dict:
        s = self
        return {
            "name": s.name, "age": s.age, "weight_kg": s.weight_kg,
            "height_cm": s.height_cm, "gender": s.gender,
            "activity_level": ACTIVITY_LABELS.get(s.activity_level, s.activity_level),
            "health_goal": HEALTH_GOAL_LABELS.get(s.health_goal, s.health_goal),
            "bmi": s.bmi, "bmi_category": s.bmi_category,
            "bmr": s.bmr, "tdee": s.tdee,
            "daily_calorie_target": s.daily_calorie_target,
            "daily_water_target_ml": s.daily_water_target_ml,
            **s.macro_targets,
        }
