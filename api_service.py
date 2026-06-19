import json, os, threading, urllib.request, urllib.parse, urllib.error
from typing import Callable

ROOT      = os.path.dirname(os.path.abspath(__file__))
KEYS_PATH = os.path.join(ROOT, "data", "api_keys.json")
_DEFAULT_KEYS = {"nutritionix_app_id": "", "nutritionix_app_key": "", "spoonacular_key": ""}


def load_keys() -> dict:
    os.makedirs(os.path.dirname(KEYS_PATH), exist_ok=True)
    if not os.path.exists(KEYS_PATH):
        save_keys(_DEFAULT_KEYS); return dict(_DEFAULT_KEYS)
    try:
        with open(KEYS_PATH) as f: return {**_DEFAULT_KEYS, **json.load(f)}
    except Exception:
        return dict(_DEFAULT_KEYS)


def save_keys(keys: dict) -> None:
    os.makedirs(os.path.dirname(KEYS_PATH), exist_ok=True)
    with open(KEYS_PATH, "w") as f: json.dump(keys, f, indent=2)


def _get(url: str, headers: dict = None, timeout: int = 8):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _async(fn: Callable, *args, callback: Callable, error_callback: Callable):
    def _run():
        try: callback(fn(*args))
        except Exception as e: error_callback(str(e))
    threading.Thread(target=_run, daemon=True).start()


# ── Open Food Facts ───────────────────────────────────────────────────────────

OFF_SEARCH = "https://world.openfoodfacts.org/cgi/search.pl"

def _parse_off(p: dict):
    n = p.get("nutriments", {})
    name = (p.get("product_name_en") or p.get("product_name") or "").strip()
    if not name: return None
    return {
        "source": "Open Food Facts", "food_name": name,
        "brand":     p.get("brands", "").split(",")[0].strip(),
        "calories":  round(float(n.get("energy-kcal_100g") or n.get("energy-kcal") or 0), 1),
        "protein_g": round(float(n.get("proteins_100g") or 0), 1),
        "carbs_g":   round(float(n.get("carbohydrates_100g") or 0), 1),
        "fats_g":    round(float(n.get("fat_100g") or 0), 1),
        "serving":   p.get("serving_size") or "100g",
    }

def search_open_food_facts(query: str, max_results: int = 20) -> list:
    params = urllib.parse.urlencode({
        "search_terms": query, "search_simple": 1, "action": "process",
        "json": 1, "page_size": max_results,
        "fields": "product_name,product_name_en,brands,nutriments,serving_size",
    })
    data = _get(f"{OFF_SEARCH}?{params}", headers={"User-Agent": "HealthTrackPro/1.0"})
    return [p for p in (_parse_off(x) for x in data.get("products", [])) if p and p["calories"] > 0][:max_results]

def search_open_food_facts_async(query, callback, error_callback, max_results=20):
    _async(search_open_food_facts, query, max_results, callback=callback, error_callback=error_callback)


# ── Nutritionix ───────────────────────────────────────────────────────────────

NX_SEARCH   = "https://trackapi.nutritionix.com/v2/search/instant"
NX_NUTRIENT = "https://trackapi.nutritionix.com/v2/nutrients"
NX_EXERCISE = "https://trackapi.nutritionix.com/v2/natural/exercise"

def _nx_headers() -> dict:
    k = load_keys()
    return {"x-app-id": k["nutritionix_app_id"], "x-app-key": k["nutritionix_app_key"],
            "Content-Type": "application/json"}

def _nx_item(item, brand="Common") -> dict:
    return {
        "source": "Nutritionix", "food_name": item.get("food_name","").title(),
        "brand":     item.get("brand_name", brand),
        "calories":  round(float(item.get("nf_calories") or 0), 1),
        "protein_g": round(float(item.get("nf_protein") or 0), 1),
        "carbs_g":   round(float(item.get("nf_total_carbohydrate") or 0), 1),
        "fats_g":    round(float(item.get("nf_total_fat") or 0), 1),
        "serving":   (f"{item.get('serving_qty','')} {item.get('serving_unit','')}".strip()) or "1 serving",
    }

