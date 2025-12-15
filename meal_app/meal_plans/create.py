from flask import Blueprint, render_template, request, redirect, url_for, session
import json
from pathlib import Path
from ..utilities import execute_mysql_query
from ..variables import extras

# Blueprint for the "Create Meal Plan" feature
create = Blueprint('create', __name__, template_folder='templates', static_folder='../static')


def get_meal_info(meal_list, quantity_list) -> list[dict]:
    """
    Fetch ingredient JSON columns for each selected meal from the database.
    Also attach the quantity selected for that meal so we can scale ingredients later.
    """
    results = []
    q = """
      SELECT Fresh_Ingredients, Tinned_Ingredients, Dry_Ingredients, Dairy_Ingredients
      FROM MealsTable
      WHERE Name = :name
    """
    for idx, meal in enumerate(meal_list):
        # Fetch one row for this meal name
        row = execute_mysql_query(q, {"name": meal}, fetch="one")
        if not row:
            continue

        # Convert JSON text to a Python dict, and treat empty/null values as an empty dict
        def _loads(v):
            if v in (None, "", "null"):
                return {}
            return json.loads(v)

        # Store ingredient buckets plus the meal quantity for later scaling
        parsed = {
            "Fresh_Ingredients": _loads(row.get("Fresh_Ingredients")),
            "Tinned_Ingredients": _loads(row.get("Tinned_Ingredients")),
            "Dry_Ingredients": _loads(row.get("Dry_Ingredients")),
            "Dairy_Ingredients": _loads(row.get("Dairy_Ingredients")),
            "quantity": quantity_list[idx],
        }
        results.append(parsed)
    return results


def quantity_adjustment(meal_list_dict) -> list[dict]:
    """Multiply ingredient amounts by the quantity selected for each meal."""

    # Helper to multiply every numeric value in a dictionary by a factor
    # If a value cannot be converted to a number, that ingredient is removed
    def _scale(dct, factor):
        if not isinstance(dct, dict):
            return {}
        for k, v in list(dct.items()):
            try:
                dct[k] = float(v) * float(factor)
            except (TypeError, ValueError):
                dct.pop(k, None)
        return dct

    # Update each meal dict by scaling ingredient quantities and then removing the quantity field
    for meal in meal_list_dict:
        qty = meal.get("quantity", 1) or 1
        meal["Fresh_Ingredients"] = _scale(meal.get("Fresh_Ingredients", {}), qty)
        meal["Tinned_Ingredients"] = _scale(meal.get("Tinned_Ingredients", {}), qty)
        meal["Dry_Ingredients"] = _scale(meal.get("Dry_Ingredients", {}), qty)
        meal["Dairy_Ingredients"] = _scale(meal.get("Dairy_Ingredients", {}), qty)
        meal.pop("quantity", None)
    return meal_list_dict


def build_ingredient_dictionary(meal_ingredient_dict, complete_ingredient_dict, ingredient_type) -> dict:
    """
    Add one meal's ingredient bucket into the overall totals dictionary.
    If an ingredient appears multiple times across meals, its quantity is added together.
    """
    for ingredient, val in meal_ingredient_dict.items():
        # Skip any ingredient amounts that are not numeric
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue

        # Add the amount into the correct ingredient category bucket
        bucket = complete_ingredient_dict[ingredient_type]
        bucket[ingredient] = bucket.get(ingredient, 0) + val

        # Round to keep totals neat and readable
        bucket[ingredient] = round(bucket[ingredient], 2)

        # If the number is effectively an integer, store it as an int for cleaner display
        if float(bucket[ingredient]).is_integer():
            bucket[ingredient] = int(bucket[ingredient])
    return complete_ingredient_dict


def collate_ingredients(meal_info_list) -> dict:
    """Merge all meals' ingredient buckets into one combined shopping list dictionary."""
    complete_ingredient_dict = {
        "Fresh_Ingredients": {},
        "Tinned_Ingredients": {},
        "Dry_Ingredients": {},
        "Dairy_Ingredients": {},
    }

    # Combine ingredient totals across all meals
    for meal in meal_info_list:
        for ingredient_type in complete_ingredient_dict.keys():
            dct = meal.get(ingredient_type) or {}
            if dct:
                build_ingredient_dictionary(dct, complete_ingredient_dict, ingredient_type)

    return complete_ingredient_dict