def search_nutritionix(query: str, max_results: int = 20) -> list:
    keys = load_keys()
    if not keys["nutritionix_app_id"] or not keys["nutritionix_app_key"]:
        raise ValueError("Nutritionix API keys not configured.")
    params = urllib.parse.urlencode({"query": query, "branded": "true", "common": "true", "detailed": "true"})
    data = _get(f"{NX_SEARCH}?{params}", headers=_nx_headers())
    results = [_nx_item(i) for i in data.get("branded", [])[:max_results // 2]]
    common_names = [i["food_name"] for i in data.get("common", [])[:8]]
    if common_names:
        try:
            payload = json.dumps({"query": ", ".join(common_names)}).encode()
            req = urllib.request.Request(NX_NUTRIENT, data=payload, headers=_nx_headers(), method="POST")
            with urllib.request.urlopen(req, timeout=8) as r:
                for item in json.loads(r.read().decode()).get("foods", []):
                    results.append(_nx_item(item))
        except Exception:
            pass
    return [r for r in results if r["calories"] > 0][:max_results]

def search_nutritionix_async(query, callback, error_callback, max_results=20):
    _async(search_nutritionix, query, max_results, callback=callback, error_callback=error_callback)

def get_exercise_calories(query: str, weight_kg: float, age: int, gender: str) -> list:
    keys = load_keys()
    if not keys["nutritionix_app_id"] or not keys["nutritionix_app_key"]:
        raise ValueError("Nutritionix API keys not configured.")
    payload = json.dumps({"query": query, "weight_kg": weight_kg, "height_cm": 170,
                          "age": age, "gender": gender.lower()}).encode()
    req = urllib.request.Request(NX_EXERCISE, data=payload, headers=_nx_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
    return [{"name": ex.get("name","").title(),
             "duration_min": round(float(ex.get("duration_min") or 0), 1),
             "calories_burned": round(float(ex.get("nf_calories") or 0), 1),
             "met": ex.get("met","")}
            for ex in data.get("exercises", [])]

def get_exercise_calories_async(query, weight_kg, age, gender, callback, error_callback):
    _async(get_exercise_calories, query, weight_kg, age, gender, callback=callback, error_callback=error_callback)


# ── Spoonacular ───────────────────────────────────────────────────────────────

SP_SEARCH  = "https://api.spoonacular.com/food/ingredients/search"
SP_INFO    = "https://api.spoonacular.com/food/ingredients/{id}/information"
SP_RECIPES = "https://api.spoonacular.com/recipes/complexSearch"

def _sp_key() -> str:
    k = load_keys().get("spoonacular_key", "")
    if not k: raise ValueError("Spoonacular API key not configured.")
    return k

def search_spoonacular_ingredients(query: str, max_results: int = 20) -> list:
    api_key = _sp_key()
    params = urllib.parse.urlencode({"query": query, "number": min(max_results, 10),
                                     "apiKey": api_key, "metaInformation": "true"})
    items = _get(f"{SP_SEARCH}?{params}").get("results", [])
    results = []
    for item in items:
        try:
            info = _get(SP_INFO.format(id=item["id"]) + f"?amount=100&unit=grams&apiKey={api_key}")
            n = {x["name"]: x["amount"] for x in info.get("nutrition", {}).get("nutrients", [])}
            results.append({
                "source": "Spoonacular", "brand": "Ingredient", "serving": "100g",
                "food_name": info.get("name", item.get("name","")).title(),
                "calories":  round(float(n.get("Calories", 0)), 1),
                "protein_g": round(float(n.get("Protein", 0)), 1),
                "carbs_g":   round(float(n.get("Carbohydrates", 0)), 1),
                "fats_g":    round(float(n.get("Fat", 0)), 1),
            })
        except Exception: continue
    return [r for r in results if r["calories"] > 0]

def search_spoonacular_async(query, callback, error_callback, max_results=20):
    _async(search_spoonacular_ingredients, query, max_results, callback=callback, error_callback=error_callback)

def get_recipes_for_goal(goal: str, max_results: int = 6) -> list:
    api_key = _sp_key()
    sort_map = {"weight_loss": "calories", "muscle_gain": "protein", "maintenance": "popularity"}
    diet_map = {"weight_loss": "lowcalorie", "muscle_gain": "highprotein"}
    params = {"number": max_results, "addRecipeNutrition": "true", "instructionsRequired": "true",
              "sort": sort_map.get(goal, "popularity"), "apiKey": api_key}
    if goal in diet_map: params["diet"] = diet_map[goal]
    results = []
    for r in _get(f"{SP_RECIPES}?{urllib.parse.urlencode(params)}").get("results", []):
        n = {x["name"]: x["amount"] for x in (r.get("nutrition") or {}).get("nutrients", [])}
        results.append({
            "title": r.get("title",""), "ready_in_minutes": r.get("readyInMinutes","?"),
            "servings": r.get("servings", 1), "url": r.get("sourceUrl",""), "image": r.get("image",""),
            "calories":  round(float(n.get("Calories", 0)), 1),
            "protein_g": round(float(n.get("Protein", 0)), 1),
            "carbs_g":   round(float(n.get("Carbohydrates", 0)), 1),
            "fats_g":    round(float(n.get("Fat", 0)), 1),
        })
    return results

def get_recipes_async(goal, callback, error_callback, max_results=6):
    _async(get_recipes_for_goal, goal, max_results, callback=callback, error_callback=error_callback)


# ── Unified Search ────────────────────────────────────────────────────────────

def search_all_apis(query: str, callback: Callable, error_callback: Callable, max_per_source: int = 10):
    keys = load_keys()
    sources = ["openfoodfacts"]
    if keys["nutritionix_app_id"] and keys["nutritionix_app_key"]: sources.append("nutritionix")
    if keys["spoonacular_key"]: sources.append("spoonacular")

    lock = threading.Lock(); all_res = []; done = [0]; errors = []; total = len(sources)

    def _on_result(items):
        with lock:
            all_res.extend(items); done[0] += 1
            if done[0] == total:
                (callback(all_res) if all_res else error_callback("No results. " + " | ".join(errors)))

    def _on_error(msg):
        with lock:
            errors.append(msg); done[0] += 1
            if done[0] == total:
                (callback(all_res) if all_res else error_callback("No results. " + " | ".join(errors)))

    fns = {"openfoodfacts": search_open_food_facts_async,
           "nutritionix": search_nutritionix_async,
           "spoonacular": search_spoonacular_async}
    for src in sources:
        fns[src](query, _on_result, _on_error, max_per_source)