@create.route('/create', methods=['GET', 'POST'])
def create_meal_plan():
    # Get meals grouped by staple from the database (useful for categorizing or headings)
    query_string = """
      SELECT GROUP_CONCAT(Name ORDER BY Name ASC) AS Meals, Staple
      FROM MealsTable
      GROUP BY Staple;
    """
    results = execute_mysql_query(query_string, fetch="all") or []

    # Convert the grouped results into a dictionary: {staple: [meal1, meal2, ...]}
    staples_dict = {}
    for item in results:
        staple = str(item.get('Staple') or '')
        meals_csv = item.get('Meals') or ''
        meals_list = [m for m in meals_csv.split(',') if m] if meals_csv else []
        staples_dict[staple] = meals_list

    # Build a flat list of all meals to populate every dropdown in the UI
    all_rows = execute_mysql_query("SELECT Name FROM MealsTable ORDER BY Name ASC;", fetch="all") or []
    all_meals = [r["Name"] for r in all_rows]

    # Try to load sample meal names from the sample JSON file (only used for display/helping users)
    sample_meals = []
    try:
        app_root = Path(__file__).resolve().parents[1]
        project_root = app_root.parent
        sample_path = project_root / "database_setup" / "sample_database_data.json"
        if sample_path.exists():
            data = json.loads(sample_path.read_text(encoding="utf-8"))
            sample_meals = sorted({str(item.get("Name", "")).strip() for item in data if item.get("Name")})
    except Exception:
        sample_meals = []

    if request.method == "POST":
        # Convert submitted form data into a normal Python dictionary
        details = request.form.to_dict()

        import re

        # Helper to sort keys like Meal 1, Meal 2, ... Meal 10 in correct numeric order
        def key_index(k: str) -> tuple:
            m = re.search(r'(\d+)', k)
            return (int(m.group(1)) if m else 10**9, k.lower())

        # Collect all selected meals from the submitted form
        meal_keys = sorted([k for k in details if 'meal' in k.lower()], key=key_index)
        meals_raw = [
            details[k].strip()
            for k in meal_keys
            if details[k] and details[k].strip().lower() not in ('null', '')
        ]

        # Collect quantities from the submitted form, defaulting to 1 if missing or invalid
        qty_keys = sorted([k for k in details if 'quantity' in k.lower()], key=key_index)
        qty_raw = []
        for k in qty_keys:
            v = details.get(k, '').strip()
            if not v:
                qty_raw.append(1)
                continue
            try:
                qty_raw.append(int(v))
            except ValueError:
                qty_raw.append(1)

        # Make sure each selected meal has a matching quantity
        meal_list = meals_raw
        if len(qty_raw) < len(meal_list):
            qty_raw += [1] * (len(meal_list) - len(qty_raw))
        quantity_list = qty_raw[:len(meal_list)]

        # If the user submits without selecting any meals, show the form again
        if not meal_list:
            return render_template('create.html',
                                   staples_dict=staples_dict,
                                   extras=extras,
                                   all_meals=all_meals,
                                   sample_meals=sample_meals)

        # Fetch ingredient info for each meal and adjust ingredient totals based on quantities
        meal_info = get_meal_info(meal_list, quantity_list)
        adjusted = quantity_adjustment(meal_info)

        # Build a per-meal breakdown so the UI can show shopping lists meal-by-meal if needed
        per_meal = []
        for idx, meal_name in enumerate(meal_list):
            meal_dict = adjusted[idx] if idx < len(adjusted) else {}
            per_meal.append({
                "Name": meal_name,
                "Fresh_Ingredients": meal_dict.get("Fresh_Ingredients", {}),
                "Tinned_Ingredients": meal_dict.get("Tinned_Ingredients", {}),
                "Dry_Ingredients": meal_dict.get("Dry_Ingredients", {}),
                "Dairy_Ingredients": meal_dict.get("Dairy_Ingredients", {}),
            })

        # Create the final combined ingredient shopping list across all selected meals
        complete_ingredient_dict = collate_ingredients(adjusted)

        # Collect any extra items the user selected (checkboxes)
        extras_selected = []
        for k, v in details.items():
            if 'extra' in k.lower() and v and v.strip().lower() != 'null':
                extras_selected.append(v.strip())

        # Store everything needed for the display page in one dictionary
        complete_ingredient_dict['Extra_Ingredients'] = extras_selected
        complete_ingredient_dict['Meal_List'] = meal_list
        complete_ingredient_dict['Per_Meal_Ingredients'] = per_meal

        # Save the meal plan result in the session so the next page can display it
        session['complete_ingredient_dict'] = complete_ingredient_dict
        return redirect(url_for('display.display_meal_plan'))

    # For GET requests, show the create meal plan page with dropdown data
    return render_template('create.html',
                           staples_dict=staples_dict,
                           extras=extras,
                           all_meals=all_meals,
                           sample_meals=sample_meals)
